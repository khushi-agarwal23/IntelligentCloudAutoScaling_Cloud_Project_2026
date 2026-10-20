import os

from rl_environment import AutoScalingEnvironment
from q_learning_agent import QLearningAgent


EPISODES = 1000
STEPS_PER_EPISODE = 50


def train():

    env = AutoScalingEnvironment()
    agent = QLearningAgent()

    rewards = []

    for episode in range(EPISODES):

        state = env.reset()
        total_reward = 0

        for step in range(STEPS_PER_EPISODE):

            # Choose an action using the Q-learning agent
            action = agent.choose_action(
                state,
                training=True
            )

            # Perform the action in the environment
            next_state, reward, done = env.step(action)

            # Update the Q-table
            agent.update(
                state,
                action,
                reward,
                next_state,
                done
            )

            state = next_state
            total_reward += reward

            if done:
                break

        # Gradually reduce exploration
        agent.decay_epsilon()

        rewards.append(total_reward)

        if (episode + 1) % 100 == 0:

            average_reward = (
                sum(rewards[-100:]) / 100
            )

            print(
                f"Episode {episode + 1}/{EPISODES} | "
                f"Average Reward: {average_reward:.2f} | "
                f"Epsilon: {agent.epsilon:.3f}"
            )

    # Create models folder
    os.makedirs("models", exist_ok=True)

    # Save trained Q-learning agent
    agent.save("models/q_table.pkl")

    print("\nTraining complete.")
    print("Model saved to: models/q_table.pkl")


if __name__ == "__main__":
    train()