#!/usr/bin/env python3
#Python client for controlling Pokémon Emerald in mGBA through Lua scripting

import socket
import sys
from typing import Optional, Dict
from random import randrange # For stress testing
from datetime import datetime # for csv file logging
import csv # for csv file logging
import os # for folder creation

class MGBAEnvironment:
    def __init__(self, host='localhost', port=8888, logFile=None):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.logFile = logFile
        self.csvWriter = None
        self.csvFileHandle = None

        self.isDone = False

        self.actions = ["UP", "LEFT", "DOWN", "RIGHT", "A", "B",
                        "START", "SELECT", "L", "R"]
        self.lastAction = None

        # === Uncomment these lines for deterministic test ===
        self.deterministicActions = [0] * 500
        for x in range(500):
            self.deterministicActions[x] = randrange(len(self.actions))
        self.deterministicActionCounter = 0
        # === /Deterministic test ===
        
        if self.logFile:
            self.InitializeCSVLog()

    # Connect to the mGBA Lua Server
    def Connect(self) -> bool: 
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            # Wait for connection message
            response = self.sock.recv(1024).decode('utf-8')
            print(f"Connected to mGBA: {response.strip()}")
            self.connected = True
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    # Disconnect from server    
    def Disconnect(self):
        if self.csvFileHandle:
            self.csvFileHandle.close()
            print(f"Closed log file: {self.logFile}")
        
        if self.sock:
            self.sock.close()
            self.sock = None
            self.connected = False
            print("Disconnected from mGBA.")

    # Initialize CSV file with headers
    def InitializeCSVLog(self):
        try:
            import os
            fullPath = os.path.abspath(self.logFile)
            print(f"Creating log file at: {fullPath}")
            
            self.csvFileHandle = open(self.logFile, 'w', newline='')
            self.csvWriter = csv.writer(self.csvFileHandle)
            # Write header
            self.csvWriter.writerow(['inputtedAction', 'x', 'y', 'mapBank', 'mapNum', 
                                    'isInBattle', 'isDone', 'executedStep', 'currentSteps'])
            self.csvFileHandle.flush()  # Ensure header is written immediately
            print(f"Successfully created log file: {self.logFile}")
        except Exception as e:
            print(f"Failed to initialize CSV log: {e}")
            self.csvWriter = None

    # Log state to CSV file
    def LogState(self, state: Dict, action):
            if self.csvWriter and not state.get('error', False):
                try:
                    self.csvWriter.writerow([
                        action,
                        state.get('x', -1),
                        state.get('y', -1),
                        state.get('mapBank', -1),
                        state.get('mapNum', -1),
                        state.get('isInBattle', False),
                        state.get('isDone', False),
                        state.get('lastAction', 'UNKNOWN'),
                        state.get('currentSteps', -1)
                    ])
                    self.csvFileHandle.flush()  # Write immediately
                except Exception as e:
                    print(f"Failed to log state: {e}")


    # Send a command to the Lua script and receive a response
    def SendCommand(self, command: str) -> Optional[str]:
        if not self.sock:
            print("Unable to send command. Not connected to the Lua server!")
            return None
        try:
            self.sock.send(f"{command}\n".encode('utf-8'))
            response = self.sock.recv(1024).decode('utf-8').strip()
            return response
        except socket.timeout:
            print(f"Command timed out: {command}")
            return None
        except Exception as e:
            print(f"Send failed: {e}")
            return None
    
    # Take one step in the environment
    # Action should be one of the self.actions (UP, DOWN, LEFT, RIGHT, A, B, etc.)
    # Returns dictionary containing the new stat (x, y, mapGroup, mapNum, etc.)
    def Step(self, action: str) -> Dict:
        action = action.upper()
        if action not in self.actions:
            print(f"Invalid action: {action}")
            print(f"Valid actions: {self.actions}")
            return self.GetErrorState() 
        
        response = self.SendCommand(f"STEP:{action}")
        state = self.ParseState(response)
        self.LogState(state, action) 
        return self.ParseState(response)
    
    # Get current state without taking an action
    def GetState(self) -> Dict:
        response = self.SendCommand("GETSTATE")
        state = self.ParseState(response)
        self.LogState(state)
        return self.ParseState(response)
        
    # Reset the environment        
    def Reset(self) -> bool:
        response = self.SendCommand("RESET")
        return response == "RESET_OK"
    
    # Parse state response from server
    def ParseState(self, response: Optional[str]) -> Dict:  
        if not response:
            return self.GetErrorState()
        
        if response.startswith("ERROR:"):
            print(f"Server error: {response}")
            return self.GetErrorState()

        if not response.startswith("STATE:"):
            return self.GetErrorState()
        
        # Parse: State:x,y,mapGroup,mapNum,isInBattle,isDone
        try:
            data = response[6:].split(",")
            if len(data) == 8:
                self.isDone = data[5].lower() == "true"
                return {
                    "x": int(data[0]),
                    "y": int(data[1]),
                    "mapBank": int(data[2]),
                    "mapNum": int(data[3]),
                    "isInBattle": data[4].lower() == "true",
                    "isDone": data[5].lower() == "true",
                    "lastAction": data[6].upper(),
                    "currentSteps": int(data[7])
                }
        except Exception as e:
            print(f"Failed to parse state: {e}")

        return self.GetErrorState()

    # Return an error state
    def GetErrorState(self) -> Dict:
        print("Error state at the frame of this printing.")
        return {
            "x": -1,
            "y": -1,
            "mapBank": -1,
            "mapNum": -1,
            "isInBattle": False,
            "isDone": False,
            "lastAction": "UNKNOWN_CLIENT",
            "error": True
        }

    # Test connection with a ping
    def Ping(self) -> bool:
        response = self.SendCommand("PING")
        return response == "PONG"
    
    def DebugPrint(self):
        print("\nAttempting to ping from Python client...")
        if self.Ping():
            print("Received a ping response from Lua server.\n")

