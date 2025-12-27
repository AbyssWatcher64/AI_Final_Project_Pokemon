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

-- Current keys pressed
local currentKeys = 0

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
    if action == "PRESS" and key ~= "" then
        local keyCode = keyMap[key] -- Retrieve the value from keyMap
        if keyCode then
            emu:addKey(keyCode)
            console:log("Pressed: " .. key .. ".")
        end
    elseif action == "RELEASE" and key ~= "" then
        local keyCode = keyMap[key]
        if keyCode then
            emu:clearKey(keyCode)
            console:log("Released: " .. key .. ".")
        end
    elseif action == "CLEAR" then
        emu:setKeys(0)
        console:log("Cleared all keys.")
    elseif action == "GETPOS" then
        local location = GetPlayerLocation()
        if client and location then
            local response = string.format("POS:%d,%d,%d,%d\n", 
                    location.x, location.y, location.mapBank, location.mapNum)
            client:send(response)
            console:log(string.format("Sent position: X=%d Y=%d Bank=%d Map=%d",
                        location.x, location.y, location.mapBank, location.mapNum))
        elseif client then
            client:send("POS:ERROR\n")
            client:send("Unable to retrieve / read position")
        end
    elseif action == "PING" then
        if client then
            client:send("PONG\n")
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
callbacks:add("frame", function() AcceptClient() HandleClient() end)

console:log("Remote control script loaded succesfully!")
console:log("Awaiting a Python Client to connect on port " .. port .. "...")





