from q_learning_agent import QLearningAgent


MODEL_PATH = "models/q_table.pkl"


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


def test_workload(agent, cpu, requests, instances):
    state = (
        cpu_level(cpu),
        request_level(requests),
        instances
    )

    action = agent.choose_action(
        state,
        training=False
    )

    action_names = {
        0: "SCALE IN",
        1: "MAINTAIN",
        2: "SCALE OUT"
    }

    print(
        f"CPU: {cpu}% | "
        f"Requests: {requests} | "
        f"Instances: {instances} | "
        f"Decision: {action_names[action]}"
    )


def main():

    agent = QLearningAgent.load(MODEL_PATH)

    print("Testing trained RL agent\n")

    test_workload(agent, 20, 20, 3)
    test_workload(agent, 45, 50, 2)
    test_workload(agent, 90, 95, 1)
    test_workload(agent, 75, 80, 2)
    test_workload(agent, 35, 40, 2)


if __name__ == "__main__":
    main()