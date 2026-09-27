import "dotenv/config";
import { createCorsair } from "corsair";
import { gmail } from "@corsair-dev/gmail";
import { github } from "@corsair-dev/github";
import { db, pool } from "./db.js";
import type { PrismaClient } from "./generated/prisma/client.js";
import { telegram } from "@corsair-dev/telegram";

export const prisma: PrismaClient = db;

export const corsair = createCorsair({
    database: pool,
    kek: process.env.CORSAIR_KEK!,
    plugins: [
        gmail({
            keyBuilder: async ({ keys }) => {
                await keys.set_client_id(process.env.GMAIL_CLIENT_ID!);
                await keys.set_client_secret(process.env.GMAIL_CLIENT_SECRET!);
            }
        }),
        github({
            authType: "oauth_2",
            keyBuilder: async ({ keys }) => {
                await keys.set_client_id(process.env.GITHUB_CLIENT_ID!);
                await keys.set_client_secret(process.env.GITHUB_CLIENT_SECRET!);
            }
        }),
        telegram()
    ],
});