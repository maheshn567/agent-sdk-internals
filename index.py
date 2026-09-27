import asyncio
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client


load_dotenv()

def load_agent_skill(file_path="skill.md"):
    """Reads the skill.md file and splits frontmatter metadata from the core playbook instructions."""
    if not os.path.exists(file_path):
        print(f"Warning: {file_path} not found.")
        return None, ""
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Basic frontmatter parser for markdown files
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            playbook_text = parts[2].strip()
            
            # Simple parse for name and description lines
            metadata = {}
            for line in raw_yaml.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
            return metadata, playbook_text
            
    return None, content

async def main():
    current_dir = os.getcwd()
    
    # Load skill playbook
    metadata, playbook_instructions = load_agent_skill("skill.md")
    
    # 1. Setup MCP parameters
    api_key = os.getenv("smithery_api_key")
    if not api_key:
        print("Error: No smithery_api_key found.")
        return

    remote_url = f"https://server.smithery.ai/theagenttimes/news?api_key={api_key}"
    fs_server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "-v", f"{current_dir}:/workdir", "ghcr.io/mark3labs/mcp-filesystem-server:latest", "/workdir"]
    )
    calc_server_params = StdioServerParameters(command=".venv/bin/python", args=["server.py"])
    corsair_params = StdioServerParameters(
        command="npx",
        args=["tsx", "corsair-server/src/server.ts"],
        env={
            **os.environ,
            "DOTENVX_LOG_LEVEL": "error",
            "DOTENV_CONFIG_QUIET": "true",
        }
    )
    userbot_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["telegarm_mcp.py"]
    )

    # 2. Establish connections to MCP servers
    print("Connecting to MCP infrastructure...")
    async with streamablehttp_client(remote_url) as (news_read, news_write, _), \
               stdio_client(fs_server_params) as (fs_read, fs_write), \
               stdio_client(calc_server_params) as (calc_read, calc_write), \
               stdio_client(corsair_params) as (corsair_read, corsair_write), \
               stdio_client(userbot_params) as (userbot_read, userbot_write): 
               
        async with ClientSession(news_read, news_write) as news_session, \
                   ClientSession(fs_read, fs_write) as fs_session, \
                   ClientSession(calc_read, calc_write) as calc_session, \
                   ClientSession(corsair_read, corsair_write) as corsair_session, \
                   ClientSession(userbot_read, userbot_write) as userbot_session:
            
            await news_session.initialize()
            await fs_session.initialize()
            await calc_session.initialize()
            await corsair_session.initialize()
            await userbot_session.initialize()

            # Dynamic tool aggregation
            tool_to_session = {}
            tools = []

            for session, name_tag in [
                (news_session, "News"), 
                (fs_session, "FS"), 
                (calc_session, "Calc"), 
                (corsair_session, "Corsair"),
                (userbot_session, "Userbot")
            ]:
                result = await session.list_tools()
                for tool in result.tools:
                    tool_to_session[tool.name] = session
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                    })

            # Initialize messages with the dynamic skill injection
            # This is where the LLM reads and adapts to your operational playbook!
            messages = []
            if playbook_instructions:
                messages.append({
                    "role": "system",
                    "content": (
                        "You are an AI Agent operating with an active execution skill.\n"
                        f"Active Skill Profile: {metadata.get('name', 'Default Orchestrator') if metadata else 'Default Orchestrator'}\n"
                        f"Skill Guidelines:\n{playbook_instructions}"
                    )
                })
            messages.append({
                "role": "user", 
                "content": "Use the TelegramUserbot run_telethon_code tool to send a message to the recipient '+919591372601' with the text 'Sathish muthmare'"
            })

            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=os.getenv("nemotron_api_key")
            )

            print(f"\nUser Query: {messages[-1]['content']}\n")

            # 4. LLM Loop (Proper multi-turn tracking)
            while True:
                response = client.chat.completions.create(
                    model="nvidia/nemotron-3-ultra-550b-a55b",
                    messages=messages,
                    tools=tools,
                    temperature=0.3,
                    max_tokens=1024
                )

                message = response.choices[0].message
                messages.append(message) # Commit LLM turn to history

                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        print(f"Executing tool: {tool_name}")
                        target_session = tool_to_session.get(tool_name)
                        
                        if target_session:
                            tool_result = await target_session.call_tool(tool_name, arguments=args)
                            content_text = "".join(
                                b.text if hasattr(b, 'text') else str(b) for b in tool_result.content
                            )
                        else:
                            content_text = f"Error: Tool {tool_name} session missing."
                                
                        print(f"Tool Result:\n{content_text}\n")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": content_text
                        })
                else:
                    print("=== FINAL SKILL-ADAPTED RESPONSE ===")
                    print(message.content)
                    break

if __name__ == "__main__":
    asyncio.run(main())