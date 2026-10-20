import random


class AutoScalingEnvironment:

    def __init__(self):
        self.min_instances = 1
        self.max_instances = 3
        self.instances = 1

        self.cpu = 50
        self.requests = 50

    def reset(self):
        """Start a new training episode."""

        self.instances = random.randint(
            self.min_instances,
            self.max_instances
        )

        self._generate_workload()

        return self.get_state()

    def _generate_workload(self):
        """Generate one workload and keep it as the current state."""

        self.cpu = random.randint(10, 90)
        self.requests = random.randint(10, 100)

    def get_state(self):
        """Return the current discrete state."""

        return (
            self.discretize_cpu(self.cpu),
            self.discretize_requests(self.requests),
            self.instances
        )

    def discretize_cpu(self, cpu):
        """Convert CPU percentage into 3 levels."""

        if cpu < 30:
            return 0       # Low
        elif cpu <= 60:
            return 1       # Medium
        else:
            return 2       # High

    def discretize_requests(self, requests):
        """Convert request count into 3 levels."""

        if requests < 40:
            return 0       # Low
        elif requests <= 70:
            return 1       # Medium
        else:
            return 2       # High

    def take_action(self, action):
        """
        Actions:
        0 = scale in
        1 = maintain
        2 = scale out
        """

        if action == 0 and self.instances > self.min_instances:
            self.instances -= 1

        elif action == 2 and self.instances < self.max_instances:
            self.instances += 1

        return self.instances

    def calculate_reward(self, action):
        """
        Reward the agent based on the current workload.

        High CPU/request load:
            Scale out is rewarded.

        Medium workload:
            Maintaining is rewarded.

        Low workload:
            Scaling in is rewarded.
        """

        high_load = self.cpu > 60 or self.requests > 70
        low_load = self.cpu < 30 and self.requests < 40

        if high_load:

            if action == 2:
                return 10

            elif action == 1:
                return 2

            else:
                return -10

        elif low_load:

            if action == 0 and self.instances > self.min_instances:
                return 10

            elif action == 1:
                return 3

            else:
                return -5

        else:

            if action == 1:
                return 10

            elif action == 0:
                return 5

            else:
                return -3

    def step(self, action):
        """
        Perform one RL step.

        Returns:
            next_state
            reward
            done
        """

        # Calculate reward using the CURRENT workload.
        reward = self.calculate_reward(action)

        # Apply the selected scaling action.
        self.take_action(action)

        # Generate the next workload.
        self._generate_workload()

        # Build the next state.
        next_state = self.get_state()

        # Episodes currently use a fixed number of steps.
        done = False

        return next_state, reward, done