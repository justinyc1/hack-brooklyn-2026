import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
import uuid
import os
import logging
from config import settings

logger = logging.getLogger(__name__)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
    region_name=settings.aws_region
)

BUCKET_NAME = settings.s3_bucket_name

async def upload_file_to_s3(file_obj, object_name: str, content_type: str = None) -> str:
    """Upload a file object to an S3 bucket"""
    try:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
            
        s3_client.upload_fileobj(file_obj, BUCKET_NAME, object_name, ExtraArgs=extra_args)
        logger.info(f"Successfully uploaded {object_name} to {BUCKET_NAME}")
        return f"s3://{BUCKET_NAME}/{object_name}"
    except ClientError as e:
        logger.error(f"Failed to upload to S3: {e}")
        raise e

def generate_presigned_url(object_name: str, expiration=3600) -> str:
    """Generate a presigned URL to share an S3 object"""
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': BUCKET_NAME,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
        return response
    except ClientError as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None

def generate_presigned_post(object_name: str, content_type: str = None, expiration=3600):
    """Generate a presigned URL S3 POST request to upload a file"""
    try:
        fields = {}
        conditions = []
        if content_type:
            fields["Content-Type"] = content_type
            conditions.append({"Content-Type": content_type})
            
        response = s3_client.generate_presigned_post(BUCKET_NAME,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
        return response
    except ClientError as e:
        logger.error(f"Failed to generate presigned POST URL: {e}")
        return None

def download_file_from_s3(object_name: str, file_path: str):
    """Download a file from S3 to a local path"""
    try:
        s3_client.download_file(BUCKET_NAME, object_name, file_path)
        logger.info(f"Successfully downloaded {object_name} to {file_path}")
        return True
    except ClientError as e:
        logger.error(f"Failed to download from S3: {e}")
        return False

def get_s3_key_for_artifact(session_id: str, artifact_type: str, filename: str) -> str:
    """
    Generate a standardized S3 key for session artifacts.
    artifact_type: 'audio', 'transcripts', 'code_submissions', 'reports', 'resumes'
    """
    return f"sessions/{session_id}/{artifact_type}/{filename}"


class S3MultipartAudioStreamer:
    """Streams binary audio chunks to S3 using multipart upload."""
    
    # S3 requires parts to be at least 5MB (except the last part)
    MIN_PART_SIZE = 5 * 1024 * 1024

    def __init__(self, session_id: str, content_type: str = "audio/webm"):
        self.session_id = session_id
        self.object_key = get_s3_key_for_artifact(session_id, "audio", f"recording_{session_id}.webm")
        self.content_type = content_type
        
        self.upload_id = None
        self.parts = []
        self.part_number = 1
        self.buffer = bytearray()
        
        try:
            response = s3_client.create_multipart_upload(
                Bucket=BUCKET_NAME,
                Key=self.object_key,
                ContentType=self.content_type
            )
            self.upload_id = response['UploadId']
            logger.info(f"Started multipart upload for session {self.session_id}, UploadId: {self.upload_id}")
        except ClientError as e:
            logger.error(f"Failed to start multipart upload: {e}")
            raise e

    def add_chunk(self, chunk: bytes):
        if not self.upload_id:
            return
            
        self.buffer.extend(chunk)
        if len(self.buffer) >= self.MIN_PART_SIZE:
            self._upload_current_buffer()

    def _upload_current_buffer(self):
        if not self.buffer:
            return
            
        try:
            part_data = bytes(self.buffer)
            response = s3_client.upload_part(
                Bucket=BUCKET_NAME,
                Key=self.object_key,
                PartNumber=self.part_number,
                UploadId=self.upload_id,
                Body=part_data
            )
            self.parts.append({
                'PartNumber': self.part_number,
                'ETag': response['ETag']
            })
            logger.info(f"Uploaded part {self.part_number} for session {self.session_id}")
            self.part_number += 1
            self.buffer.clear()
        except ClientError as e:
            logger.error(f"Failed to upload part {self.part_number}: {e}")

    def close(self) -> str | None:
        """Completes the upload and returns the object key/URL, or None if failed."""
        if not self.upload_id:
            return None
            
        if self.buffer:
            self._upload_current_buffer()
            
        try:
            s3_client.complete_multipart_upload(
                Bucket=BUCKET_NAME,
                Key=self.object_key,
                UploadId=self.upload_id,
                MultipartUpload={'Parts': self.parts}
            )
            logger.info(f"Completed multipart upload for session {self.session_id}")
            return f"s3://{BUCKET_NAME}/{self.object_key}"
        except ClientError as e:
            logger.error(f"Failed to complete multipart upload: {e}")
            # Try to abort to avoid dangling parts
            s3_client.abort_multipart_upload(
                Bucket=BUCKET_NAME,
                Key=self.object_key,
                UploadId=self.upload_id
            )
            return None

