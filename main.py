from fastapi import FastAPI
from pydantic import BaseModel

from q_learning_agent import QLearningAgent
from mock_aws import MockAutoScalingGroup


app = FastAPI(
    title="Intelligent Cloud Auto Scaling API"
)


MODEL_PATH = "models/q_table.pkl"

# Load the trained RL agent.
agent = QLearningAgent.load(MODEL_PATH)

# Create the mock AWS Auto Scaling Group.
mock_asg = MockAutoScalingGroup(
    initial_instances=1,
    min_instances=1,
    max_instances=3
)


class Workload(BaseModel):
    cpu: int
    requests: int


def cpu_level(cpu):
    if cpu < 30:
        return 0
    elif cpu <= 60:
        return 1
    else:
        return 2


def request_level(requests):
    if requests < 40:
        return 0
    elif requests <= 70:
        return 1
    else:
        return 2


@app.get("/")
def home():
    return {
        "message": "RL Auto Scaling API is running",
        "instances": mock_asg.instances
    }


@app.post("/predict")
def predict(workload: Workload):

    # Build the RL state using the CURRENT mock ASG capacity.
    state = (
        cpu_level(workload.cpu),
        request_level(workload.requests),
        mock_asg.instances
    )

    # Ask the trained RL agent for a decision.
    action = agent.choose_action(
        state,
        training=False
    )

    action_names = {
        0: "SCALE IN",
        1: "MAINTAIN",
        2: "SCALE OUT"
    }

    # Apply the RL decision to the mock AWS ASG.
    scaling_result = mock_asg.apply_action(action)

    return {
        "cpu": workload.cpu,
        "requests": workload.requests,
        "previous_instances": state[2],
        "action": action,
        "decision": action_names[action],
        "new_instances": scaling_result["instances"],
        "aws_result": scaling_result["message"]
    }