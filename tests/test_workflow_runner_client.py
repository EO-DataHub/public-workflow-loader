import logging
from unittest import mock
from unittest.mock import patch

import pytest

from public_workflow_loader.workflow_runner_client import WorkflowRunnerClient


@pytest.fixture()
def workflow_runner_client():
    workflow_runner_client = WorkflowRunnerClient(
        base_wr_url="https://example.com/{workspace}",
        workspace="test-workspace",
        api_token="test-token",
    )
    return workflow_runner_client


@patch("requests.post")
def test_deploy_success(mock_requests_post, workflow_runner_client, caplog):

    # Set logging level
    caplog.set_level(logging.INFO)

    # Configure mocks
    mock_requests_post.return_value.status_code = 201

    workflow_runner_client.deploy("test_workflow", b"test_workflow_content")

    # Assertions
    mock_requests_post.assert_called_once_with(
        "https://example.com/test-workspace/processes",
        data=b"test_workflow_content",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/cwl+yaml",
        },
    )
    assert "Successfully deployed workflow: test_workflow" in caplog.text


@patch("requests.post")
@patch("requests.put")
def test_deploy_update_success(
    mock_requests_put, mock_requests_post, workflow_runner_client, caplog
):

    # Set logging level
    caplog.set_level(logging.INFO)

    # Configure mocks
    mock_requests_post.return_value.status_code = 409
    mock_requests_put.return_value.status_code = 204

    workflow_runner_client.deploy("test_workflow", b"test_workflow_content")

    # Assertions
    mock_requests_post.assert_called_once_with(
        "https://example.com/test-workspace/processes",
        data=b"test_workflow_content",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/cwl+yaml",
        },
    )
    mock_requests_put.assert_called_once_with(
        "https://example.com/test-workspace/processes/test_workflow",
        data=b"test_workflow_content",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/cwl+yaml",
        },
    )
    assert (
        "Failed to deploy workflow: test_workflow, already deployed, updating instead."
        in caplog.text
    )
    assert "Successfully updated workflow: test_workflow" in caplog.text


@patch("requests.post")
@patch("requests.put")
def test_deploy_update_failure(
    mock_requests_put, mock_requests_post, workflow_runner_client, caplog
):

    # Set logging level
    caplog.set_level(logging.INFO)

    # Configure mocks
    mock_requests_post.return_value.status_code = 409
    mock_requests_put.return_value.status_code = 500

    with pytest.raises(ValueError):
        workflow_runner_client.deploy("test_workflow", b"test_workflow_content")

    # Assertions
    mock_requests_post.assert_called_once_with(
        "https://example.com/test-workspace/processes",
        data=b"test_workflow_content",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/cwl+yaml",
        },
    )
    mock_requests_put.assert_called_once_with(
        "https://example.com/test-workspace/processes/test_workflow",
        data=b"test_workflow_content",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/cwl+yaml",
        },
    )
    assert (
        "Failed to deploy workflow: test_workflow, already deployed, updating instead."
        in caplog.text
    )


@patch("requests.post")
def test_deploy_failure(mock_requests_post, workflow_runner_client, caplog):

    # Set logging level
    caplog.set_level(logging.INFO)

    # Configure mocks
    mock_requests_post.return_value.status_code = 500

    with pytest.raises(ValueError):
        workflow_runner_client.deploy("test_workflow", b"test_workflow_content")

    # Assertions
    mock_requests_post.assert_called_once_with(
        "https://example.com/test-workspace/processes",
        data=b"test_workflow_content",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
            "Content-Type": "application/cwl+yaml",
        },
    )


def test_get_workflow_id(workflow_runner_client):
    # Mock the workflow content
    workflow_content = b"""\
        cwlVersion: v1.0
        $graph:
        - class: CommandLineTool
          id: step-1
        - class: Workflow
          id: test_workflow
        - class: CommandLineTool
          id: step-2
    """
    # Call the method
    result = workflow_runner_client.get_workflow_id(workflow_content)

    # Assertions
    assert result == "test_workflow"


def test_get_workflow_id_invalid_yaml(workflow_runner_client):
    # Mock the workflow content
    workflow_content = b"""\
        cwlVersion: v1.0
        $graph:
        - class: CommandLineTool
          id: step-1
        - class Workflow
          id: test_workflow
        class: CommandLineTool
          id: step-2
    """
    # Call the method
    with pytest.raises(ValueError, match="Failed to parse CWL file: "):
        workflow_runner_client.get_workflow_id(workflow_content)


def test_get_workflow_id_missing_workflow(workflow_runner_client):
    # Mock the workflow content
    workflow_content = b"""\
        cwlVersion: v1.0
        $graph:
        - class: CommandLineTool
          id: step-1
        - class: CommandLineTool
          id: test_workflow
        - class: CommandLineTool
          id: step-2
    """
    # Call the method
    with pytest.raises(ValueError, match="Invalid CWL file format: 'Workflow' class not found."):
        workflow_runner_client.get_workflow_id(workflow_content)


def test_get_workflow_id_missing_id(workflow_runner_client):
    # Mock the workflow content
    workflow_content = b"""\
        cwlVersion: v1.0
        $graph:
        - class: CommandLineTool
          id: step-1
        - class: Workflow
          if: test_workflow
        - class: CommandLineTool
          id: step-2
    """
    # Call the method
    with pytest.raises(ValueError, match="Workflow ID not found in CWL file."):
        workflow_runner_client.get_workflow_id(workflow_content)


@patch(
    "public_workflow_loader.workflow_runner_client.open",
    new_callable=mock.mock_open,
    read_data=b"""\
        cwlVersion: v1.0
        $graph:
        - class: CommandLineTool
          id: step-1
        - class: Workflow
          id: test_workflow
        - class: CommandLineTool
          id: step-2
    """,
)
@patch("public_workflow_loader.workflow_runner_client.WorkflowRunnerClient.deploy")
def test_deploy_workflow_from_file_path(mock_deploy, mock_open, workflow_runner_client):

    # Configure mocks
    mock_deploy.return_value = None
    workflow_runner_client.deploy_workflow_from_file_path("path/to/workflow.cwl")

    # Assertions
    mock_open.assert_called_once_with("path/to/workflow.cwl", "r")
    mock_deploy.assert_called_once_with(
        "test_workflow",
        b"""\
        cwlVersion: v1.0
        $graph:
        - class: CommandLineTool
          id: step-1
        - class: Workflow
          id: test_workflow
        - class: CommandLineTool
          id: step-2
    """,
    )
