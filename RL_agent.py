#!/usr/bin/env python3
from datetime import datetime # for csv file logging
import actions 
from q_learning_agent import QLearningAgent

class RLAgent:
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

        self.agentState = None
        self.action = None
        
        self.qLearningAgent = QLearningAgent()

        #We load the QTable for the agent
        path = "./QTables/qTable.pkl"
        self.qLearningAgent.q_table.LoadQTable(path)

    def EncodeState(self, state):
        self.posX = state["x"]
        self.posY = state["y"]
        self.mapBank = state["mapBank"]
        self.mapNum = state["mapNum"]

        self.inBattle = int(state["isInBattle"])

        self.direction = self.actions[state["direction"]].value #not directions, but it returns the correct value anyway
        return (self.posX, self.posY, self.mapBank, self.mapNum, self.inBattle, self.direction)

    # Here we have the thinking process of the AI, that will return an action
    def ThinkingProcess(self, state):
        self.agentState = self.EncodeState(state)
        self.action = self.qLearningAgent.ChooseAction(self.agentState)
        return self.action

    # Here we update the AI state given 
    def UpdateAIState(self, state):
        self.posX = state["x"]
        self.posY = state["y"]
        self.mapBank = state["mapBank"]
        self.mapNum = state["mapNum"]

        self.inBattle = int(state["isInBattle"])

        self.direction = self.actions[state["direction"]].value #not directions, but it returns the correct value anyway
        self.reward = state["reward"]
        self.isDone = state["isDone"]

        #When the episode finishes the QTable is saved for the agent and for debugging purposes
        if self.isDone == True:
            #Save of the definitive QTable
            path = "./QTables/qTable.pkl"
            self.qLearningAgent.q_table.SaveQTable(path)

            #Save of the QTable for logging the different results"
            logPath = f"./QTables/LogQTables/log_qTable_{datetime.now().strftime('%Y%m%d')}/log_qTable_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.qLearningAgent.q_table.ExportCSV(logPath)

    def UpdateAIAgent(self, state):
        nextState = self.EncodeState(state)
        self.qLearningAgent.Update(self.agentState, self.action, self.reward, nextState)

        #Epsilon decay for improving learning
        self.qLearningAgent.DecayEpsilon()