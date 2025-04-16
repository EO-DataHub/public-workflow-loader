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
            raise ValueError(f"Attempted to update workflow: {workflow_id} - {response.text}")
        else:
            logging.info("Successfully updated workflow: %s", workflow_id)

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
            logging.info("Successfully deployed workflow: %s", workflow_id)
        elif response.status_code == 409:
            logging.warning(
                "Failed to deploy workflow: %s, already deployed, updating instead.", workflow_id
            )
            self.update(workflow_id, workflow)
        else:
            raise ValueError(
                f"{workflow_id} - URL: {self.wr_url}/processes, Error: {response.text}"
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
                            if workflow_id := item.get("id"):
                                return workflow_id
                            raise ValueError("Workflow ID not found in CWL file.")
                raise ValueError("Invalid CWL file format: 'Workflow' class not found.")
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse CWL file: {e}") from e

    def deploy_workflow_from_file_path(self, workflow_file_path) -> str:
        """
        Deploy a workflow to the Workflow Runner.
        """
        logging.info("Deploying workflow from %s", workflow_file_path)
        try:
            with open(workflow_file_path, "r") as file:
                workflow = file.read()
                workflow_id = self.get_workflow_id(workflow)
                self.deploy(workflow_id, workflow)
            return workflow_id
        except Exception as e:
            logging.error("Failed to deploy workflow at %s: %s", workflow_file_path, e)
            return ""
