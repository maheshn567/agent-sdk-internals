# Guide: Implementing a Telegram Personal Account Tool (Userbot)

To allow your AI Agent to act as a **personal Telegram account** (reading all your private chats, accessing pinned folders, and sending messages to anyone without needing a `/start` button), you must use Telegram's **MTProto Userbot API** instead of the Bot API.

---

## 1. How it Works (MTProto vs. Bot API)

| Feature | Bot API (Current) | Userbot API (Personal Account) |
| :--- | :--- | :--- |
| **Protocol** | HTTP REST | MTProto (TCP Sockets + Custom Encryption) |
| **Authentication** | Bot Token | API ID + API Hash + Phone Number (with SMS/App OTP) |
| **Initiate Chats** | No (User must send `/start` first) | **Yes** (Can message any username or phone number) |
| **Read Chats/Groups** | Only groups where bot is added | **Yes** (Reads all your personal groups, DMs, and channels) |
| **Access Pinned Chats** | No | **Yes** (Can read your pinned folders/chats) |

---

## 2. Steps to Get Credentials

To authenticate as a personal account, you need developer credentials from Telegram:

1. Go to [my.telegram.org](https://my.telegram.org) and log in with your personal Telegram phone number.
2. Go to **API development tools**.
3. Create a new application (you can name it whatever you like, e.g. "MyAIPlugin").
4. Copy your **`App api_id`** (integer) and **`App api_hash`** (string). Keep these secret!

---

## 3. Implementation Code Example (Python + Telethon)

The most popular Python library for MTProto is **Telethon**. You can install it via `pip install telethon`.

Here is a complete, working script showing how a personal userbot can connect, list your pinned chats, and send a message:

```python
import os
from telethon import TelegramClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE = os.getenv("TELEGRAM_PHONE")  # e.g., "+1234567890"

# The client will create a '.session' file locally to store authentication session keys
client = TelegramClient("session_personal_user", API_ID, API_HASH)

async def main():
    # Connect and sign in (will prompt you in the terminal for the OTP code on first run)
    await client.start(phone=PHONE)
    print("Successfully authenticated as personal account!")

    # 1. Fetch and print the first pinned chat/group name
    dialogs = await client.get_dialogs()
    pinned_dialogs = [d for d in dialogs if d.is_pinned]
    
    if pinned_dialogs:
        first_pinned = pinned_dialogs[0]
        print(f"\n📌 First Pinned Chat: '{first_pinned.name}' (ID: {first_pinned.id})")
    else:
        print("\n📌 No pinned chats found.")

    # 2. Send message to any user (even if they never messaged a bot)
    # You can specify username or phone number
    target_username = "rajesh_username"  # Replace with actual Telegram username
    print(f"\nSending message to @{target_username}...")
    
    try:
        await client.send_message(target_username, "Hello! Sent from my custom AI Userbot.")
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
```

---

## 4. How to Expose this to your AI Agent (MCP Server)

To integrate this Userbot into your main AI agent loop (`index.py`), you can create a custom **MCP Server** using the Python MCP SDK.

Create a new file `telegram_userbot_server.py`:

```python
from mcp.server.fastmcp import FastMCP
from telethon import TelegramClient
import os

# Initialize FastMCP Server
mcp = FastMCP("TelegramUserbot")

# Create Telethon client
client = TelegramClient("session_personal_user", int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))

@mcp.tool()
async def get_pinned_chats() -> str:
    """List all pinned chats and groups from your personal account."""
    if not client.is_connected():
        await client.connect()
    
    dialogs = await client.get_dialogs()
    pinned = [f"- {d.name} (ID: {d.id})" for d in dialogs if d.is_pinned]
    return "\n".join(pinned) if pinned else "No pinned chats found."

@mcp.tool()
async def send_user_message(recipient: str, text: str) -> str:
    """Send a text message to a user or group by username, phone number, or chat ID."""
    if not client.is_connected():
        await client.connect()
        
    try:
        await client.send_message(recipient, text)
        return f"Successfully sent message to {recipient}"
    except Exception as e:
        return f"Failed to send: {str(e)}"

if __name__ == "__main__":
    # Run the client loop to authenticate/start, then run MCP
    client.start(phone=os.getenv("TELEGRAM_PHONE"))
    mcp.run()
```

### Registered in `index.py`:
You can connect your agent to this new server in `index.py` by adding it to the Stdio connection list:
```python
userbot_server_params = StdioServerParameters(
    command=".venv/bin/python", 
    args=["telegram_userbot_server.py"]
)
```
Once connected, the AI agent will automatically detect `get_pinned_chats` and `send_user_message` tools and be able to control your personal Telegram account!
