"""
This script demonstrates how to use the backend agents to migrate a query from one SQL dialect to another.
"""

import json
import logging

from azure.identity.aio import DefaultAzureCredential
from fastapi import HTTPException
from semantic_kernel.agents import AzureAIAgent  # pylint: disable=E0611
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException

from api.status_updates import send_status_update
from common.models.api import (
    FileProcessUpdate,
    FileRecord,
    FileResult,
    LogType,
    ProcessStatus,
)
from common.services.batch_service import BatchService
from common.storage.blob_factory import BlobStorageFactory
from sql_agents.agent_config import AgentBaseConfig
from sql_agents.fixer.response import FixerResponse
from sql_agents.helpers.agents_manager import SqlAgents
from sql_agents.helpers.comms_manager import CommsManager
from sql_agents.helpers.models import AgentType
from sql_agents.helpers.utils import is_text
from sql_agents.migrator.response import MigratorResponse
from sql_agents.picker.response import PickerResponse
from sql_agents.semantic_verifier.response import SemanticVerifierResponse
from sql_agents.syntax_checker.response import SyntaxCheckerResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def convert_script(
    source_script,
    file: FileRecord,
    batch_service: BatchService,
    sql_agents: SqlAgents,
    # agent_config: AgentBaseConfig,
) -> str:
    """setup agents, selection and termination."""
    logger.info("Migrating query: %s\n", source_script)

    # Setup the group chat for the agents
    chat = CommsManager(sql_agents.idx_agents).group_chat

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
                elif response.name == AgentType.SYNTAX_CHECKER.value:
                    result = SyntaxCheckerResponse.model_validate_json(
                        response.content.lower() or ""
                    )
                    # If there are no syntax errors, we can move to the semantic verifier
                    if result.syntax_errors == []:
                        chat.history.add_message(
                            ChatMessageContent(
                                role=AuthorRole.USER,
                                name="candidate",
                                content=(
                                    f"source_script: {source_script}, \n migrated_script: {current_migration}"
                                ),
                            )
                        )
                elif response.name == AgentType.PICKER.value:
                    result = PickerResponse.model_validate_json(response.content or "")
                    current_migration = result.picked_query
                elif response.name == AgentType.FIXER.value:
                    result = FixerResponse.model_validate_json(response.content or "")
                    current_migration = result.fixed_query
                elif response.name == AgentType.SEMANTIC_VERIFIER.value:
                    result = SemanticVerifierResponse.model_validate_json(
                        response.content or ""
                    )
                    # If the semantic verifier agent returns a difference, we need to report it
                    if len(result.differences) > 0:
                        description = {
                            "role": AuthorRole.ASSISTANT.value,
                            "name": AgentType.SEMANTIC_VERIFIER.value,
                            "content": "\n".join(result.differences),
                        }
                        logger.info(
                            "Semantic verification had issues. Pass with warnings."
                        )
                        # send status update to the client of type in progress with agent status
                        send_status_update(
                            status=FileProcessUpdate(
                                file.batch_id,
                                file.file_id,
                                ProcessStatus.COMPLETED,
                                AgentType.SEMANTIC_VERIFIER,
                                result.summary,
                                FileResult.WARNING,
                            ),
                        )
                        await batch_service.create_file_log(
                            str(file.file_id),
                            description,
                            current_migration,
                            LogType.WARNING,
                            AgentType.SEMANTIC_VERIFIER,
                            AuthorRole.ASSISTANT,
                        )

                    elif response == "":
                        # If the semantic verifier agent returns an empty response
                        logger.info(
                            "Semantic verification had no return value. Pass with warnings."
                        )
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
                            current_migration,
                            LogType.WARNING,
                            AgentType.SEMANTIC_VERIFIER,
                            AuthorRole.ASSISTANT,
                        )

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
        return ""
    else:
        # send status update to the client of type completed / success
        send_status_update(
            status=FileProcessUpdate(
                batch_id=file.batch_id,
                file_id=file.file_id,
                process_status=ProcessStatus.COMPLETED,
                agent_type=AgentType.ALL,
                file_result=FileResult.SUCCESS,
            ),
        )
        await batch_service.create_file_log(
            file_id=str(file.file_id),
            description="Migration completed successfully.",
            last_candidate=migrated_query,
            log_type=LogType.SUCCESS,
            agent_type=AgentType.ALL,
            author_role=AuthorRole.ASSISTANT,
        )

    logger.info("# Migration complete.")
    logger.info("Final query: %s\n", migrated_query)
    logger.info(
        "Analysis of source and migrated queries:\n%s", "semantic verifier response"
    )

    return migrated_query


# Walk through batch structure processing each file
async def process_batch_async(
    batch_id: str, convert_from: str = "informix", convert_to: str = "tsql"
):
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

        # Add client and auto cleanup
        async with (
            DefaultAzureCredential() as creds,
            AzureAIAgent.create_client(credential=creds) as client,
        ):

            # setup all agent settings and agents per batch
            agent_config = AgentBaseConfig(
                project_client=client, sql_from=convert_from, sql_to=convert_to
            )

            # setup the agents
            sql_agents = await SqlAgents.create(agent_config)

            # Walk through each file name and retrieve it from blob storage
            # Send file to the agents for processing
            # Send status update to the client of type in progress, completed, or failed
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

                    # split into base validation routine
                    # Check if the file is a valid text file <--
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
                    # -->

                    # Convert the file
                    converted_query = await convert_script(
                        sql_in_file,
                        file_record,
                        batch_service,
                        sql_agents,
                        # agent_config,
                    )
                    if converted_query:
                        # Add RAI disclaimer to the converted query - split this into a function
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

            # Cleanup the agents
            await sql_agents.delete_agents()

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
