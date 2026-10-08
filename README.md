# Multi-Agent MCP Orchestration

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP Protocol](https://img.shields.io/badge/Model_Context_Protocol-MCP-black?logo=anthropic&logoColor=white)](https://modelcontextprotocol.io/)
[![NVIDIA AI](https://img.shields.io/badge/LLM-NVIDIA_Nemotron_3-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com/)
[![E2B Sandbox](https://img.shields.io/badge/Sandbox-E2B_Code_Interpreter-FF6B6B)](https://e2b.dev/)
[![Telethon](https://img.shields.io/badge/Telegram-MTProto_Userbot-26A5E4?logo=telegram&logoColor=white)](https://telethon.dev/)

A multi-agent system built on the Model Context Protocol (MCP), using an orchestrator that delegates work to scoped sub-agents rather than calling tools directly itself.

---

## Why this project

This was built to understand how agent SDKs work under the hood — specifically, how a tool-use harness wires an LLM to external tools, and how orchestrator/sub-agent delegation is actually implemented rather than treated as a black box.

Giving a single agent access to every tool at once causes two practical problems: the context window fills up with irrelevant tool schemas and results, and the agent can call tools well outside the scope of the task it's actually working on. This project addresses both by splitting work across an orchestrator and scoped worker agents connected over MCP.

Highlights:
- **Scoped sub-agents** — each worker only receives the tool sessions relevant to its domain, not the full tool set.
- **Async MCP transport handling** — stdio and streamable HTTP connections managed concurrently across 5 separate tool servers.
- **Remote sandboxed execution** — Python and shell code run inside an isolated E2B cloud container.
- **Dynamic skill/playbook loading** — markdown files with YAML frontmatter are parsed and injected into the system prompt at runtime, so agent behavior can change without touching code.
- **Personal-account Telegram automation** — uses the MTProto protocol (via Telethon) instead of the restricted Bot API.

---

## Architecture

An orchestrator agent reads the user's request and decides which worker(s) should handle it. It never calls a real tool itself — it only has two functions available: delegate to the communications worker, or delegate to the analyst worker. Each worker then runs its own independent tool-calling loop against the specific MCP sessions it was given, and returns a plain-text summary back to the orchestrator.

```mermaid
graph TD
    User(["User prompt"]) --> Orchestrator["Orchestrator"]

    subgraph Delegation
        Orchestrator -- "delegate_to_communications_agent" --> CommAgent["Communications Agent"]
        Orchestrator -- "delegate_to_analyst_agent" --> AnalystAgent["Analyst Agent"]
    end

    subgraph MCP Tool Servers
        CommAgent --> CorsairMCP["Corsair MCP (Gmail / GitHub)"]
        CommAgent --> TelegramMCP["Telegram MCP (Telethon)"]
        CommAgent --> NewsMCP["News MCP (streamable HTTP)"]

        AnalystAgent --> E2BMCP["E2B Sandbox MCP"]
        AnalystAgent --> CalcMCP["Calculator MCP"]
        AnalystAgent --> FSMCP["Filesystem MCP"]
    end

    CommAgent -- "summary" --> Orchestrator
    AnalystAgent -- "summary" --> Orchestrator
    Orchestrator --> FinalOutput(["Final response"])
```

Each box in "MCP Tool Servers" is its own process, connected independently. The orchestrator and both workers are the same LLM tool-calling loop reused three times, each with a different tool list and message history.

---

## Components

### Orchestrator-worker engine — [`multi_agent.py`](multi_agent.py)
The orchestrator holds two delegation functions instead of real tools. When it calls one, the corresponding worker is started with only the MCP sessions relevant to it, runs its own tool-calling loop to completion, and returns a text summary — not the raw tool output — back to the orchestrator's context.

### E2B sandbox server — [`E2B_sandbox.py`](E2B_sandbox.py)
Wraps the E2B Code Interpreter as an MCP server, exposing tools to run Python/Bash and read/write files inside an isolated remote container.

### Telegram userbot server — [`telegarm_mcp.py`](telegarm_mcp.py)
Wraps a Telethon (MTProto) client as an MCP server, so the agent can send messages and read dialogs as a full personal account rather than a restricted bot.

### Skill/playbook loader — [`index.py`](index.py) & [`skill.md`](skill.md)
Reads a markdown file with YAML frontmatter and folds its contents into the system prompt at startup, so operational rules can be changed without editing code.

### Corsair server — [`corsair-server/`](corsair-server)
A Node.js/TypeScript MCP server exposing Gmail and GitHub API access over stdio.

---

## Tech stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| LLM | NVIDIA Nemotron-3 (`nemotron-3-ultra-550b-a55b`) | Reasoning and tool selection |
| Agent protocol | Model Context Protocol (`mcp` SDK) | Tool connection over stdio and HTTP |
| Cloud sandbox | E2B Code Interpreter | Isolated remote code execution |
| Telegram | Telethon | MTProto personal account access |
| Containerization | Docker | Local filesystem server isolation |
| Runtime | Python 3.12, `uv`, Node.js, `tsx` | Async runtime and multi-language MCP servers |

---

## Structure

```text
simpleAgent/
├── multi_agent.py            # Orchestrator-worker implementation
├── index.py                  # Single-agent runtime with skill playbook injection
├── E2B_sandbox.py            # MCP server wrapping the E2B sandbox
├── telegarm_mcp.py           # MCP server wrapping the Telethon userbot
├── server.py                 # MCP calculator server
├── corsair_mcp.py            # Stdio connection config for the Corsair server
├── skill.md                  # Example operational playbook
├── multi_agent_guide.md      # Notes on the multi-agent architecture
├── personal_telegram_guide.md# Telegram userbot setup notes
├── corsair-server/           # Node.js MCP server for Gmail & GitHub
├── pyproject.toml            # Python dependencies
└── .env                      # API keys (git-ignored, not committed)
```

---

## Setup

### Prerequisites
- Python 3.12+ and `uv`
- Node.js 18+ and `npx`
- Docker or Podman (for the local containerized filesystem server)
- PostgreSQL (for Corsair server OAuth token persistence)

### Environment
Create a `.env` file in the project root:
```env
NVIDIA_API_KEY="your_nvidia_api_key"
smithery_api_key="your_smithery_api_key"
E2B_API_KEY="your_e2b_api_key"
DATABASE_URL="postgresql://postgres:password@localhost:5433/mydb"
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH="your_telegram_api_hash"
TELEGRAM_PHONE="+1234567890"
```

### Install
```bash
uv sync
```

### One-time Telegram login
```bash
.venv/bin/python telegarm_mcp.py login
```
Enter the OTP sent to your Telegram client when prompted.

### Run the orchestrator-worker system
```bash
uv run multi_agent.py "Run a python script in E2B sandbox to calculate Fibonacci and send to Telegram"
```

### Run the single-agent version with skill injection
```bash
uv run index.py "Send an email to user@example.com with project updates"
```

---

## Example run

Given the request:

> "Run a Python script in the E2B sandbox to calculate the first 10 Fibonacci numbers, write the results to `fib.txt`, read the file, and send the output to my Telegram account."

1. The orchestrator delegates the sandbox/file work to the analyst agent.
2. The analyst agent runs the calculation in E2B, writes `fib.txt`, reads it back, and reports the result.
3. The orchestrator delegates the messaging step to the communications agent, passing along the file contents.
4. The communications agent sends the message over Telegram and reports success.
5. The orchestrator combines both reports into one final response.

---
*Mahesh N*
