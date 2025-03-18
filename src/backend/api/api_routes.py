"""FastAPI API routes for file processing and conversion"""

import asyncio
import io
import zipfile
from typing import Dict

from api.auth.auth_utils import get_authenticated_user
from api.status_updates import app_connection_manager, close_connection
from azure.storage.blob import BlobServiceClient
from common.logger.app_logger import AppLogger
from common.services.batch_service import BatchService
from common.services.queue_service import QueueService
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import Response, StreamingResponse
from sql_agents.syntax_checker.plug_ins import SyntaxCheckerPlugin

router = APIRouter()
logger = AppLogger("APIRoutes")

# Temp while waiting for queue implementation
from sql_agents_start import process_batch_async


@router.post("/start-processing")
async def start_processing(request: Request):
    """
    Start processing files for a given batch
    ---
    tags:
    - File Processing
    parameters:
    - in: body
      name: processing_config
      schema:
        type: object
        properties:
          batch_id:
            type: string
            format: uuid
          translate_from:
            type: string
          translate_to:
            type: string
    responses:
      200:
        description: Processing initiated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
      400:
        description: Invalid processing request
      500:
        description: Internal server error
    """
    try:
        payload = await request.json()
        batch_id = payload.get("batch_id")

        await process_batch_async(batch_id)

        await close_connection(batch_id)

        return {
            "batch_id": batch_id,
            "status": "Processing completed",
            "message": "Files processed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/download/{upload_id}",
    summary="Download files as ZIP",
    description="Download all files associated with an upload ID as a ZIP archive",
    response_description="ZIP file containing all processed files",
)
async def download_files(batch_id: str):
    """
    Download files as ZIP

    ---
    tags:
      - File Download
    consumes:
      - application/json
    parameters:
      - in: path
        name: upload_id
        required: true
        description: The ID of the upload to download files for
        schema:
          type: string
    responses:
      200:
        description: ZIP file containing all processed files
        schema:
          type: string
          format: binary
      404:
        description: Batch not found or error creating ZIP file
        schema:
          type: object
          properties:
            detail:
              type: string
              example: Batch not found
    """

    # call batch_service get_batch_for_zip to get all files for batch_id
    batch_service = BatchService()
    await batch_service.initialize_database()

    file_data = await batch_service.get_batch_for_zip(batch_id)
    if not file_data:
        raise HTTPException(status_code=404, detail="Batch not found") from e

    # Create an in-memory bytes buffer for the zip file
    zip_stream = io.BytesIO()
    try:
        # Create a new zip file in memory
        with zipfile.ZipFile(
            zip_stream, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zf:
            for file_name, content in file_data:
                # Make sure the file has content
                if not content:
                    continue
                # Ensure the file name ends with '.sql'
                if not file_name.endswith(".sql"):
                    file_name += ".sql"
                # Ensure the file name is safe for zip
                file_name = file_name.replace("/", "_").replace("\\", "_")
                # Write the file into the zip archive with its content
                zf.writestr(file_name, content)

        # Reset the stream's position to the beginning
        zip_stream.seek(0)
        zip_data = zip_stream.getvalue()

        # Get the size of the zip file for the Content-Length header
        zip_size = len(zip_data)

        # Prepare headers for file download
        headers = {
            "Content-Disposition": "attachment; filename=tsql_relts.zip",
            "Content-Length": str(zip_size),
        }

        # Return the zip file as a streaming response
        return Response(zip_data, media_type="application/zip", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Error creating ZIP file: {str(e)}"
        )


@router.websocket("/socket/{batch_id}")
async def batch_status_updates(
    websocket: WebSocket, batch_id: str
):  # , request: Request):
    """
    WebSocket endpoint for real-time batch status updates

    ---
    tags:
      - Batch Status
    parameters:
      - in: path
        name: batch_id
        required: true
        schema:
          type: string
          format: uuid
        description: Unique identifier for the batch
    responses:
      101:
        description: WebSocket connection established for batch updates
        content:
          application/json:
            schema:
              type: object
              properties:
                batch_id:
                  type: string
                  format: uuid
                  description: Unique identifier for the batch
                file_id:
                  type: string
                  format: uuid
                  description: Unique identifier for the file
                process_status:
                  type: string
                  description: Current processing status of the file
      400:
        description: Invalid batch_id format
      401:
        description: User authentication failed
      404:
        description: Batch not found
      500:
        description: Internal server error
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()

        # Validate batch_id format
        if not batch_service.is_valid_uuid(batch_id):
            await websocket.close(code=4002, reason="Invalid batch_id format")
            return

        # Accept WebSocket connection
        await websocket.accept()

        # Add to the connection manager for backend updates
        app_connection_manager.add_connection(batch_id, websocket)

        # Keep the connection open - FastAPI will close the connection if this returns
        while True:
            # no expectation that we will receive anything from the client but this keeps
            # the connection open and does not take cpu cycle
            try:
                await websocket.receive_text()
            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from batch {batch_id}")
        await close_connection(batch_id)
    except Exception as e:
        logger.error("Error in WebSocket connection", error=str(e))
        await close_connection(batch_id)


@router.get("/batch-story/{batch_id}")
async def get_batch_status(request: Request, batch_id: str):
    """
    Retrieve batch history and file statuses

    ---
    tags:
      - Batch History
    parameters:
      - in: path
        name: batch_id
        required: true
        schema:
          type: string
          format: uuid
        description: Unique identifier for the batch
    responses:
      200:
        description: Batch history retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                batch:
                  type: object
                  properties:
                    batch_id:
                      type: string
                      format: uuid
                      description: Unique identifier for the batch
                    user_id:
                      type: string
                      description: ID of the user who owns the batch
                    files:
                      type: integer
                      description: Number of files in the batch
                    created_at:
                      type: string
                      format: date-time
                      description: Timestamp when the batch was created
                    updated_at:
                      type: string
                      format: date-time
                      description: Timestamp of last batch update
                    status:
                      type: string
                      description: Current processing status of the batch
                files:
                  type: array
                  description: List of files associated with the batch
                  items:
                    type: object
                    properties:
                      file_id:
                        type: string
                        format: uuid
                        description: Unique identifier for the file
                      batch_id:
                        type: string
                        format: uuid
                        description: ID of the batch the file belongs to
                      original_name:
                        type: string
                        description: Original name of the uploaded file
                      blob_path:
                        type: string
                        description: Path where file is stored
                      translated_path:
                        type: string
                        description: Path of the translated file (if available)
                      status:
                        type: string
                        description: Processing status of the file
                      error_count:
                        type: integer
                        description: Number of errors encountered
                      created_at:
                        type: string
                        format: date-time
                        description: Timestamp when the file was uploaded
                      updated_at:
                        type: string
                        format: date-time
                        description: Timestamp of last file status update
      400:
        description: Invalid batch_id format
      401:
        description: User authentication failed
      404:
        description: Batch not found
      500:
        description: Internal server error
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()
        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate batch_id format
        if not batch_service.is_valid_uuid(batch_id):
            raise HTTPException(status_code=400, detail="Invalid batch_id format")

        # Fetch batch details
        batch_data = await batch_service.get_batch(batch_id, user_id)
        if not batch_data:
            raise HTTPException(status_code=404, detail="Batch not found")

        return batch_data
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error retrieving batch history", error=str(e))
        error_message = str(e)
        if "403" in error_message:
            raise HTTPException(status_code=403, detail="Incorrect user_id") from e
        else:
            raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/batch-summary/{batch_id}")
async def get_batch_summary(request: Request, batch_id: str):
    """
    Retrieve batch summary for a given batch ID.
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()

        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Retrieve batch summary
        batch_summary = await batch_service.get_batch_summary(batch_id, user_id)
        if not batch_summary:
            raise HTTPException(status_code=404, detail="No batch summary found.")

        return batch_summary

    except HTTPException as e:
        logger.error("Error fetching batch summary", error=str(e))
        raise e
    except Exception as e:
        logger.error("Error fetching batch summary", error=str(e))
        raise HTTPException(status_code=404, detail="Batch not found")


@router.get("/testplugin")
async def test_plugin(request: Request):
    """
    Test the Syntax Checker Plugin

    ---
    tags:
      - Syntax Checker
    parameters:
      - in: query
        name: candidate_sql
        type: string
        required: true
        description: The SQL query to check for syntax errors.
    responses:
      200:
        description: A JSON list of syntax errors or an empty list if there are no errors.
        schema:
          type: array
          items:
            type: object
            properties:
              Line:
                type: integer
                description: The line number where the error occurred.
              Column:
                type: integer
                description: The column number where the error occurred.
              Error:
                type: string
                description: The error message.
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            detail:
              type: string
              description: Error details.
    """
    try:
        # Set the environment variables for Azure OpenAI
        candidate_sql = "-- Return the first 5 rows from the 'employees' table \n SELECT FIRST 5 * FROM employees;"
        ccp = SyntaxCheckerPlugin()
        result = await ccp.check_syntax(candidate_sql)
        print(result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/upload")
async def upload_file(
    request: Request, file: UploadFile = File(...), batch_id: str = Form(...)
):
    """
    Upload file for conversion

    ---
    tags:
      - File Conversion
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
      - in: formData
        name: batch_id
        type: string
        format: uuid
        required: true
        description: The batch ID to associate the file with.
    responses:
      200:
        description: File uploaded successfully
        schema:
          type: object
          properties:
            batch_info:
              type: object
              properties:
                batch_id:
                  type: string
                  format: uuid
                  description: Unique identifier for the conversion batch
                user_id:
                  type: string
                  description: ID of the authenticated user
                created_at:
                  type: string
                  format: date-time
                  description: Timestamp when the batch was created
                updated_at:
                  type: string
                  format: date-time
                  description: Timestamp of last update
                status:
                  type: string
                  description: Overall status of the conversion batch
            file:
              type: object
              properties:
                file_id:
                  type: string
                  format: uuid
                  description: Unique identifier for the file
                original_name:
                  type: string
                  description: Original filename
                blob_path:
                  type: string
                  description: Path where file is stored
                translated_path:
                  type: string
                  description: Path of the translated file (if available)
                status:
                  type: string
                  description: Status of file processing
                error_count:
                  type: integer
                  description: Number of errors encountered
                created_at:
                  type: string
                  format: date-time
                  description: When file was uploaded
                updated_at:
                  type: string
                  format: date-time
                  description: Last status update
      400:
        description: Invalid file type or missing authentication
      401:
        description: User not authenticated
      500:
        description: Internal server error during processing
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()
        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate batch_id format
        logger.info(f"batch_id: {batch_id}")
        if not batch_service.is_valid_uuid(batch_id):
            raise HTTPException(status_code=400, detail="Invalid batch_id format")

        # Upload file via BatchService
        upload_result = await batch_service.upload_file_to_batch(
            batch_id, user_id, file
        )

        return upload_result

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/file/{file_id}")
async def get_file_details(request: Request, file_id: str):
    """
    Retrieve file details and processing logs.

    ---
    tags:
      - File Management
    parameters:
      - in: path
        name: file_id
        required: true
        schema:
          type: string
          format: uuid
        description: Unique identifier for the file.
    responses:
      200:
        description: File details retrieved successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                file:
                  type: object
                  properties:
                    file_id:
                      type: string
                      format: uuid
                      description: Unique identifier for the file.
                    batch_id:
                      type: string
                      format: uuid
                      description: ID of the batch the file belongs to.
                    original_name:
                      type: string
                      description: Original name of the uploaded file.
                    blob_path:
                      type: string
                      description: Path where file is stored.
                    translated_path:
                      type: string
                      description: Path of the translated file (if available).
                    status:
                      type: string
                      description: Processing status of the file.
                    error_count:
                      type: integer
                      description: Number of errors encountered.
                    created_at:
                      type: string
                      format: date-time
                      description: Timestamp when the file was uploaded.
                    updated_at:
                      type: string
                      format: date-time
                      description: Timestamp of last file status update.
                logs:
                  type: array
                  description: List of logs associated with the file.
                  items:
                    type: object
                    properties:
                      file_id:
                        type: string
                        format: uuid
                        description: Unique identifier for the file.
                      status:
                        type: string
                        description: Status of the file at the time of log entry.
                      description:
                        type: string
                        description: Description of the log event.
                      log_type:
                        type: string
                        description: Type of log event (success or error).
                      timestamp:
                        type: string
                        format: date-time
                        description: Timestamp of the log entry.
      400:
        description: Invalid file_id format.
      401:
        description: User authentication failed.
      404:
        description: File not found.
      500:
        description: Internal server error.
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()
        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate file_id format
        if not batch_service.is_valid_uuid(file_id):
            raise HTTPException(status_code=400, detail="Invalid file_id format")

        # Fetch file details
        file_data = await batch_service.get_file_report(file_id)
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found")

        return file_data

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error retrieving file details", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/delete-batch/{batch_id}")
async def delete_batch_details(request: Request, batch_id: str):
    """
    delete batch history using batch_id

    ---
    tags:
      - Batch Delete
    parameters:
      - in: path
        name: batch_id
        required: true
        schema:
          type: string
          format: uuid
        description: Unique identifier for the batch
    responses:
      200:
        description: Batch deleted successfully
      400:
        description: Invalid batch_id format
      401:
        description: User authentication failed
      404:
        description: Batch not found
      500:
        description: Internal server error
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()
        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate file_id format
        if not batch_service.is_valid_uuid(batch_id):
            raise HTTPException(
                status_code=400, detail=f"Invalid batch_id format: {batch_id}"
            )

        await batch_service.delete_batch_and_files(batch_id, user_id)

        logger.info(f"Batch deleted successfully: {batch_id}")
        return {"message": "Batch deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to delete batch from database", error=str(e))
        raise HTTPException(status_code=500, detail="Database connection error")


@router.delete("/delete-file/{file_id}")
async def delete_file_details(request: Request, file_id: str):
    """
    delete file history using batch_id

    ---
    tags:
      - File Delete
    parameters:
      - in: path
        name: file_id
        required: true
        schema:
          type: string
          format: uuid
        description: Unique identifier for the batch
    responses:
      200:
        description: File deleted successfully
      400:
        description: Invalid file_id format
      401:
        description: User authentication failed
      404:
        description: File not found
      500:
        description: Internal server error
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()
        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate file_id format
        if not batch_service.is_valid_uuid(file_id):
            raise HTTPException(
                status_code=400, detail=f"Invalid file_id format: {file_id}"
            )

        # Delete file
        file_delete = await batch_service.delete_file(file_id, user_id)
        if file_delete is None:
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

        logger.info(f"File deleted successfully: {file_delete}")
        return {"message": "File deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to delete file from database", error=str(e))
        raise HTTPException(status_code=500, detail="Database connection error")


@router.delete("/delete_all")
async def delete_all_details(request: Request):
    """
    delete all the history of batches, files and logs

    ---
    tags:
      - Delete All
    responses:
      200:
        description: All user data deleted successfully
      401:
        description: User authentication failed
      404:
        description: Delete operation failed
      500:
        description: Internal server error
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()
        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Validate file_id format
        if not batch_service.is_valid_uuid(user_id):
            raise HTTPException(
                status_code=400, detail=f"Invalid user_id format: {user_id}"
            )

        # Delete all the files from storage and cosmosDB
        delete_all = await batch_service.delete_all_from_storage_cosmos(user_id)
        if delete_all is None:
            logger.error("File/Batch not found")
            raise HTTPException(status_code=404, detail="File/Batch not found")

        logger.info(f"All user data deleted successfully: {user_id}")
        return {"message": "All user data deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Failed to delete user data from database", error=str(e))
        raise HTTPException(status_code=500, detail="Database connection error")


@router.post("/queue-send")
async def queue_send(request: Request):

    queue_service = QueueService()
    # Get the payload from the request body
    payload = await request.json()
    translate_from = payload.get("translate_from")
    translate_to = payload.get("translate_to")
    batch_id = payload.get("batch_id")

    if not batch_id or not translate_to:
        raise HTTPException(
            status_code=400, detail="batch_id and translate_to are required"
        )

    # Create the message to be sent to the queue
    message = {
        "batch_id": batch_id,
        "translate_from": translate_from,
        "translate_to": translate_to,
    }

    # Send the message to the Azure Service Bus Queue
    await queue_service.send_message_to_queue(message)


@router.get("/queue-entry")
async def queue_entry(request: Request):
    """
    Process queue entry
    ---
    tags:
    - Queue Processing
    parameters:
    - in: body
      name: queue_entry
      schema:
        type: object
        properties:
          batch_id:
            type: string
            format: uuid
          translate_from:
            type: string
          translate_to:
            type: string
    responses:
      200:
        description: Queue entry processed successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                message:
                  type: string
      400:
        description: Invalid queue entry request
      500:
        description: Internal server error
    """
    try:
        # Get the payload from the request body
        queue_service = QueueService()

        messages = await queue_service.receive_messages_from_queue()

        batch_id = messages.get("batch_id")

        await process_batch_async(batch_id)

        return {
            "batch_id": batch_id,
            "status": "Processing started successfully",
            "message": "Files queued for processing",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/batch-history")
async def list_batch_history(request: Request, offset: int = 0, limit: int = 25):
    """
    Retrieve batch processing history for the authenticated user.

    ---
    tags:
      - Batch History
    parameters:
      - in: query
        name: offset
        required: false
        schema:
          type: integer
        description: Pagination offset for batch history retrieval.
      - in: query
        name: limit
        required: false
        schema:
          type: integer
        description: Number of batch history records to fetch.
    responses:
      200:
        description: Successfully retrieved batch history.
        content:
          application/json:
            schema:
              type: array
              items:
                type: object
                properties:
                  batch_id:
                    type: string
                    format: uuid
                    description: Unique identifier for the batch.
                  user_id:
                    type: string
                    description: User ID associated with the batch.
                  created_at:
                    type: string
                    format: date-time
                    description: Timestamp when the batch was created.
                  updated_at:
                    type: string
                    format: date-time
                    description: Timestamp of the last update.
                  status:
                    type: string
                    description: Processing status of the batch.
      400:
        description: Invalid request parameters.
      401:
        description: Unauthorized request.
      500:
        description: Internal server error.
    """
    try:
        batch_service = BatchService()
        await batch_service.initialize_database()

        # Authenticate user
        authenticated_user = get_authenticated_user(request)
        user_id = authenticated_user.user_principal_id
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Retrieve batch history
        batch_history = await batch_service.get_batch_history(
            user_id, limit=limit, offset=offset
        )
        if not batch_history:
            return HTTPException(status_code=404, detail="No batch history found.")

        return batch_history

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error("Error fetching batch history", error=str(e))
        raise HTTPException(status_code=500, detail="Error retrieving batch history")


async def process_queue_tasks():
    """Background task that polls the queue for processing tasks"""
    queue_service = QueueService()

    while True:
        try:
            # Get a message from the queue (a task to process)
            messages = await queue_service.receive_messages_from_queue(max_messages=1)
            logger.info(f"Received messages1: {messages} \n\n\n")
            if messages and len(messages) > 0:
                # Extract the batch_id from the message
                logger.info("Received task from queue IF \n\n\n")
                message = messages[0]
                logger.info(f"print Message: {message}")
                batch_id = message.get("batch_id")
                logger.info(f"print batch_id: {batch_id} \n\n\n")
                if batch_id:
                    logger.info(f"Retrieved task for batchq: {batch_id} \n\n\n")
                    # Process the batch based on the task
                    await process_batch_async(batch_id)
                else:
                    logger.error("Received task without batch_id")

            # Wait before checking again
            await asyncio.sleep(20)

        except Exception as e:
            logger.error(f"Error processing queue task: {str(e)}")
            await asyncio.sleep(60)  # Longer delay after errors
