-- This is the mGBA Lua Script for python Remote Control (or anything that can connect to it)
-- Load this script in mGBA through Tools -> Scripting

console:log("Starting remote control server...")

-- Configuration
local port = 8888 -- localhost
local server = nil
local client = nil

-- === MEMORY ADDRESSES ===
-- Memory addresses for Pokémon Emerald (US v1.0)
-- These addresses may change from ROM to ROM
-- The most important resource for all of this is the
-- dissassembly of Pokémon Emerald: https://github.com/pret/pokeemerald/tree/master
-- This can be expanded as necessary
-- === HOW MEMORY WORKS ===
-- Memory can change because it is dynamic, and each time you save, the memory moves.
-- However, there's a pointer for the save slot, and we know certain elements have an
-- offset in RAM given the save slot pointer. Thus, we check the save slot, and sum 
-- certain hexadecimal values to retrieve certain things.
local SAVE_BLOCK1_PTR = 0x03005D8C  -- Pointer to SaveBlock1
local PLAYER_X_OFFSET = 0x00        -- X position offset in SaveBlock1
local PLAYER_Y_OFFSET = 0x02        -- Y position offset in SaveBlock1
local MAP_BANK_OFFSET = 0x04        -- Map bank offset in SaveBlock1 -> Bank = Folder of map. EG: Bank 3 = Littleroot Town Area
local MAP_NUM_OFFSET = 0x05         -- Map number offset in SaveBlock1 -> Map = Specific map in a bank. EG: Bank 3, Map 0: Littleroot Town. Bank 3, Map 1: Professor Birch's Lab.
local BATTLE_FLAG = 0x02022B4C

-- Action queue for step-based control
local pendingAction = nil
local actionFramesRemaining = 0
local actionKey = nil

-- Done variables
local MAX_STEPS = 500 -- This is to give a done condition
local MAX_STEPS_SOFTLOCK = 200 -- This is to prevent the bot from softlocking
local currentSteps = 0
local currentSoftLockSteps = 0
local prevLocation = nil

-- Save / Load variables
local saveState = script.dir .. "/Rom_and_Saves/pokemon_emerald.ss1"

-- Key mapping - Using mGBA Constant files
-- Check this for more information: https://mgba.io/docs/scripting.html#constants
local keyMap =
{
    UP = C.GBA_KEY.UP,
    DOWN = C.GBA_KEY.DOWN,
    LEFT = C.GBA_KEY.LEFT,
    RIGHT = C.GBA_KEY.RIGHT,
    A = C.GBA_KEY.A,
    B = C.GBA_KEY.B,
    START = C.GBA_KEY.START,
    SELECT = C.GBA_KEY.SELECT,
    L = C.GBA_KEY.L,
    R = C.GBA_KEY.R
}

-- Step configuration - These can be adjusted for faster / slower training
local FRAMES_PER_STEP = 15
local STABILIZATION_FRAMES = 5

-- Function to check if player is in battle
local function IsInBattle()
    local battleFlag = emu:read8(BATTLE_FLAG)
    return battleFlag ~= 0
end

-- TODO: Add condition for when episode is done (probably reaching a place)
local function IsDone(playerLocation)
    if (playerLocation.mapBank == 1 and playerLocation.mapNum == 0)
        or playerLocation.mapNum == 16 then
        return true
    end
    if currentSteps >= MAX_STEPS then
        console:log("Reached MAX Steps.")
        return true
    end
    if currentSoftLockSteps >= MAX_STEPS_SOFTLOCK then
        console:log("Reached MAX SOFTLOCK Steps.")
        return true
    end
    return false
end

-- Function to read player location data
local function GetPlayerLocation()
    -- Read the pointer to SaveBlock1
    local saveBlock1Ptr = emu:read32(SAVE_BLOCK1_PTR)

    if saveBlock1Ptr == 0 or saveBlock1Ptr < 0x02000000 or saveBlock1Ptr > 0x0203FFFF then
        return nil
    end

    -- Read player coordinates and map info
    -- You can find what type of constants each is (if x position is 16 bits, 
    -- you should get those, no more, no less) in this link: 
    -- https://github.com/pret/pokeemerald/blob/master/include/global.h
    local playerX = emu:read16(saveBlock1Ptr + PLAYER_X_OFFSET)
    local playerY = emu:read16(saveBlock1Ptr + PLAYER_Y_OFFSET)
    local mapBank = emu:read8(saveBlock1Ptr + MAP_BANK_OFFSET)
    local mapNum = emu:read8(saveBlock1Ptr + MAP_NUM_OFFSET)
    
    return 
    {
        x = playerX,
        y = playerY,
        mapBank = mapBank,
        mapNum = mapNum
    }
end

local function CheckLocationSoftlock(location)
    if prevLocation and 
       location.x == prevLocation.x and 
       location.y == prevLocation.y and
       location.mapBank == prevLocation.mapBank and
       location.mapNum == prevLocation.mapNum then
        currentSoftLockSteps = currentSoftLockSteps + 1
    else
        currentSoftLockSteps = 0
    end

    prevLocation = {
        x = location.x,
        y = location.y,
        mapBank = location.mapBank,
        mapNum = location.mapNum
    }
end

-- Function to get current state
local function GetState()
    local location = GetPlayerLocation()

    if not location then
        return {
            x = -1,
            y = -1,
            mapGroup = -1,
            mapNum = -1,
            isInBattle = false,
            isDone = false,
            pendingAction = "UNKNOWN_SERVER",
            currentSteps = -1,
            error = true
        }
    end

    CheckLocationSoftlock(location)

    return {
        x = location.x,
        y = location.y,
        mapBank = location.mapBank,
        mapNum = location.mapNum,
        isInBattle = IsInBattle(),
        isDone = IsDone(location),
        pendingAction = pendingAction,
        currentSteps = currentSteps,
        error = false
    }
