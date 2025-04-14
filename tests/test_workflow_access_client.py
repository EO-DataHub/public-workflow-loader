import json
from unittest import mock
from unittest.mock import mock_open, patch

import pytest

from public_workflow_loader.workflow_access_client import WorkflowAccessClient


@pytest.fixture()
@patch("boto3.client")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""{"id": "", "public": true, "user_service": false}""",
)
def workflow_access_client(mock_open, mock_boto3_client):
    # Configure mocks
    mock_boto3_client_instance = mock.Mock()
    mock_boto3_client_instance.put_object.return_value = None
    mock_boto3_client.return_value = mock_boto3_client_instance
    workflow_access_client = WorkflowAccessClient(
        template_filepath="./templates",
        bucket="test-bucket",
        prefix="deployed",
        workspace="test-workspace",
    )
    return workflow_access_client


def test_create_access_policy(workflow_access_client):
    # Configure mocks
    result = workflow_access_client.create_access_policy("test_workflow")

    # Assertions
    assert result == {"id": "test_workflow", "public": True, "user_service": False}


def test_create_and_upload_access_policy(workflow_access_client):
    # Configure mocks
    workflow_access_client.create_and_upload_access_policy("test-workspace", "test_workflow")

    # Configure variables
    workspace = "test-workspace"
    workflow_id = "test_workflow"
    bucket = "test-bucket"
    expected_policy = {"id": "test_workflow", "public": True, "user_service": False}

    # Assertions
    workflow_access_client.s3_client.put_object.assert_called_once_with(
        json.dumps(expected_policy),
        bucket,
        f"deployed/{workspace}/{workflow_id}.access_policy.json",
    )


@patch("boto3.client")
def test_create_s3_client(mock_boto3_client):
    WorkflowAccessClient.create_s3_client()

    # Assertions
    mock_boto3_client.assert_called_once_with("s3")
