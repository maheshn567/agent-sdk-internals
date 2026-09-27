import pg from 'pg';
import { PrismaPg } from '@prisma/adapter-pg';
import { PrismaClient } from './generated/prisma/client.js';
import { config } from './config.js';

// Setup type safety for global scope
const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
  pool: pg.Pool | undefined;
};

// Initialize the shared pg Pool
export const pool = globalForPrisma.pool ?? new pg.Pool({
  connectionString: config.databaseUrl,
});

const adapter = new PrismaPg(pool);

// Use existing global instance if available, otherwise instantiate a new one
export const db = globalForPrisma.prisma ?? new PrismaClient({ adapter });

// Save to global scope in non-production environments to preserve connection across hot-reloads
if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = db;
  globalForPrisma.pool = pool;
}

console.error('[Database] Initialized Prisma Client and pg Pool global instances');
