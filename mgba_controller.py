#!/usr/bin/env python3
#Python client for controlling Pokémon Emerald in mGBA through Lua scripting

import socket
import time
import sys

class MGBAController:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.sock = None

    # Connect to the mGBA Lua Server
    def Connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            # Wait for connection message
            response = self.sock.recv(1024).decode('utf-8')
            print(f"Connected to mGBA: {response.strip()}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    # Disconnect from server    
    def Disconnect(self):
        if self.sock:
            self.ClearKeys()
            self.sock.close()
            self.sock = None
            print("Disconnected from mGBA")

    # Send a command to the Lua script
    def SendCommand(self, command):
        if not self.sock:
            print("Unable to send command. Not connected to the Lua server!")
            return False
        try:
            self.sock.send(f"{command}\n".encode('utf-8'))
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False
        
    # Press a key (keeps it held down)
    def PressKey(self, key):
        return self.SendCommand(f"PRESS:{key}")
    
    # Release a key
    def ReleaseKey(self, key):
        return self.SendCommand(f"RELEASE:{key}")
    
    # Release all keys
    def ClearKeys(self):
        return self.SendCommand("CLEAR")
    
    # Tap Key briefly
    def TapKey(self, key, duration=0.1):
        self.PressKey(key)
        time.sleep(duration)
        self.ReleaseKey(key)

    # Move in a direction for a duration
    def Move(self, direction, duration=0.5):
        validDirections = ["UP", "DOWN", "LEFT", "RIGHT"]
        if direction.upper() not in validDirections:
            print(f"Invalid direction: {direction}")
            return
        
        self.PressKey(direction.upper())
        time.sleep(duration)
        self.ReleaseKey(direction.upper())

    # Test connection with a ping
    def Ping(self):
        if self.SendCommand("PING"):
            try:
                response = self.sock.recv(1024).decode('utf-8').strip()
                return response == "PONG"
            except:
                return False
        return False
    
    # Get Player's Current position and Map information
    def GetPosition(self):
        if not self.sock:
            print("Not connected!")
            return None
        
        try:
            self.sock.send("GETPOS\n".encode('utf-8'))
            # Wait for response
            response = self.sock.recv(1024).decode('utf-8').strip()

            if response.startswith("POS:"):
                # Parse response: POS:x,y,mapBank,mapNum
                data = response[4:].split(',')
                if len(data) == 4:
                    return {
                    "x": int(data[0]),
                    "y": int(data[1]),
                    "mapBank": int(data[2]),
                    "mapNum": int(data[3])
                }
            elif response == "POS:ERROR":
                print("Failed to read position from game")
                return None
            return None
        except Exception as e:
            print(f"Get position failed: {e}")
            return None

# Demonstrate Basic Movement    
def DemoMovement(controller):
    print("\n=== Demo Movement Sequence ===")

    # Get Initial Position
    pos = controller.GetPosition()
    if pos:
        print(f"Starting position: X={pos['x']}, Y={pos['y']}, Bank={pos['mapBank']}, Map={pos['mapNum']}")

    # Move in a Square fashion: Up -> Right -> Down -> Left ->
    print("Moving UP...")
    controller.Move("UP", 1.0)
    time.sleep(0.5)

    pos = controller.GetPosition()
    if pos:
        print(f"Current position: X={pos['x']}, Y={pos['y']}, Bank={pos['mapBank']}, Map={pos['mapNum']}")

    print("Moving RIGHT...")
    controller.Move("RIGHT", 1.0)
    time.sleep(0.5)

    pos = controller.GetPosition()
    if pos:
        print(f"Current position: X={pos['x']}, Y={pos['y']}, Bank={pos['mapBank']}, Map={pos['mapNum']}")

    print("Moving DOWN...")
    controller.Move("DOWN", 1.0)
    time.sleep(0.5)

    pos = controller.GetPosition()
    if pos:
        print(f"Current position: X={pos['x']}, Y={pos['y']}, Bank={pos['mapBank']}, Map={pos['mapNum']}")

    print("Moving LEFT...")
    controller.Move("LEFT", 1.0)
    time.sleep(0.5)

    pos = controller.GetPosition()
    if pos:
        print(f"Final position: X={pos['x']}, Y={pos['y']}, Bank={pos['mapBank']}, Map={pos['mapNum']}")

    print("Demo complete!")

# Interactive Control Mode
def InteractiveMode(controller):
    print("\n=== Interactive Mode ===")
    print("Commands:")
    print("  w/a/s/d - Move up/left/down/right")
    print("  x - Press A button")
    print("  z - Press B button")
    print("  enter - Start button")
    print("  space - Select button")
    print("  r - R button")
    print("  l - L button")
    print("  p - Show current position")
    print("  q - Quit")
    print("\nPress keys to control (press Enter after each):")

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
                pos = controller.GetPosition()
                if pos:
                    print(f"Position: X={pos['x']}, Y={pos['y']}, Bank={pos['mapBank']}, Map={pos['mapNum']}")
                else:
                    print("Failed to get position.")
            elif key in keyMap:
                button = keyMap[key]
                print(f"Tapping {button}.")
                controller.TapKey(button, 0.2)
            else:
                print("Unknown command.")

        except KeyboardInterrupt:
            break

    controller.ClearKeys()

def main():
    print("Pokémon Emerald Remote Controller")
    print("=" * 40)

    controller = MGBAController()

    print("Connecting to mGBA...")
    if not controller.Connect():
        print("Make sure mGBA is running with the Lua script loaded!")
        sys.exit(1)

    # Test ping
    try:
        controller.Ping()

        # Choose mode
        print("\nSelect mode:")
        print("1. Demo movement sequence")
        print("2. Interactive control")
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == '1':
            DemoMovement(controller)
        elif choice == '2':
            InteractiveMode(controller)
        else:
            print("Invalid choice.")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    
    finally:
        controller.Disconnect()


if __name__ == "__main__":
    main()

