from mcp.server.fastmcp import FastMCP

# Create a FastMCP server instance
mcp = FastMCP("Calculator")

@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate a simple mathematical expression."""
    try:
        # Evaluate math expression safely (using simple eval with cleared builtins)
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    mcp.run()