# Start inputting commands
def InputCommandLoop(env):
    keyMap = {
        "w": "UP",
        "a": "LEFT",
        "s": "DOWN",
        "d": "RIGHT",
        "x": "A",
        "z": "B",
        "": "START",
        " ": "SELECT",
        "r": "R",
        "l": "L"
    }

    # Resetting to start always at the same position
    env.Reset()

    while True:
        while not env.isDone:
            try:
                # === Uncomment these lines for deterministic test ===
                action = env.actions[env.deterministicActions[env.deterministicActionCounter]]
                state = env.Step(action)
                env.deterministicActionCounter = env.deterministicActionCounter + 1
                print(f"Action: {action}, State: {state}")
                # === /Deterministic test ===

            except KeyboardInterrupt:
                break

        if env.isDone:
            print("==========================")
            print("Goal completed or bot softlocked. RESETTING")

            if env.csvFileHandle:
                env.csvFileHandle.close()
                print(f"Closed log file: {env.logFile}")

            # === Uncomment these lines for deterministic test ===
            env.deterministicActionCounter = 0
            env.isDone = False
            # === /Deterministic test ===

            env.logFile = f"Logging/pokemon_log_{datetime.now().strftime('%Y%m%d')}/pokemon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            env.InitializeCSVLog()

            if env.Reset():
                print("Received RESET_OK from server.")        

def main():
    print("Pokémon Emerald Remote Environment")
    print("=" * 40)

    directory = f"Logging/pokemon_log_{datetime.now().strftime('%Y%m%d')}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    logFileName = f"Logging/pokemon_log_{datetime.now().strftime('%Y%m%d')}/pokemon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    env = MGBAEnvironment(logFile=logFileName)

    print("Connecting to mGBA...")
    if not env.Connect():
        print("Make sure mGBA is running with the Lua script loaded!")
        sys.exit(1)

    # Test connection
    try:
        if not env.Ping():
            print("Ping failed!")
            sys.exit(1)

        InputCommandLoop(env)
    
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    
    finally:
        env.Disconnect()


if __name__ == "__main__":
    main()

