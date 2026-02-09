import json
import logging
import os
from typing import Any

import boto3
from mypy_boto3_s3 import S3Client


class WorkflowAccessClient:
    def __init__(self, template_filepath: str, bucket: str, prefix: str, workspace: str) -> None:
        self.s3_bucket = bucket
        self.s3_prefix = prefix
        self.workspace = workspace

        with open(os.path.join(template_filepath, "access-policy.json")) as file:
            self.access_policy_template = json.load(file)

        self.s3_client = self.create_s3_client()

    @staticmethod
    def create_s3_client() -> S3Client:
        return boto3.client("s3")

    def create_access_policy(self, workflow_id: str) -> dict[str, Any]:
        """
        Create an access policy for the given workflow ID.
        """
        access_policy = self.access_policy_template.copy()
        access_policy["id"] = workflow_id
        return access_policy

    def create_and_upload_access_policy(self, workspace: str, workflow_id: str) -> None:
        """
        Create and upload the access policy to S3.
        """
        access_policy = self.create_access_policy(workflow_id)
        s3_path = f"{self.s3_prefix}/{workspace}/{workflow_id}.access-policy.json"
        logging.info("Uploading access policy for %s to S3 at %s", workflow_id, s3_path)
        try:
            self.s3_client.put_object(Body=json.dumps(access_policy), Bucket=self.s3_bucket, Key=s3_path)
        except Exception as e:
            raise ValueError(f"Failed to upload access policy: {e}") from e
