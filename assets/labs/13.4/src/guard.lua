-- guard.lua: a simple license check script for practicing Lua decompiling
-- Build bytecode:  luac -o guard.luac guard.lua
-- Build + strip:   luac -s -o guard_strip.luac guard.lua
-- Decompile:       java -jar unluac.jar guard.luac > guard_out.lua

local function transform(s)
    local out = {}
    for i = 1, #s do
        local c = string.byte(s, i)
        out[i] = (c + i) % 256
    end
    return out
end

local EXPECTED = { 109, 119, 100, 99, 55, 54, 57, 60, 42 }

local function check(key)
    if #key ~= #EXPECTED then
        return false
    end
    local t = transform(key)
    for i = 1, #EXPECTED do
        if t[i] ~= EXPECTED[i] then
            return false
        end
    end
    return true
end

io.write("Enter license key: ")
local key = io.read("l")
if check(key) then
    print("Correct! Welcome.")
else
    print("Nope.")
end
