from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


import os

corsair_params = StdioServerParameters(
    command="npx",
    args=[
        "tsx",
        "corsair-server/src/server.ts"
    ],
    env={
        **os.environ,
        "DOTENVX_LOG_LEVEL": "error",
        "DOTENV_CONFIG_QUIET": "true",
    }
)


async def create_corsair_session():

    transport = stdio_client(corsair_params)

    read, write = await transport.__aenter__()

    session = ClientSession(read, write)

    await session.__aenter__()

    await session.initialize()

    return session, transport