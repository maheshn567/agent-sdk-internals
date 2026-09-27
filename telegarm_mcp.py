import os
import sys
import asyncio
from mcp.server.fastmcp import FastMCP
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE") or os.getenv("PHONE")

# Initialize FastMCP Server
mcp = FastMCP("TelegramUserbot")

# Create Telethon client
client = TelegramClient("session_personal_user", API_ID, API_HASH)

@mcp.tool()
async def run_telethon_code(code: str) -> str:
    """
    Executes raw python code against the TelegramClient instance `client` asynchronously.
    The `client` object is already in scope.
    Use `await client.send_message(recipient, text)` or `await client.get_dialogs()` etc.
    Always use a return statement at the end of the block to send the output back.
    
    Example code:
    dialogs = await client.get_dialogs()
    return [d.name for d in dialogs[:5] if d.is_pinned]
    """
    if not client.is_connected():
        await client.connect()
        
    exec_globals = {
        "client": client,
        "asyncio": asyncio,
        "os": os
    }
    exec_locals = {}
    
    # Wrap the code in a temporary async function
    indented = "\n".join(f"    {line}" for line in code.splitlines())
    func_code = f"async def _temp_exec_fn():\n{indented}"
    
    try:
        exec(func_code, exec_globals, exec_locals)
        _temp_exec_fn = exec_locals["_temp_exec_fn"]
        res = await _temp_exec_fn()
        return str(res)
    except Exception as e:
        return f"Error executing Telethon code: {str(e)}"

if __name__ == "__main__":
    # If run with 'login' argument in terminal, perform authentication flow
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        print("Starting interactive Telegram login...")
        client.start(phone=PHONE)
        print("Login complete! Session file 'session_personal_user.session' created.")
        client.disconnect()
    else:
        # Run as MCP stdio server
        mcp.run()