import os
from mcp.server.fastmcp import FastMCP
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# Ensure E2B API Key is present
if not os.getenv("E2B_API_KEY"):
    raise ValueError("E2B_API_KEY is not set in the .env file.")

# 2. Create the FastMCP Server
mcp = FastMCP("E2B-Sandbox")

# 3. Create a persistent, secure remote sandbox instance
sandbox = Sandbox.create()

@mcp.tool()
def run_python_code(code: str) -> str:
    """
    Runs Python code inside the remote, secure sandboxed environment.
    Use this to perform heavy computations, data analysis, or run script blocks.
    Returns output logs (stdout/stderr) or error tracebacks.
    """
    try:
        execution = sandbox.run_code(code)
        output = []
        
        # Check standard output
        if execution.logs.stdout:
            for log in execution.logs.stdout:
                output.append(log)
                
        # Check standard error
        if execution.logs.stderr:
            for log in execution.logs.stderr:
                output.append(f"[stderr] {log}")
                
        # Check runtime errors
        if execution.error:
            output.append(f"[error] {execution.error.name}: {execution.error.value}\n{execution.error.traceback}")
            
        return "\n".join(output) if output else "Executed successfully (no output logs)."
    except Exception as e:
        return f"Error executing Python code: {str(e)}"

@mcp.tool()
def run_bash_command(command: str) -> str:
    """
    Runs a bash shell command inside the remote sandbox.
    Use this to run terminal utilities, compile code, or inspect virtual envs.
    """
    try:
        res = sandbox.commands.run(command)
        output = []
        if res.stdout:
            output.append(res.stdout)
        if res.stderr:
            output.append(f"[stderr] {res.stderr}")
        return "\n".join(output) if output else f"Command completed with exit code: {res.exit_code}"
    except Exception as e:
        return f"Error executing command: {str(e)}"

@mcp.tool()
def write_sandbox_file(path: str, content: str) -> str:
    """
    Writes a file at the specified path inside the remote sandbox.
    """
    try:
        sandbox.files.write(path, content)
        return f"Successfully wrote file at: {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def read_sandbox_file(path: str) -> str:
    """
    Reads a file from the specified path inside the remote sandbox.
    """
    try:
        content = sandbox.files.read(path)
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def list_sandbox_files(path: str = "/") -> str:
    """
    Lists the files and directories inside the specified path of the remote sandbox.
    """
    try:
        files = sandbox.files.list(path)
        result = []
        for f in files:
            details = f"Name: {f.name}"
            if getattr(f, "is_dir", False):
                details += " (directory)"
            else:
                details += f" (file, size: {getattr(f, 'size', 'unknown')} bytes)"
            result.append(details)
        return "\n".join(result) if result else "Directory is empty."
    except Exception as e:
        return f"Error listing files: {str(e)}"

if __name__ == "__main__":
    mcp.run()