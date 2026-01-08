#!/usr/bin/env python3

import random 
from .q_table import QTable
from .actions import Action
from .actions import ALL_ACTIONS

class QLearningAgent:
    def __init__(
        self,
        alpha=0.1,
        gamma=0.99,
        epsilon=1.0,
        epsilon_min=0.05,
        epsilon_decay=0.9995,
    ):
        self.alpha = alpha
        self.gamma = gamma

        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

        self.actions = ALL_ACTIONS
        self.q_table = QTable(self.actions)

    def ChooseAction(self, state):

        if random.random() < self.epsilon:
            random_action = random.choice(self.actions)
            print(f"Chosen random action: {random_action}")
            return random_action

        q_values = self.q_table.GetStateActions(state)
        best_action = max(q_values, key=q_values.get)
        print(f"Chosen best action based on reward: {best_action}")
        return best_action
    
    def Update(self, state, action, reward, next_state):
        
        self.q_table.Update(
            state,
            action,
            reward,
            next_state,
            self.alpha,
            self.gamma,
        )

    def DecayEpsilon(self):

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            self.epsilon = max(self.epsilon, self.epsilon_min)
            print(f"Epsilon decayed. New epsilon value: {self.epsilon}")

    