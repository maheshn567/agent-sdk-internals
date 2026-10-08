import asyncio
import sys
import os
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client

# Suppress background library log noise (MCP, Telethon, HTTPX, etc.)
logging.basicConfig(level=logging.WARNING)
for logger_name in ["mcp", "telethon", "httpx", "httpcore", "asyncio"]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# 1. Load environment variables from .env file
load_dotenv()

# 2. Correctly initialize the Nvidia/Nemotron OpenAI Client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("nemotron_api_key")
)

# 3. Define the Orchestrator Router instructions
SYSTEM_MESSAGE = """
You are the Orchestrator Router. Your job is to analyze the user's prompt and delegate tasks to the appropriate specialized sub-agents.
You DO NOT call standard MCP tools yourself; you must delegate work to:
1. delegate_to_communications_agent(task_description): For email, GitHub, and Telegram tasks.
2. delegate_to_analyst_agent(task_description): For file reading/writing and calculations.

Once the sub-agents report their output, integrate their findings into a clean, minimal final answer.
"""

# 4. Define connection parameters for all sub-services
current_dir = os.getcwd()
api_key = os.getenv("smithery_api_key")
remote_url = f"https://server.smithery.ai/theagenttimes/news?api_key={api_key}"

fs_server_params = StdioServerParameters(
    command=".venv/bin/python",
    args=["E2B_sandbox.py"]
)
calc_server_params = StdioServerParameters(
    command=".venv/bin/python", 
    args=["server.py"]
)
corsair_params = StdioServerParameters(
    command="npx",
    args=["tsx", "corsair-server/src/server.ts"],
    env={**os.environ, "DOTENVX_LOG_LEVEL": "error", "DOTENV_CONFIG_QUIET": "true"}
)
userbot_params = StdioServerParameters(
    command=".venv/bin/python",
    args=["telegarm_mcp.py"]
)

async def main():
    print("Connecting to MCP infrastructure...")
    # Open connections to all 5 servers
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
            
            # Initialize connection handshake
            await news_session.initialize()
            await fs_session.initialize()
            await calc_session.initialize()
            await corsair_session.initialize()
            await userbot_session.initialize()

            print("All MCP connections initialized successfully!")


            # 5. Dynamic tool extraction helper function
            async def get_formatted_tools(target_sessions):
                formatted_tools = []
                tool_to_session = {}
                for session in target_sessions:
                    result = await session.list_tools()
                    for tool in result.tools:
                        tool_to_session[tool.name] = session
                        formatted_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.inputSchema
                            }
                        })
                return formatted_tools, tool_to_session

            # 6. Specialized Agent Loop Runner
            async def run_worker_agent(system_prompt, task, target_sessions):
                # Retrieve tools only for the sessions assigned to this worker
                worker_tools, tool_to_session = await get_formatted_tools(target_sessions)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task}
                ]
                
                while True:
                    response = client.chat.completions.create(
                        model="nvidia/nemotron-3-ultra-550b-a55b",
                        messages=messages,
                        tools=worker_tools if worker_tools else None,
                        temperature=0.2,
                        max_tokens=1024
                    )
                    message = response.choices[0].message
                    messages.append(message)
                    
                    if message.tool_calls:
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments)
                            
                            target_session = tool_to_session.get(tool_name)
                            if target_session:
                                tool_result = await target_session.call_tool(tool_name, arguments=args)
                                content_text = "".join(
                                    b.text if hasattr(b, 'text') else str(b) for b in tool_result.content
                                )
                            else:
                                content_text = f"Error: Tool {tool_name} not available in worker session."
                                
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": content_text
                            })
                    else:
                        # Return the worker's final conclusion text
                        return message.content

                        # 7. Define System Prompts for Worker Agents
            COMM_AGENT_PROMPT = """
            You are the Communications Specialist. You are responsible for Gmail, GitHub, and Telegram tasks.
            Analyze the user's task description, execute the required tools to perform it, and return a summary of what you did.
            """

            ANALYST_AGENT_PROMPT = """
            You are the Technical Analyst. You are responsible for reading/writing local files and running calculations.
            Analyze the user's task description, execute the required tools to perform it, and return a summary of the results.
            """

            # 8. Define Orchestrator Tools (Delegation Methods)
            orchestrator_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "delegate_to_communications_agent",
                        "description": "Delegates communication tasks (like sending emails, Telegram messages, or managing GitHub) to the Communications Agent.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_description": {
                                    "type": "string",
                                    "description": "Specific task description for the Communications Agent to perform."
                                }
                            },
                            "required": ["task_description"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "delegate_to_analyst_agent",
                        "description": "Delegates local files operations, reading/writing files, or calculation operations to the Analyst Agent.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "task_description": {
                                    "type": "string",
                                    "description": "Specific task description for the Analyst Agent to perform."
                                }
                            },
                            "required": ["task_description"]
                        }
                    }
                }
            ]

            # 9. Dynamic Orchestrator Query (from CLI arguments or interactive input)
            if len(sys.argv) > 1:
                user_query = " ".join(sys.argv[1:])
            else:
                user_query = input("\n📝 Enter task for Multi-Agent Orchestrator (or press Enter for default): ").strip()
                if not user_query:
                    user_query = "Run a python code block inside the E2B Sandbox that calculates the first 10 Fibonacci numbers, write the results to a file named 'fib.txt' in the sandbox, and then read the file contents using the Analyst Agent. After that, send the contents of 'fib.txt' to my personal Telegram account (using my chat ID 5734120490) using the Communications Agent."

            print(f"\n💬 [LLM Orchestrator Input]: {user_query}\n")

            messages = [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_query}
            ]

            # 10. Orchestrator Loop
            while True:
                response = client.chat.completions.create(
                    model="nvidia/nemotron-3-ultra-550b-a55b",
                    messages=messages,
                    tools=orchestrator_tools,
                    temperature=0.2,
                    max_tokens=1024
                )
                
                message = response.choices[0].message
                messages.append(message)
                
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        task_desc = args["task_description"]
                        
                        if tool_name == "delegate_to_communications_agent":
                            # Expose only the news, corsair, and userbot sessions to this worker
                            print(f"\n👑 [Orchestrator] Sending task to Communications Agent: '{task_desc}'")
                            result = await run_worker_agent(
                                system_prompt=COMM_AGENT_PROMPT,
                                task=task_desc,
                                target_sessions=[news_session, corsair_session, userbot_session]
                            )
                            
                        elif tool_name == "delegate_to_analyst_agent":
                            # Expose only the filesystem and calculator sessions to this worker
                            print(f"\n👑 [Orchestrator] Sending task to Analyst Agent: '{task_desc}'")
                            result = await run_worker_agent(
                                system_prompt=ANALYST_AGENT_PROMPT,
                                task=task_desc,
                                target_sessions=[fs_session, calc_session]
                            )
                        
                        print(f"💬 [Worker Report]:\n{result}\n")
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
                else:
                    print("\n👑 [Orchestrator] Final Integrated Response:")
                    print(message.content)
                    break

if __name__ == "__main__":
    asyncio.run(main())



