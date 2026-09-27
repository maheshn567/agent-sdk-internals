import dotenv from "dotenv";

dotenv.config();

export interface AppConfig {
    googleClientId: string;
    googleClientSecret: string;
    databaseUrl: string;
    kek: string;
    port: number;
}

export const config: AppConfig = {
    googleClientId: process.env.GOOGLE_CLIENT_ID ?? "",
    googleClientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    telegatamAccessToken: process.env.TELEGATAM_ACCESS_TOKEN ?? "",
    

    databaseUrl: process.env.DATABASE_URL ?? "file:./corsair.db",

    kek: process.env.KEK ?? "",

    port: Number(process.env.PORT ?? 3000),
};