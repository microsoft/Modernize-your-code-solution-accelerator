"""This module loops through each file in a batch and processes it using the SQL agents.
It sets up a group chat for the agents, sends the source script to the chat, and processes
the responses from the agents. It also reports in real-time to the client using websockets
and updates the database with the results.
"""

import json
import logging

from api.status_updates import send_status_update

from common.models.api import (
    FileProcessUpdate,
    FileRecord,
    FileResult,
    LogType,
    ProcessStatus,
)
from common.services.batch_service import BatchService

from semantic_kernel.contents import AuthorRole, ChatMessageContent

from sql_agents.agents.fixer.response import FixerResponse
from sql_agents.agents.migrator.response import MigratorResponse
from sql_agents.agents.picker.response import PickerResponse
from sql_agents.agents.semantic_verifier.response import SemanticVerifierResponse
from sql_agents.agents.syntax_checker.response import SyntaxCheckerResponse
from sql_agents.helpers.agents_manager import SqlAgents
from sql_agents.helpers.comms_manager import CommsManager
from sql_agents.helpers.models import AgentType

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def convert_script(
    source_script,
    file: FileRecord,
    batch_service: BatchService,
    sql_agents: SqlAgents,
    # agent_config: AgentBaseConfig,
) -> str:
    """Use the team of agents to migrate a sql script."""
    logger.info("Migrating query: %s\n", source_script)

    # Setup the group chat for the agents
    comms_manager = CommsManager(
        sql_agents.idx_agents,
        max_retries=5,          # Retry up to 5 times for rate limits
        initial_delay=1.0,      # Start with 1 second delay
        backoff_factor=2.0,     # Double delay each retry
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
        await comms_manager.group_chat.add_chat_message(
            ChatMessageContent(role=AuthorRole.USER, content=source_script)
        )
        carry_response = None
        try:

            async for response in comms_manager.async_invoke():
                carry_response = response
                if response.role == AuthorRole.ASSISTANT.value:
                    # Our process can terminate with either of these as the last response
                    # before syntax check
                    match response.name:
                        case AgentType.MIGRATOR.value:
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
                        case AgentType.SYNTAX_CHECKER.value:
                            result = SyntaxCheckerResponse.model_validate_json(
                                response.content.lower() or ""
                            )
                            # If there are no syntax errors, we can move to the semantic verifier
                            # We provide both scripts by injecting them into the chat history
                            if result.syntax_errors == []:
                                comms_manager.group_chat.history.add_message(
                                    ChatMessageContent(
                                        role=AuthorRole.USER,
                                        name="candidate",
                                        content=(
                                            f"source_script: {source_script}, \n "
                                            + f"migrated_script: {current_migration}"
                                        ),
                                    )
                                )
                        case AgentType.PICKER.value:
                            result = PickerResponse.model_validate_json(
                                response.content or ""
                            )
                            current_migration = result.picked_query
                        case AgentType.FIXER.value:
                            result = FixerResponse.model_validate_json(
                                response.content or ""
                            )
                            current_migration = result.fixed_query
                        case AgentType.SEMANTIC_VERIFIER.value:
                            logger.info(
                                "Semantic verifier agent response: %s", response.content
                            )
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
                try:
                    parsed_content = json.loads(response.content or "{}")
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from agent: %s", response.content)
                    parsed_content = {
                        "input_summary": "",
                        "candidates": [],
                        "summary": "",
                        "input_error": "",
                        "rai_error": "Invalid JSON from agent.",
                    }

                # Send status update using safe fallback values
                send_status_update(
                    status=FileProcessUpdate(
                        file.batch_id,
                        file.file_id,
                        ProcessStatus.IN_PROGRESS,
                        AgentType(response.name),
                        parsed_content.get("summary", ""),
                        FileResult.INFO,
                    ),
                )
                # end
                await batch_service.create_file_log(
                    str(file.file_id),
                    description,
                    current_migration,
                    LogType.INFO,
                    AgentType(response.name),
                    AuthorRole(response.role),
                )
        except Exception as e:
            logger.error("Error during comms_manager.async_invoke(): %s", str(e))
            # Log the error to the batch service for tracking
            await batch_service.create_file_log(
                str(file.file_id),
                f"Critical error during agent communication: {str(e)}",
                current_migration,
                LogType.ERROR,
                AgentType.ALL,
                AuthorRole.ASSISTANT,
            )
            # Send error status update
            send_status_update(
                status=FileProcessUpdate(
                    file.batch_id,
                    file.file_id,
                    ProcessStatus.COMPLETED,
                    AgentType.ALL,
                    f"Processing failed: {str(e)}",
                    FileResult.ERROR,
                ),
            )
            break

        if comms_manager.group_chat.is_complete:
            is_complete = True

        break

    migrated_query = current_migration

    is_valid = await validate_migration(
        migrated_query, carry_response, file, batch_service
    )

    if not is_valid:
        logger.info("# Migration failed.")

        return ""

    logger.info("# Migration complete.")
    logger.info("Final query: %s\n", migrated_query)
    logger.info(
        "Analysis of source and migrated queries:\n%s", "semantic verifier response"
    )

    return migrated_query


async def validate_migration(
    migrated_query: str,
    carry_response: ChatMessageContent,
    file: FileRecord,
    batch_service: BatchService,
) -> bool:
    """Make sure the migrated query was returned"""
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
        return False

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

    return True
