import logging
import os

import click

from .workflow_runner_client import WorkflowRunnerClient

logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def does_dir_exist(path: str):
    """
    Check if the given directory exists.
    """
    if not os.path.exists(path):
        logging.error(f"Directory {dir} does not exist.")
        return False
    return True


@click.command()
@click.argument("workspace", type=str)
@click.argument("workflows-file-path", type=str)
def main(workspace: str, workflows_file_path: str):
    """
    Load CWL workflows from the given directory and deploy them to the Workflow Runner.
    """
    workflow_runner_client = WorkflowRunnerClient(
        base_wr_url=os.getenv("WORKFLOW_RUNNER_API_URL"),
        workspace=workspace,
        api_token=os.getenv("WORKSPACE_API_TOKEN"),
    )

    if not does_dir_exist(workflows_file_path):
        raise ValueError(f"Directory {workflows_file_path} does not exist.")

    ## Get all files in dir
    workflow_files = os.listdir(workflows_file_path)

    for file in workflow_files:
        file_path = os.path.join(workflows_file_path, file)
        workflow_runner_client.deploy_workflow_from_file_path(file_path)


if __name__ == "__main__":
    main()
