import { runStdioMcpServer } from "@corsair-dev/mcp";
import { corsair } from "./corsair.js";


await runStdioMcpServer({
    corsair: corsair,
});