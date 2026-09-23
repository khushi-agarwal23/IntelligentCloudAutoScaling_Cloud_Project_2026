import random
import pickle


class QLearningAgent:

    def __init__(
        self,
        actions=(0, 1, 2),
        learning_rate=0.1,
        discount_factor=0.9,
        epsilon=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.995
    ):
        self.actions = list(actions)
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        # Q-table:
        # state -> [Q-value for action 0, action 1, action 2]
        self.q_table = {}

    def get_q_values(self, state):
        state = tuple(state)

        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)

        return self.q_table[state]

    def choose_action(self, state, training=True):
        q_values = self.get_q_values(state)

        # Exploration during training
        if training and random.random() < self.epsilon:
            return random.choice(self.actions)

        # Exploitation: choose action with highest Q-value
        max_q = max(q_values)

        best_actions = [
            action
            for action, value in zip(self.actions, q_values)
            if value == max_q
        ]

        return random.choice(best_actions)

    def update(self, state, action, reward, next_state, done=False):
        q_values = self.get_q_values(state)
        next_q_values = self.get_q_values(next_state)

        current_q = q_values[action]

        if done:
            target = reward
        else:
            target = reward + self.discount_factor * max(next_q_values)

        # Q-learning update rule
        q_values[action] = current_q + self.learning_rate * (
            target - current_q
        )

    def decay_epsilon(self):
        self.epsilon = max(
            self.epsilon_min,
            self.epsilon * self.epsilon_decay
        )

    def save(self, filepath):
        with open(filepath, "wb") as file:
            pickle.dump(self, file)

    @staticmethod
    def load(filepath):
        with open(filepath, "rb") as file:
            return pickle.load(file)