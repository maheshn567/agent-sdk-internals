import asyncio
from corsair_mcp import create_corsair_session

async def main():
    print("Hello from simpleagent!")
    print("Connecting to MCP infrastructure...")
    corsair_session, corsair_transport = await create_corsair_session()
    
    # List and print tools to verify connection works
    tools = await corsair_session.list_tools()
    print("Successfully connected! Available tools:")
    for tool in tools.tools:
        print(f"- {tool.name}")
        
    # Clean up session and transport
    await corsair_session.__aexit__(None, None, None)
    await corsair_transport.__aexit__(None, None, None)

if __name__ == "__main__":
    asyncio.run(main())
