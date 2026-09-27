import { corsair } from "./corsair.js";
import { setupCorsair } from "corsair";

async function runSetup() {
  try {
    const result = await setupCorsair(corsair);
    console.log("Setup output:");
    console.log(result);
  } catch (err) {
    console.error("Setup failed:", err);
  }
}

runSetup();
