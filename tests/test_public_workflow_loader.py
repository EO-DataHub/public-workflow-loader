import os
from unittest import mock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from public_workflow_loader.__main__ import main


@pytest.fixture()
def setenvvar(monkeypatch):
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "WORKFLOW_RUNNER_API_URL": "https://example.com/{workspace}",
            "WORKSPACE_API_TOKEN": "test-token",
        }
        for k, v in envvars.items():
            monkeypatch.setenv(k, v)
        yield


@patch("public_workflow_loader.__main__.does_dir_exist")
@patch("os.listdir")
@patch("public_workflow_loader.__main__.WorkflowRunnerClient")
def test_cli(mock_WorkflowRunnerClient, mock_list_dir, mock_does_dir_exist, setenvvar):

    # Configure mocks
    mock_workflow_runner_client = mock.Mock()
    print(mock_WorkflowRunnerClient)
    print(mock_workflow_runner_client)
    mock_workflow_runner_client.deploy_workflow_from_file_path.return_value = None
    mock_WorkflowRunnerClient.return_value = mock_workflow_runner_client
    mock_list_dir.return_value = [
        "test_workflow.cwl",
        "another_workflow.cwl",
    ]
    mock_does_dir_exist.return_value = True

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, ["test-workspace", "./workflows"])

    # Assertions
    assert result.exit_code == 0
    mock_WorkflowRunnerClient.assert_called_once_with(
        base_wr_url="https://example.com/{workspace}",
        workspace="test-workspace",
        api_token="test-token",
    )
    mock_does_dir_exist.assert_called_once_with("./workflows")
    mock_list_dir.assert_called_once_with("./workflows")
    assert mock_workflow_runner_client.deploy_workflow_from_file_path.call_count == 2
    mock_workflow_runner_client.deploy_workflow_from_file_path.assert_any_call("test_workflow.cwl")
    mock_workflow_runner_client.deploy_workflow_from_file_path.assert_any_call(
        "another_workflow.cwl"
    )


@patch("public_workflow_loader.__main__.does_dir_exist")
@patch("os.listdir")
@patch("public_workflow_loader.__main__.WorkflowRunnerClient")
def test_cli_dir_doesnt_exist(
    mock_WorkflowRunnerClient, mock_list_dir, mock_does_dir_exist, setenvvar, caplog
):

    # Configure mocks
    mock_workflow_runner_client = mock.Mock()
    mock_workflow_runner_client.deploy_workflow_from_file_path.return_value = None
    mock_WorkflowRunnerClient.return_value = mock_workflow_runner_client
    mock_list_dir.return_value = [
        "test_workflow.cwl",
        "another_workflow.cwl",
    ]
    mock_does_dir_exist.return_value = False

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, ["test-workspace", "./workflows"])

    # Assertions
    assert result.exit_code == 1
    assert "Directory ./workflows does not exist." in str(result.exception)
