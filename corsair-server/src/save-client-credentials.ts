import "dotenv/config";
import { corsair } from "./corsair.js";

async function save() {
  const gmailClientId = process.env.GMAIL_CLIENT_ID;
  const gmailClientSecret = process.env.GMAIL_CLIENT_SECRET;
  const githubClientId = process.env.GITHUB_CLIENT_ID;
  const githubClientSecret = process.env.GITHUB_CLIENT_SECRET;
  
  if (gmailClientId && gmailClientSecret) {
    console.log("Saving Gmail client credentials...");
    await corsair.keys.gmail.set_client_id(gmailClientId);
    await corsair.keys.gmail.set_client_secret(gmailClientSecret);
  }
  
  if (githubClientId && githubClientSecret) {
    console.log("Saving GitHub client credentials...");
    await corsair.keys.github.set_client_id(githubClientId);
    await corsair.keys.github.set_client_secret(githubClientSecret);
  }

  const telegramToken = process.env.TELEGATAM_ACCESS_TOKEN;
  if (telegramToken) {
    console.log("Saving Telegram bot token...");
    await corsair.telegram.keys.set_bot_token(telegramToken);
    await corsair.telegram.keys.set_one("one");
  }
  
  console.log("Saved all successfully!");
  process.exit(0);
}

save();
