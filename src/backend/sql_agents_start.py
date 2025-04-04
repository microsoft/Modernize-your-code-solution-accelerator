﻿"""
This script demonstrates how to use the backend agents to migrate a query from one SQL dialect to another.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from api.status_updates import close_connection, send_status_update
from common.models.api import (
    AgentType,
    FileProcessUpdate,
    FileRecord,
    FileResult,
    LogType,
    ProcessStatus,
)
from common.services.batch_service import BatchService
from common.storage.blob_factory import BlobStorageFactory
from fastapi import HTTPException
from sql_agents.helpers.selection_function import setup_selection_function
from sql_agents.helpers.termination_function import setup_termination_function
from sql_agents.helpers.utils import is_text
from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.strategies import (
    KernelFunctionSelectionStrategy,
    KernelFunctionTerminationStrategy,
)
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatHistoryTruncationReducer,
    ChatMessageContent,
)
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException
from sql_agents import (
    create_kernel_with_chat_completion,
    setup_fixer_agent,
    setup_migrator_agent,
    setup_picker_agent,
    setup_semantic_verifier_agent,
    setup_syntax_checker_agent,
)
from sql_agents.agent_config import AgentModelDeployment, create_config
from sql_agents.fixer.response import FixerResponse
from sql_agents.migrator.response import MigratorResponse
from sql_agents.picker.response import PickerResponse
from sql_agents.semantic_verifier.response import SemanticVerifierResponse

# Loop through files from Cosmos DB.

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create a console handler and set the level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create a formatter and set it for the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)

# DEPLOYMENT_NAME = os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]

# configure agents
agent_dialect_config = create_config(sql_dialect_in="informix", sql_dialect_out="tsql")

# label agents
SELECTION_FUNCTION_NAME = "selection"
TERMINATION_FUNCTION_NAME = "termination"
TERMINATION_KEYWORD = "yes"


def extract_query(content):
    """Extract the query from a chat that contains the following template:
    # "migrated_query": 'SELECT TOP 10 * FROM mytable'"""
    if "migrated_query" in content:
        sub_str = content.split("migrated_query")[1]
        return sub_str.split(":")[1].strip().strip('"')


async def configure_agents():
    try:
        agent_fixer = setup_fixer_agent(
            AgentType.FIXER,
            agent_dialect_config,
            AgentModelDeployment.FIXER_AGENT_MODEL_DEPLOY,
        )
        agent_migrator = setup_migrator_agent(
            AgentType.MIGRATOR,
            agent_dialect_config,
            AgentModelDeployment.MIGRATOR_AGENT_MODEL_DEPLOY,
        )
        agent_picker = setup_picker_agent(
            AgentType.PICKER,
            agent_dialect_config,
            AgentModelDeployment.PICKER_AGENT_MODEL_DEPLOY,
        )
        agent_syntax_checker = setup_syntax_checker_agent(
            AgentType.SYNTAX_CHECKER,
            agent_dialect_config,
            AgentModelDeployment.SYNTAX_CHECKER_AGENT_MODEL_DEPLOY,
        )
        selection_function = setup_selection_function(
            SELECTION_FUNCTION_NAME,
            AgentType.MIGRATOR,
            AgentType.PICKER,
            AgentType.SYNTAX_CHECKER,
            AgentType.FIXER,
        )
        termination_function = setup_termination_function(
            TERMINATION_FUNCTION_NAME, TERMINATION_KEYWORD
        )
        return {
            "agents": {
                AgentType.MIGRATOR.value: agent_migrator,
                AgentType.PICKER.value: agent_picker,
                AgentType.SYNTAX_CHECKER.value: agent_syntax_checker,
                AgentType.FIXER.value: agent_fixer,
            },
            "selection_function": selection_function,
            "termination_function": termination_function,
        }

    except ValueError as exc:
        logger.error("Error setting up agents.")
        raise exc


