import random


class AutoScalingEnvironment:

    def __init__(self):
        self.instances = 1

    def get_state(self):
        cpu = random.randint(10, 90)
        requests = random.randint(10, 100)

        return {
            "cpu": cpu,
            "requests": requests,
            "instances": self.instances
        }

    def take_action(self, action):
        # 0 = scale in
        # 1 = no change
        # 2 = scale out

        if action == 0 and self.instances > 1:
            self.instances -= 1

        elif action == 2 and self.instances < 3:
            self.instances += 1

        return self.instances

    def calculate_reward(self, cpu):
        if cpu > 80:
            return -10
        elif cpu > 60:
            return -2
        elif 30 <= cpu <= 60:
            return 10
        else:
            return 3


env = AutoScalingEnvironment()

for i in range(10):

    state = env.get_state()

    action = random.choice([0, 1, 2])

    instances = env.take_action(action)

    reward = env.calculate_reward(state["cpu"])

    print(
        f"State: {state} | "
        f"Action: {action} | "
        f"Instances: {instances} | "
        f"Reward: {reward}"
    )