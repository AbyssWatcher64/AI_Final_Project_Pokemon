#!/usr/bin/env python3

import random
import actions 

class RandomAgent:
    def __init__ (self):
        self.posX = None
        self.posY = None
        self.mapBank = None
        self.mapNum = None

        self.inBattle = None
        self.direction = None

        self.reward = None
        self.isDone = None

        self.actions = actions.Action

# Here we have the thinking process of the AI, that will return an action
    def ThinkingProcess(self):
        return random.choice(list(self.actions))
    
    def UpdateAIState(self, state):
        self.posX = state[0]
        self.posY = state[1]
        self.mapBank = state[2]
        self.mapNum = state[3]

        self.inBattle = state[4]
        self.direction = state[5]

        self.reward = state[6]
        self.isDone = state[7]