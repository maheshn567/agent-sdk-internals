import { corsair } from "./corsair.js";

async function login() {
  try {
    const result = await corsair.manage.connect.createLink({
      plugin: "gmail",
      tenantId: "default"
    });
    console.log("\n----------------------------------------");
    console.log("Open this URL in your browser to log in to Gmail:");
    console.log(result.connectUrl);
    console.log("----------------------------------------\n");
  } catch (err) {
    console.error("Error generating login link:", err);
  }
}

login();
