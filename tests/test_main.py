import os
from collections.abc import Generator
from unittest import mock
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from public_workflow_loader.__main__ import does_dir_exist, main


@pytest.fixture
def setenvvar(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "WORKFLOW_RUNNER_API_URL": "https://example.com/wr",
            "WORKSPACE_API_TOKEN": "test-token",
            "S3_POLICY_BUCKET": "test-bucket",
        }
        for k, v in envvars.items():
            monkeypatch.setenv(k, v)
        yield


@patch("public_workflow_loader.__main__.does_dir_exist")
@patch("os.listdir")
@patch("public_workflow_loader.__main__.WorkflowRunnerClient")
@patch("public_workflow_loader.__main__.WorkflowAccessClient")
def test_cli(
    mock_WorkflowAccessClient: mock.MagicMock,
    mock_WorkflowRunnerClient: mock.MagicMock,
    mock_list_dir: mock.MagicMock,
    mock_does_dir_exist: mock.MagicMock,
    setenvvar: None,
) -> None:
    # Configure mocks
    mock_workflow_access_client = mock.Mock()
    mock_workflow_access_client.create_and_upload_access_policy.return_value = None
    mock_WorkflowAccessClient.return_value = mock_workflow_access_client
    mock_workflow_runner_client = mock.Mock()
    mock_workflow_runner_client.deploy_workflow_from_file_path.side_effect = [
        "test_workflow",
        "another_workflow",
    ]
    mock_WorkflowRunnerClient.return_value = mock_workflow_runner_client
    mock_list_dir.return_value = [
        "test_workflow.cwl",
        "another_workflow.cwl",
    ]
    mock_does_dir_exist.return_value = True

    # Configure variables
    workspace = "test-workspace"

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, [workspace, "./workflows", "./templates", "-p", "test-prefix"])

    # Assertions
    assert result.exit_code == 0
    mock_WorkflowRunnerClient.assert_called_once_with(
        base_wr_url="https://example.com/wr",
        workspace=workspace,
        api_token="test-token",
    )
    mock_WorkflowAccessClient.assert_called_once_with(
        template_filepath="./templates",
        bucket="test-bucket",
        prefix="test-prefix",
        workspace=workspace,
    )

    mock_does_dir_exist.assert_called_once_with("./workflows")
    mock_list_dir.assert_called_once_with("./workflows")
    assert mock_workflow_runner_client.deploy_workflow_from_file_path.call_count == 2
    mock_workflow_runner_client.deploy_workflow_from_file_path.assert_any_call("./workflows/test_workflow.cwl")
    mock_workflow_runner_client.deploy_workflow_from_file_path.assert_any_call("./workflows/another_workflow.cwl")
    assert mock_workflow_access_client.create_and_upload_access_policy.call_count == 2
    mock_workflow_access_client.create_and_upload_access_policy.assert_any_call(workspace, "test_workflow")
    mock_workflow_access_client.create_and_upload_access_policy.assert_any_call(workspace, "another_workflow")


@patch("public_workflow_loader.__main__.does_dir_exist")
@patch("os.listdir")
@patch("public_workflow_loader.__main__.WorkflowRunnerClient")
@patch("public_workflow_loader.__main__.WorkflowAccessClient")
def test_cli_failed_to_deploy(
    mock_WorkflowAccessClient: mock.MagicMock,
    mock_WorkflowRunnerClient: mock.MagicMock,
    mock_list_dir: mock.MagicMock,
    mock_does_dir_exist: mock.MagicMock,
    setenvvar: None,
) -> None:
    # Configure mocks
    mock_workflow_access_client = mock.Mock()
    mock_workflow_access_client.create_and_upload_access_policy.return_value = None
    mock_WorkflowAccessClient.return_value = mock_workflow_access_client
    mock_workflow_runner_client = mock.Mock()
    mock_workflow_runner_client.deploy_workflow_from_file_path.side_effect = [
        "",
        "another_workflow",
    ]
    mock_WorkflowRunnerClient.return_value = mock_workflow_runner_client
    mock_list_dir.return_value = [
        "test_workflow.cwl",
        "another_workflow.cwl",
    ]
    mock_does_dir_exist.return_value = True

    # Configure variables
    workspace = "test-workspace"

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, [workspace, "./workflows", "./templates"])

    # Assertions
    assert result.exit_code == 0
    mock_WorkflowRunnerClient.assert_called_once_with(
        base_wr_url="https://example.com/wr",
        workspace=workspace,
        api_token="test-token",
    )
    mock_WorkflowAccessClient.assert_called_once_with(
        template_filepath="./templates",
        bucket="test-bucket",
        prefix="deployed",
        workspace=workspace,
    )

    mock_does_dir_exist.assert_called_once_with("./workflows")
    mock_list_dir.assert_called_once_with("./workflows")
    assert mock_workflow_runner_client.deploy_workflow_from_file_path.call_count == 2
    mock_workflow_runner_client.deploy_workflow_from_file_path.assert_any_call("./workflows/test_workflow.cwl")
    mock_workflow_runner_client.deploy_workflow_from_file_path.assert_any_call("./workflows/another_workflow.cwl")
    # This will only be called for the second file, as the first workflow failed to deploy
    assert mock_workflow_access_client.create_and_upload_access_policy.call_count == 1
    mock_workflow_access_client.create_and_upload_access_policy.assert_any_call(workspace, "another_workflow")


@patch("public_workflow_loader.__main__.does_dir_exist")
@patch("os.listdir")
@patch("public_workflow_loader.__main__.WorkflowRunnerClient")
@patch("public_workflow_loader.__main__.WorkflowAccessClient")
def test_cli_dir_doesnt_exist(
    mock_WorkflowAccessClient: mock.MagicMock,
    mock_WorkflowRunnerClient: mock.MagicMock,
    mock_list_dir: mock.MagicMock,
    mock_does_dir_exist: mock.MagicMock,
    setenvvar: None,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Configure mocks
    mock_workflow_access_client = mock.Mock()
    mock_workflow_access_client.create_and_upload_access_policy.return_value = None
    mock_WorkflowAccessClient.return_value = mock_workflow_access_client
    mock_workflow_runner_client = mock.Mock()
    mock_workflow_runner_client.deploy_workflow_from_file_path.side_effect = [
        "test_workflow",
        "another_workflow",
    ]
    mock_WorkflowRunnerClient.return_value = mock_workflow_runner_client
    mock_list_dir.return_value = [
        "test_workflow.cwl",
        "another_workflow.cwl",
    ]
    mock_does_dir_exist.return_value = False

    # Configure variables
    workspace = "test-workspace"

    # Set up the CliRunner
    runner = CliRunner()

    # Invoke the CLI with a test topic
    result = runner.invoke(main, [workspace, "./workflows", "./templates"])

    # Assertions
    assert result.exit_code == 1
    assert "Directory ./workflows does not exist." in str(result.exception)


def test_does_dir_exist() -> None:
    # Test with an existing directory
    assert does_dir_exist("./tests")

    # Test with a non-existing directory
    assert not does_dir_exist("./non_existing_dir")
