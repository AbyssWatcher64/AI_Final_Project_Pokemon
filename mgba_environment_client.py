#!/usr/bin/env python3
#Python client for controlling Pokémon Emerald in mGBA through Lua scripting

import socket
import sys
from typing import Optional, Dict

class MGBAEnvironment:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False

        self.actions = ["UP", "LEFT", "DOWN", "RIGHT", "A", "B",
                        "START", "SELECT", "L", "R"]

    # Connect to the mGBA Lua Server
    def Connect(self) -> bool: 
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10.0)
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
        if self.sock:
            self.sock.close()
            self.sock = None
            self.connected = False
            print("Disconnected from mGBA.")

    # Send a command to the Lua script and receive a response
    def SendCommand(self, command: str) -> Optional[str]:
        if not self.sock:
            print("Unable to send command. Not connected to the Lua server!")
            return None
        try:
            self.sock.send(f"{command}\n".encode('utf-8'))
            response = self.sock.recv(1024).decode('utf-8').strip()
            return response
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
        return self.ParseState(response)
    
    # Get current state without taking an action
    def GetState(self) -> Dict:
        response = self.SendCommand("GETSTATE")
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
            if len(data) == 6:
                return {
                    "x": int(data[0]),
                    "y": int(data[1]),
                    "mapBank": int(data[2]),
                    "mapNum": int(data[3]),
                    "isInBattle": data[4].lower() == "true",
                    "isDone": data[5].lower() == "true"
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

def PrintCommands():
    print("\n=== Commands ===")
    print("  w/a/s/d - Move up/left/down/right")
    print("  x - Press A button")
    print("  z - Press B button")
    print("  enter - Start button")
    print("  space - Select button")
    print("  r - R button")
    print("  l - L button")
    print("  p - Print current state")
    print("  q - Quit")
    print("\n=== Debug Commands ===")
    print("  h - Print commands")
    print("  ping - Ping the server")
    print("  reset - Reset state to savestate")
    print("\nPress keys to control (press Enter after each):")


# Start inputting commands
def InputCommandLoop(env):
    PrintCommands()
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

    while True:
        try:
            key = input("> ").lower()

            if key == "q":
                break

            if key == "p":
                state = env.GetState()
                print(f"State: {state}")
            elif key == "h":
                PrintCommands()
            elif key == "ping":
                env.DebugPrint()
            elif key == "reset":
                if env.Reset():
                    print("Received RESET_OK from server.")
            elif key in keyMap:
                action = keyMap[key]
                state = env.Step(action)
                print(f"State: {state}")
            else:
                print("Unknown command.")

        except KeyboardInterrupt:
            break

def main():
    print("Pokémon Emerald Remote Environment")
    print("=" * 40)

    env = MGBAEnvironment()

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

