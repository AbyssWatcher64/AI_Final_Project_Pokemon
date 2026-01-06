#!/usr/bin/env python3

from collections import namedtuple

class RewardSystem: 
    def __init__(self):
        self.visitedTiles = set()
        self.reward = 0
        self.framesNotMoving = 0

        self.pendingGoalLocation = set()
        self.visitedLocationVisited = set()

        self.goal = namedtuple("Goal", ["mapBank", "mapNum", "reward"])
    
        self.InitGoalMaps()
    
    def CheckTileRecord(self, currentPosition):
        # currentPosition is a tuple (x, y, mapNum, mapBank)
        if currentPosition not in self.visitedTiles:
            self.reward += 1
            self.visitedTiles.add(currentPosition)

    def CheckMapGoal(self, currentPosition):
        # currentPosition is a tuple (x, y, mapBank, mapNum)
        mapBank = currentPosition[2]
        mapNum = currentPosition[3]
        
        # Iterate over a copy since we're modifying the set
        for location in list(self.pendingGoalLocation):
            if mapNum == location.mapNum and mapBank == location.mapBank:
                self.reward += location.reward
                self.visitedLocationVisited.add(location)
                self.pendingGoalLocation.remove(location)
                break
    
    # If AI hasn't used an action for the past 1000 frames, it will start losing 0.1 per frame - Unused atm
    # Unused because I don't have a good way of checking if frames are advancing
    def IncreaseInactivityTimer(self):
        self.framesNotMoving += 1
        if self.framesNotMoving > 1000:
            self.reward -= 0.1

    def ResetInactivity(self): # Has to be called when an action is done
        self.framesNotMoving = 0

    def InitGoalMaps(self):
        self.pendingGoalLocation = {
            self.goal(mapBank = 0, mapNum = 16, reward = 50),
            self.goal(mapBank = 1, mapNum = 0, reward = 25)
        }

    def UpdateRewardAction(self, state):
        currentLocation = (state['x'], state['y'], state['mapBank'], state['mapNum'])
        self.CheckTileRecord(currentLocation)
        self.CheckMapGoal(currentLocation)
        self.reward -= 0.1 # Might be wrong to do this. Let's check.

        return self.reward
    
    # Unused atm.
    def UpdateRewardTick(self):
        self.IncreaseInactivityTimer()

    def GetReward(self):
        return self.reward

    def Reset(self):
        self.visitedTiles.clear()
        self.reward = 0
        self.framesNotMoving = 0
        self.visitedLocationVisited.clear()
        self.InitGoalMaps()

    #TODO: Fighting rewards


    
