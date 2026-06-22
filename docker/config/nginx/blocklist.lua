-- blocklist.lua: Redis-backed early IP rejection before Gunicorn.
-- ASN and User-Agent blocking are handled upstream by nginx if() blocks.
--
-- Checks (Redis DB 1, read-only):
--   1. ngx.shared.ip_prefix_blocked — in-process prefix cache (60s refresh, no Redis I/O)
--   2. GET rl:ip:{ip}:blocked        — global IP block
--   3. GET rl:api:ns:{ns}:ip:{ip}:blocked — per-tenant API block (/api/ only)
--
-- Checks 2+3 are pipelined in one Redis round trip.
-- On Redis failure: fail-open (request passes to Django).

local url = os.getenv("REDIS_URL") or "redis://127.0.0.1:6379"
local REDIS_HOST, port_str = url:match("redis://([^:/]+):(%d+)")
if not REDIS_HOST then REDIS_HOST = url:match("redis://([^:/]+)") or "127.0.0.1" end
local REDIS_PORT = tonumber(port_str) or 6379

local POD_NS = os.getenv("POD_NAMESPACE") or ""
local ip     = ngx.var.remote_addr
local is_api = ngx.var.uri:sub(1, 5) == "/api/"

-- Build 4 prefix candidates for ip e.g. '203.0.113.42':
--   '203.', '203.0.', '203.0.113.', '203.0.113.42'
-- Mirrors Django's _is_ip_prefix_blocked normalisation.
local parts = {}
for p in ip:gmatch("[^.]+") do parts[#parts+1] = p end
local p1 = parts[1] .. "."
local p2 = parts[1] .. "." .. parts[2] .. "."
local p3 = parts[1] .. "." .. parts[2] .. "." .. parts[3] .. "."

local function return_429()
    ngx.status = 429
    ngx.header["Retry-After"] = "300"
    ngx.header["Content-Type"] = "application/json"
    ngx.say('{"detail":"Too Many Requests"}')
    return ngx.exit(429)
end

-- 1. Prefix check (shared dict — zero Redis I/O per request).
local dict = ngx.shared.ip_prefix_blocked
if dict:get(p1) or dict:get(p2) or dict:get(p3) or dict:get(ip) then
    return return_429()
end

-- 2+3. Pipeline both STRING block checks in one Redis round trip.
local red = require("resty.redis"):new()
red:set_timeout(200)
local ok = red:connect(REDIS_HOST, REDIS_PORT)
if not ok then return end  -- fail-open

red:select(1)
red:init_pipeline()
red:get("rl:ip:" .. ip .. ":blocked")
red:get("rl:api:ns:" .. POD_NS .. ":ip:" .. ip .. ":blocked")
local res = red:commit_pipeline()
red:set_keepalive(10000, 1)

if not res then return end  -- fail-open on pipeline error

if res[1] == "1" then return return_429() end
if is_api and res[2] == "1" then return return_429() end
