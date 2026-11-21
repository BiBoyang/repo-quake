import json
import sys

# A stdio MCP server (classic handshake, no tools) that answers at once and
# exits when its stdin closes.
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except ValueError:
        continue
    rid = msg.get("id")
    method = msg.get("method")
    if rid is None:
        continue
    if method == "initialize":
        result = {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                  "serverInfo": {"name": "s", "version": "1"}}
        reply = {"jsonrpc": "2.0", "id": rid, "result": result}
    elif method == "tools/list":
        reply = {"jsonrpc": "2.0", "id": rid, "result": {"tools": []}}
    elif method == "ping":
        reply = {"jsonrpc": "2.0", "id": rid, "result": {}}
    else:
        reply = {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "Method not found"}}
    sys.stdout.write(json.dumps(reply) + "\n")
    sys.stdout.flush()
