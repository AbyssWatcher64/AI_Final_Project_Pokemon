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
        # for a specific choice it would be something like self.actions.UP / self.actions.A
        return random.choice(list(self.actions))

    # Here we update the AI state given 
    def UpdateAIState(self, state):
        self.posX = state["x"]
        self.posY = state["y"]
        self.mapBank = state["mapBank"]
        self.mapNum = state["mapNum"]

        self.inBattle = int(state["isInBattle"])

        self.direction = self.actions[state["direction"]].value #not directions, but it returns the correct value anyway
        self.reward = state["reward"]