async def convert(
    source_script, file: FileRecord, batch_service: BatchService, agent_config
) -> str:
    """setup agents, selection and termination."""
    logger.info("Migrating query: %s\n", source_script)

    history_reducer = ChatHistoryTruncationReducer(
        target_count=2
    )  # keep only the last two messages

    # setup the chat
    chat = AgentGroupChat(
        agent_config["agents"].values(),
        selection_strategy=KernelFunctionSelectionStrategy(
            function=agent_config["selection_function"],
            kernel=create_kernel_with_chat_completion(
                AgentType.SELECTION.value,
                AgentModelDeployment.SELECTION_MODEL_DEPLOY.value,
            ),
            result_parser=lambda result: (
                str(result.value[0]) if result.value is not None else AgentType.MIGRATOR
            ),
            agent_variable_name="agents",
            history_variable_name="history",
            history_reducer=history_reducer,
        ),
        termination_strategy=KernelFunctionTerminationStrategy(
            agents=[agent_config["agents"][AgentType.SYNTAX_CHECKER.value]],
            function=agent_config["termination_function"],
            kernel=create_kernel_with_chat_completion(
                AgentType.TERMINATION.value,
                AgentModelDeployment.TERMINATION_MODEL_DEPLOY.value,
            ),
            result_parser=lambda result: TERMINATION_KEYWORD
            in str(result.value[0]).lower(),
            history_variable_name="history",
            maximum_iterations=10,
            history_reducer=history_reducer,
        ),
    )

    # send websocket notification that file processing has started
    send_status_update(
        status=FileProcessUpdate(
            file.batch_id,
            file.file_id,
            ProcessStatus.IN_PROGRESS,
            AgentType.ALL,
            "File processing started",
            file_result=FileResult.INFO,
        ),
    )

    # orchestrate the chat
    current_migration = "No migration"
    is_complete: bool = False
    while not is_complete:
        await chat.add_chat_message(
            ChatMessageContent(role=AuthorRole.USER, content=source_script)
        )
        carry_response = None
        async for response in chat.invoke():
            carry_response = response
            if response.role == AuthorRole.ASSISTANT.value:
                # Our process can terminate with either of these as the last response before syntax check
                if response.name == AgentType.MIGRATOR.value:
                    result = MigratorResponse.model_validate_json(
                        response.content or ""
                    )
                    if result.input_error or result.rai_error:
                        # If there is an error in input, we end the processing here.
                        # We do not include this in termination to avoid forking the chat process.
                        description = {
                            "role": response.role,
                            "name": response.name or "*",
                            "content": response.content,
                        }
                        await batch_service.create_file_log(
                            str(file.file_id),
                            description,
                            current_migration,
                            LogType.ERROR,
                            AgentType(response.name),
                            AuthorRole(response.role),
                        )
                        current_migration = None
                        break
                if response.name == AgentType.PICKER.value:
                    result = PickerResponse.model_validate_json(response.content or "")
                    current_migration = result.picked_query
                elif response.name == AgentType.FIXER.value:
                    result = FixerResponse.model_validate_json(response.content or "")
                    current_migration = result.fixed_query

            description = {
                "role": response.role,
                "name": response.name or "*",
                "content": response.content,
            }

            logger.info(description)

            # send status update to the client of type in progress with agent status
            send_status_update(
                status=FileProcessUpdate(
                    file.batch_id,
                    file.file_id,
                    ProcessStatus.IN_PROGRESS,
                    AgentType(response.name),
                    json.loads(response.content)["summary"],
                    FileResult.INFO,
                ),
            )

            await batch_service.create_file_log(
                str(file.file_id),
                description,
                current_migration,
                LogType.INFO,
                AgentType(response.name),
                AuthorRole(response.role),
            )

        if chat.is_complete:
            is_complete = True

        break

    migrated_query = current_migration

    # Make sure the migrated query was returned
    if not migrated_query:
        # send status update to the client of type failed
        send_status_update(
            status=FileProcessUpdate(
                file.batch_id,
                file.file_id,
                ProcessStatus.COMPLETED,
                file_result=FileResult.ERROR,
            ),
        )
        await batch_service.create_file_log(
            str(file.file_id),
            "No migrated query returned. Migration failed.",
            "",
            LogType.ERROR,
            (
                AgentType.SEMANTIC_VERIFIER
                if carry_response is None
                else AgentType(carry_response.name)
            ),
            (
                AuthorRole.ASSISTANT
                if carry_response is None
                else AuthorRole(carry_response.role)
            ),
        )

        logger.error("No migrated query returned. Migration failed.")
        # Add needed error or log data to the file record here
        # skip the semantic verification
        return migrated_query

    # Invoke the semantic verifier agent to validate the migrated query
    semver_response = await invoke_semantic_verifier(
        source_script, migrated_query, file, batch_service
    )
    semver_response = SemanticVerifierResponse.model_validate_json(
        semver_response or ""
    )

    # Fake a problematic response for testing
    # semver_response = SemanticVerifierResponse(
    #     analysis="",
    #     judgement="",
    #     differences=[
    #         "The migrated query may have different outcomes in the following cases: ",
    #         "1. The source query runs as part of a data pipeline.",
    #     ],
    #     summary="",
    # )

    # If the semantic verifier agent returns a difference, we need to fix it
    if len(semver_response.differences) > 0:
        # If the semantic verifier agent returns a difference, we need to fix it
        description = {
            "role": AuthorRole.ASSISTANT.value,
            "name": AgentType.SEMANTIC_VERIFIER.value,
            "content": "\n".join(semver_response.differences),
        }
        logger.info("Semantic verification had issues. Pass with warnings.")
        # send status update to the client of type in progress with agent status
        send_status_update(
            status=FileProcessUpdate(
                file.batch_id,
                file.file_id,
                ProcessStatus.COMPLETED,
                AgentType.SEMANTIC_VERIFIER,
                semver_response.summary,
                FileResult.WARNING,
            ),
        )
        await batch_service.create_file_log(
            str(file.file_id),
            description,
            migrated_query,
            LogType.WARNING,
            AgentType.SEMANTIC_VERIFIER,
            AuthorRole.ASSISTANT,
        )

    elif semver_response == "":
        # If the semantic verifier agent returns an empty response
        logger.info("Semantic verification had no return value. Pass with warnings.")
        # send status update to the client of type in progress with agent status
        send_status_update(
            status=FileProcessUpdate(
                file.batch_id,
                file.file_id,
                ProcessStatus.COMPLETED,
                AgentType.SEMANTIC_VERIFIER,
                "No return value from semantic verifier agent.",
                FileResult.WARNING,
            ),
        )
        await batch_service.create_file_log(
            str(file.file_id),
            "No return value from semantic verifier agent.",
            migrated_query,
            LogType.WARNING,
            AgentType.SEMANTIC_VERIFIER,
            AuthorRole.ASSISTANT,
        )
    else:
        # send status update to the client of type completed / success
        send_status_update(
            status=FileProcessUpdate(
                file.batch_id,
                file.file_id,
                ProcessStatus.COMPLETED,
                AgentType.SEMANTIC_VERIFIER,
                semver_response.summary,
                file_result=FileResult.SUCCESS,
            ),
        )
        await batch_service.create_file_log(
            str(file.file_id),
            semver_response.summary,
            migrated_query,
            LogType.SUCCESS,
            AgentType.SEMANTIC_VERIFIER,
            AuthorRole.ASSISTANT,
        )

    logger.info("# Migration complete.")
    logger.info("Final query: %s\n", current_migration)
    logger.info("Analysis of source and migrated queries:\n%s", semver_response)

    return current_migration


