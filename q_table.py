#!/usr/bin/env python3

import pickle
import csv
from collections import defaultdict
from typing import Dict, Tuple

class QTable:
    def __init__(self, actions):
        self.actions = actions

        self.q_table: Dict[Tuple, Dict[int, float]] = defaultdict(lambda: {a: 0.0 for a in self.actions})

    def GetStateActions(self, state):
        return self.q_table[state]

    def GetQTable(self, state, action):
        return self.q_table[state][action]

    def SetQTable(self, state, action, value):
        self.q_table[state][action] = value
    
    def MaxActionValue(self, state):
        return max(self.q_table[state].values())
    
    # Update

    def Update(self, state, action, reward, next_state, alpha, gamma):
        current_q = self.GetQTable(state, action)
        next_max_q = self.MaxActionValue(next_state)

        new_q = current_q + alpha * (reward + gamma * next_max_q - current_q)
        self.SetQTable(state, action, new_q)

    # Save and load

      def SaveQTable(self, path):
        with open(path, "wb") as f:
            pickle.dump(dict(self.q_table), f)

    def LoadQTable(self, path):
        with open(path, "rb") as f:
            data = pickle.load(f)

        #Re-wrap with defaultdict
        self.q_table = defaultdict(
            lambda: {a: 0.0 for a in self.actions},
            data
        )

    def ExportCSV(self, path):
        with open(path, "w", newline = "") as f:
            writer = csv.writer(f)

            writer.writerow([
                "pos_x",
                "pos_y",
                "map_bank",
                "map_num",
                "in_battle",
                "direction",
                "action",
                "q_value"
            ])

            for state, action_values in self.q_table.items():
                pos_x, pos_y, map_bank, map_num, in_battle, direction = state

                for action, q_value in action_values.items():
                    writer.writerow([
                        pos_x,
                        pos_y,
                        map_bank,
                        map_num,
                        in_battle,
                        direction,
                        action,
                        q_value
                    ])