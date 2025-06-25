"""
This script demonstrates how to use the backend agents to migrate
a query from one SQL dialect to another.
It is the main entry point for the SQL migration process.
"""

import logging

from api.status_updates import send_status_update

from azure.identity.aio import DefaultAzureCredential

from common.config.config import app_config
from common.models.api import (
    FileProcessUpdate,
    FileRecord,
    FileResult,
    LogType,
    ProcessStatus,
)
from common.services.batch_service import BatchService
from common.storage.blob_factory import BlobStorageFactory

from fastapi import HTTPException


from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent  # pylint: disable=E0611
from semantic_kernel.contents import AuthorRole
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException

from sql_agents.agents.agent_config import AgentBaseConfig
from sql_agents.convert_script import convert_script
from sql_agents.helpers.agents_manager import SqlAgents
from sql_agents.helpers.models import AgentType
from sql_agents.helpers.utils import is_text

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Walk through batch structure processing each file
async def process_batch_async(
    batch_id: str, convert_from: str = "informix", convert_to: str = "tsql"
):
    """Central batch processing function to process each file in the batch"""
    logger.info("Processing batch: %s", batch_id)
    storage = await BlobStorageFactory.get_storage()
    batch_service = BatchService()
    await batch_service.initialize_database()

    try:
        batch_files = await batch_service.database.get_batch_files(batch_id)
        if not batch_files:
            raise HTTPException(status_code=404, detail="Batch not found")
        # Retrieve list of file paths
        await batch_service.update_batch(batch_id, ProcessStatus.IN_PROGRESS)
    except Exception as exc:
        logger.error("Error updating batch status. %s", exc)

    # Add client and auto cleanup
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds, endpoint=app_config.ai_project_endpoint) as client,
    ):

        # setup all agent settings and agents per batch
        agent_config = AgentBaseConfig(
            project_client=client, sql_from=convert_from, sql_to=convert_to
        )
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
                    logger.error("Error updating file status. %s", exc)

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

                # Convert the file
                converted_query = await convert_script(
                    sql_in_file,
                    file_record,
                    batch_service,
                    sql_agents,
                )
                if converted_query:
                    # Add RAI disclaimer to the converted query
                    converted_query = add_rai_disclaimer(converted_query)
                    await batch_service.create_candidate(
                        file["file_id"], converted_query
                    )
                else:
                    await batch_service.update_file_counts(file["file_id"])
                # TEMPORARY: awaiting bug fix for rate limits
                #await asyncio.sleep(5)
            except UnicodeDecodeError as ucde:
                logger.error("Error decoding file: %s", file)
                logger.error("Error decoding file. %s", ucde)
                await process_error(ucde, file_record, batch_service)
            except ServiceResponseException as sre:
                logger.error(file)
                logger.error("Error processing file. %s", sre)
                # insert data base write to file record stating invalid file
                await process_error(sre, file_record, batch_service)
            except Exception as exc:
                logger.error(file)
                logger.error("Error processing file. %s", exc)
                # insert data base write to file record stating invalid file
                await process_error(exc, file_record, batch_service)

        # Cleanup the agents
        await sql_agents.delete_agents()

        try:
            await batch_service.batch_files_final_update(batch_id)
            await batch_service.update_batch(batch_id, ProcessStatus.COMPLETED)
        except Exception as exc:
            await batch_service.update_batch(batch_id, ProcessStatus.FAILED)
            logger.error("Error updating batch status. %s", exc)
        logger.info("Batch processing complete.")


async def process_error(
    ex: Exception, file_record: FileRecord, batch_service: BatchService
):
    """Insert data base write to file record stating invalid file and send ws notification"""
    await batch_service.create_file_log(
        file_id=str(file_record.file_id),
        description=f"Error processing file {ex}",
        last_candidate="",
        log_type=LogType.ERROR,
        agent_type=AgentType.ALL,
        author_role=AuthorRole.ASSISTANT,
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


def add_rai_disclaimer(converted_query: str) -> str:
    """Add RAI disclaimer to the converted query."""
    rai_disclaimer = "/*\n -- AI-generated content may be incorrect\n */\n"
    return rai_disclaimer + converted_query