end

local function ResetVariables()
    currentSteps = 0
    pendingAction = nil
    actionFramesRemaining = 0
    actionKey = nil
end

-- Function to execute a step (action + wait + get state)
local function ExecuteStep(action)
    local keyCode = keyMap[action]

    if not keyCode then
        console:error("Invalid action: " .. action)
        return nil
    end

    -- Queue the action instead of executing immediately
    pendingAction = action
    actionKey = keyCode
    actionFramesRemaining = FRAMES_PER_STEP + STABILIZATION_FRAMES  -- Action frames + stabilization frames
    currentSteps = currentSteps + 1
    
    console:log("Queued step: " .. action)
    return true
end

-- Process queued action (called each frame)
local function ProcessQueuedAction()
    if actionFramesRemaining > 0 then
        -- Hold the key down during the action period
        if actionFramesRemaining > STABILIZATION_FRAMES then
            if actionKey then
                emu:addKey(actionKey)  -- Add key EVERY frame during action
            end
        end
        
        -- Clear the key during stabilization
        if actionFramesRemaining <= STABILIZATION_FRAMES then
            if actionKey then
                emu:clearKey(actionKey)
            end
        end

        actionFramesRemaining = actionFramesRemaining - 1

        if actionFramesRemaining == 0 and client and pendingAction then
            local state = GetState()
            local response = string.format("STATE:%d,%d,%d,%d,%s,%s,%s,%d\n",
                                            state.x, state.y, state.mapBank, state.mapNum,
                                            state.isInBattle and "true" or "false",
                                            state.isDone and "true" or "false",
                                            pendingAction,
                                            currentSteps)
            console:log("Action completed, sending: " .. response:gsub("\n", ""))
            client:send(response)
            pendingAction = nil
            actionKey = nil
        end
    end
end

-- Process commands from client
local function ProcessCommand(cmd)
    cmd = cmd:gsub("%s+", "")

    if cmd == "" then
        return
    end

    -- Parse command format: PRESS:KEY or RELEASE:KEY or CLEAR or GETPOS
    -- Therefore the following regex finds these two possible kinds of formats
    -- If colon is found, then the string is divided into action (PRESS) and key (KEY)
    local action, key = cmd:match("([^:]+):?(.*)")

    -- ~= is the same as !=
    -- Queue the step (response will be sent when action completes)
    if action == "STEP" and key ~= "" then
        if actionFramesRemaining > 0 then
            -- Action already in progress - reject the new one
            if client then
                client:send("ERROR:ACTION_IN_PROGRESS\n")
            end
            console:log("Rejected action, one already in progress")
        else
            ExecuteStep(key)
        end
        
    elseif action == "GETSTATE" then
        -- Just return current state without taking action
        local state = GetState()
        if client then
            local response = string.format("STATE:%d,%d,%d,%d,%s,%s,%s,%d\n",
                state.x, state.y, state.mapBank, state.mapNum,
                state.isInBattle and "true" or "false",
                state.isDone and "true" or "false",
                pendingAction,
                currentSteps)
            client:send(response)
        end
        
    elseif action == "RESET" then
        -- Clear all keys and reload save state
        emu:clearKeys(0xFFFFFFFF)
        ResetVariables()
    
        -- Use a oneshot callback to load the state in a valid context
        callbacks:oneshot("frame", function()
            local result = emu:loadStateFile(saveState)
            
            if result then
                console:log("Environment reset successfully.")
                -- Wait one more frame before sending response
                callbacks:oneshot("frame", function()
                    if client then
                        client:send("RESET_OK\n")
                    end
                end)
            else
                console:error("Failed to load save state!")
                if client then
                    client:send("ERROR:RESET_FAILED\n")
                end
            end
        end)
        
    elseif action == "PING" then
        if client then
            client:send("PONG\n")
        end
    end
end

-- Initialize server
local function InitServer()
    server = socket.bind(nil, port)
    if server then
        server:listen(1)
        console:log("Server listening on port " .. port .. ".")
        return true
    else
        console:error("Server failed to bind to port " .. port .. ".")
        return false
    end
end

-- Accept client connection
local function AcceptClient()
    if not client and server then
        local newClient, err = server:accept()
        if newClient then
            client = newClient
            console:log("Client connected!")
            -- Send welcome message to Python
            client:send("You've successfully connected to the mGBA Lua script.\n")
        end
    end
end

-- Handle Client communication
local function HandleClient()
    if client then
        -- Try to receive data (non-blocking)
        local data, err = client:receive(1024)

        if data then
            -- Successfully received data, process it
            for cmd in data:gmatch("[^\n]+") do
                ProcessCommand(cmd)
            end
        elseif err then
            -- Error occurred - check if it's just "no data available" or if it's an actual disconnect
            -- SOCKERR.OK (0) and SOCKERR.AGAIN (1) both mean no data available, keep connection
            if err ~= socket.ERRORS[0] and err ~= socket.ERRORS[1] and
               err ~= "timeout" and err ~= "wantread" then
                console:log("Client disconnected.\n")
                client = nil
            end
        end
    end
end

-- Initialize server
if not InitServer() then
    console:error("Failed to initialize server. Script stopping.")
    return 
end

-- Frame callback - runs every frame
callbacks:add("frame", function() AcceptClient() HandleClient() ProcessQueuedAction() end)

console:log("Remote control script loaded succesfully!")
console:log("Awaiting a Python Client to connect on port " .. port .. "...")