async def invoke_semantic_verifier(
    source_script, migrated_query, file: FileRecord, batch_service: BatchService
):
    """Invoke the semantic verifier agent to validate the migrated query."""
    try:
        chat_history = ChatHistory()

        # Add user message to chat history
        user_message = (
            "Provide me with the semantic verification of the source and migrated queries. "
            "Remember to adhere to the specified JSON format for your response."
        )
        chat_history.add_message(
            ChatMessageContent(role=AuthorRole.USER, content=user_message)
        )

        agent_semantic_verifier = setup_semantic_verifier_agent(
            AgentType.SEMANTIC_VERIFIER,
            agent_dialect_config,
            AgentModelDeployment.SEMANTIC_VERIFIER_AGENT_MODEL_DEPLOY,
            source_script,
            migrated_query,
        )

        # Invoke the agent and process the response
        async for response in agent_semantic_verifier.invoke(chat_history):
            return response.content

    # Handle this as an exception from the Sematic Verifier is a warning
    except Exception as exc:
        logger.error(
            "Error setting up semantic verifier agent. Skipping semantic verification."
        )
        logger.error(exc)
        return None


async def process_batch_async(batch_id: str):
    """Run main script with dummy Cosmos data"""
    logger.info("Processing batch: %s", batch_id)
    storage = await BlobStorageFactory.get_storage()
    batch_service = BatchService()
    await batch_service.initialize_database()

    batch_files = await batch_service.database.get_batch_files(batch_id)

    if not batch_files:
        raise HTTPException(status_code=404, detail="Batch not found")
    else:
        # Retrieve list of file paths
        try:
            await batch_service.update_batch(batch_id, ProcessStatus.IN_PROGRESS)
        except Exception as exc:
            logger.error("Error updating batch status.{}".format(exc))
            # raise exc

        # setup agents once per batch
        agent_config = await configure_agents()

        # Walk through each file name and retrieve it from blob storage
        for file in batch_files:
            # Get the file from blob storage
            try:
                file_record = FileRecord.fromdb(file)
                # Update the file status
                try:
                    file_record.status = ProcessStatus.IN_PROGRESS
                    await batch_service.update_file_record(file_record)
                except Exception as exc:
                    logger.error("Error updating file status.{}".format(exc))

                sql_in_file = await storage.get_file(file_record.blob_path)

                # Check if the file is a valid text file
                if not is_text(sql_in_file):
                    logger.error("File is not a valid text file. Skipping.")
                    # insert data base write to file record stating invalid file
                    await batch_service.create_file_log(
                        str(file_record.file_id),
                        "File is not a valid text file. Skipping.",
                        "",
                        LogType.ERROR,
                        AgentType.ALL,
                        AuthorRole.ASSISTANT,
                    )
                    # send status update to the client of type failed
                    send_status_update(
                        status=FileProcessUpdate(
                            file_record.batch_id,
                            file_record.file_id,
                            ProcessStatus.COMPLETED,
                            file_result=FileResult.ERROR,
                        ),
                    )
                    file_record.file_result = FileResult.ERROR
                    file_record.status = ProcessStatus.COMPLETED
                    file_record.error_count = 1
                    await batch_service.update_file_record(file_record)
                    continue
                else:
                    logger.info("sql_in_file: %s", sql_in_file)

                # Convert the file
                converted_query = await convert(
                    sql_in_file, file_record, batch_service, agent_config
                )
                if converted_query:
                    # Add RAI disclaimer to the converted query
                    converted_query = (
                        "/*\n"
                        "-- AI-generated content may be incorrect\n"
                        "*/\n" + converted_query
                    )
                    await batch_service.create_candidate(
                        file["file_id"], converted_query
                    )
                else:
                    await batch_service.update_file_counts(file["file_id"])
            except UnicodeDecodeError as ucde:
                logger.error("Error decoding file: %s", file)
                logger.error("Error decoding file.{}".format(ucde))
                await process_error(ucde, file_record, batch_service)
            except ServiceResponseException as sre:
                logger.error(file)
                logger.error("Error processing file.{}".format(sre))
                # insert data base write to file record stating invalid file
                await process_error(sre, file_record, batch_service)
            except Exception as exc:
                logger.error(file)
                logger.error("Error processing file.{}".format(exc))
                # insert data base write to file record stating invalid file
                await process_error(exc, file_record, batch_service)

        try:
            await batch_service.batch_files_final_update(batch_id)
        except Exception as exc:
            logger.error("Error updating files status.{}".format(exc))
        try:
            await batch_service.update_batch(batch_id, ProcessStatus.COMPLETED)
        except Exception as exc:
            await batch_service.update_batch(batch_id, ProcessStatus.FAILED)
            logger.error("Error updating batch status.{}".format(exc))
        logger.info("Batch processing complete.")


async def process_error(
    ex: Exception, file_record: FileRecord, batch_service: BatchService
):
    """insert data base write to file record stating invalid file and send ws notification"""
    await batch_service.create_file_log(
        str(file_record.file_id),
        "Error processing file {}".format(ex),
        "",
        LogType.ERROR,
        AgentType.ALL,
        AuthorRole.ASSISTANT,
    )
    # send status update to the client of type failed
    send_status_update(
        status=FileProcessUpdate(
            file_record.batch_id,
            file_record.file_id,
            ProcessStatus.COMPLETED,
            file_result=FileResult.ERROR,
        ),
    )
