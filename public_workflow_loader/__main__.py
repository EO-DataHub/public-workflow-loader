import logging
import os

import click

from .workflow_access_client import WorkflowAccessClient
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
        logging.error("Directory %s does not exist.", dir)
        return False
    return True


@click.command()
@click.argument("workspace", type=str)
@click.argument("workflows-file-path", type=str)
@click.argument("templates-file-path", type=str)
@click.option("-p", "--prefix", type=str, default="deployed")
def main(workspace: str, workflows_file_path: str, templates_file_path: str, prefix: str):
    """
    Load CWL workflows from the given directory and deploy them to the Workflow Runner.
    """

    workflow_runner_api_url = os.getenv("WORKFLOW_RUNNER_API_URL")
    if not workflow_runner_api_url:
        raise ValueError("WORKFLOW_RUNNER_API_URL environment variable is not set.")

    workspace_api_token = os.getenv("WORKSPACE_API_TOKEN")
    if not workspace_api_token:
        raise ValueError("WORKSPACE_API_TOKEN environment variable is not set.")

    policy_s3_bucket = os.getenv("S3_POLICY_BUCKET")
    if not policy_s3_bucket:
        raise ValueError("S3_POLICY_BUCKET environment variable is not set.")

    workflow_runner_client = WorkflowRunnerClient(
        base_wr_url=workflow_runner_api_url,
        workspace=workspace,
        api_token=workspace_api_token,
    )
    workflow_access_client = WorkflowAccessClient(
        template_filepath=templates_file_path,
        bucket=policy_s3_bucket,
        prefix=prefix,
        workspace=workspace,
    )

    if not does_dir_exist(workflows_file_path):
        raise ValueError(f"Directory {workflows_file_path} does not exist.")

    ## Get all files in directory
    workflow_files = [
        file_path for file_path in os.listdir(workflows_file_path) if file_path.endswith(".cwl")
    ]

    logging.info("Found workflow files to load: %s", workflow_files)

    deploy_count = 0

    for file in workflow_files:
        file_path = os.path.join(workflows_file_path, file)
        workflow_id = workflow_runner_client.deploy_workflow_from_file_path(file_path)
        if workflow_id:
            workflow_access_client.create_and_upload_access_policy(workspace, workflow_id)
            deploy_count += 1

    logging.info("%i workflows deployed and access policies created.", deploy_count)


if __name__ == "__main__":
    main()
