import "dotenv/config";
import { corsair } from "./corsair.js";

async function main() {
  console.log("Calling getMe...");
  const me = await corsair.telegram.api.me.getMe();
  console.log("Bot info:", me);

  console.log("Calling deleteWebhook...");
  const del = await corsair.telegram.api.webhook.deleteWebhook({ drop_pending_updates: false });
  console.log("Delete Webhook result:", del);

  console.log("Calling getUpdates...");
  const updates = await corsair.telegram.api.updates.getUpdates({});
  console.log("Updates:", JSON.stringify(updates, null, 2));

  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
