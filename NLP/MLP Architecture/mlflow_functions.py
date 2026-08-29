import requests
from item import TrainingParameters, TrialParameters
import mlflow
import os
from mlflow.exceptions import MlflowException

class MlflowManager():
    def __init__(
            self, 
            host,
            port
    ):
        self.host = f"http://{host}"
        self.port = str(port)

    def mlflow_init(self,):
        if self.is_mlflow_running():
            self.set_tracking_uri()
        else:
            raise ValueError("you need to start mlflow server first by running ./app/launchers/start-mlflow-server.sh &")

    def set_tracking_uri(self,):
        mlflow.set_tracking_uri(f"{str(self.host)}:{str(self.port)}")

    def is_mlflow_running(self,):
        try:
            response = requests.get(f"{self.host}:{self.port}/health", timeout=2)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False
    
    def mlflow_set_experiment(self, experiment_name):
        try:
            experiment_id = mlflow.create_experiment(
                name=experiment_name,
                # artifact_location="file:///runtime/data/MLFLOW/artifacts"  # Optionnel
            )
        except MlflowException:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            experiment_id = experiment.experiment_id

        return experiment_id


def log_mlflow_parameters(obj):
    for key, value in vars(obj).items():
        if isinstance(obj, TrialParameters):
            mlflow.log_param(f"trial_{key}", str(value)) 
        elif isinstance(obj, TrainingParameters):
            mlflow.log_param(f"train_{key}", str(value)) 

