import logging

import requests
import yaml


class WorkflowRunnerClient:

    def __init__(self, base_wr_url: str, workspace: str, api_token: str):
        """
        Initialize the WorkflowRunnerClient with the provided API client.
        """
        self.base_wf_url = base_wr_url
        self.wr_url = f"{base_wr_url}/{workspace}"
        self.api_token = api_token

    def update(self, workflow_id: str, workflow: bytes):
        """
        Update a workflow on the Workflow Runner.
        """
        response = requests.put(
            f"{self.wr_url}/processes/{workflow_id}",
            data=workflow,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/cwl+yaml",
            },
        )
        if response.status_code != 204:
            raise ValueError(f"Failed to update workflow: {workflow_id} - {response.text}")
        else:
            logging.info(f"Successfully updated workflow: {workflow_id}")

    def deploy(self, workflow_id: str, workflow: bytes):
        """
        Deploy a workflow to the Workflow Runner.
        """
        response = requests.post(
            f"{self.wr_url}/processes",
            data=workflow,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/cwl+yaml",
            },
        )
        if response.status_code == 201:
            logging.info(f"Successfully deployed workflow: {workflow_id}")
        elif response.status_code == 409:
            logging.warning(
                f"Failed to deploy workflow: {workflow_id}, already deployed, updating instead."
            )
            self.update(workflow_id, workflow)
        else:
            raise ValueError(
                f"Failed to deploy workflow: {workflow_id} - URL: "
                f"{self.wr_url}/processes, Error: {response.text}"
            )

    def get_workflow_id(self, workflow: bytes):
        """
        Get the workflow ID from the CWL file, as a string.
        """
        try:
            workflow_dict = yaml.safe_load(workflow)
            if isinstance(workflow_dict, dict) and "$graph" in workflow_dict:
                graph = workflow_dict["$graph"]
                # Find Workflow class in graph
                for item in graph:
                    if isinstance(item, dict) and "class" in item:
                        if item["class"] == "Workflow":
                            workflow_id = item.get("id")
                            if workflow_id is None:
                                raise ValueError("Workflow ID not found in CWL file.")
                            return workflow_id
                raise ValueError("Invalid CWL file format: 'Workflow' class not found.")
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse CWL file: {e}") from e

    def deploy_workflow_from_file_path(self, workflow_file_path) -> str:
        """
        Deploy a workflow to the Workflow Runner.
        """
        logging.info(f"Deploying workflow from {workflow_file_path}")
        try:
            with open(workflow_file_path, "r") as file:
                workflow = file.read()
                workflow_id = self.get_workflow_id(workflow)
                self.deploy(workflow_id, workflow)
            return workflow_id
        except Exception as e:
            logging.error(f"Failed to deploy workflow at {workflow_file_path}: {e}")
            return ""
