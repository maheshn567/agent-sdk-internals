import pg from 'pg';

async function initDb() {
  const client = new pg.Client({
    connectionString: "postgresql://postgres:mahesh567@localhost:5432/mydb"
  });
  try {
    await client.connect();
    
    // Create corsair_integrations table
    await client.query(`
      CREATE TABLE IF NOT EXISTS corsair_integrations (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        name TEXT NOT NULL,
        config JSONB NOT NULL,
        dek TEXT NULL
      );
    `);
    
    // Create corsair_accounts table
    await client.query(`
      CREATE TABLE IF NOT EXISTS corsair_accounts (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        tenant_id TEXT NOT NULL,
        integration_id TEXT NOT NULL,
        config JSONB NOT NULL,
        dek TEXT NULL
      );
    `);

    // Create corsair_entities table
    await client.query(`
      CREATE TABLE IF NOT EXISTS corsair_entities (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        account_id TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        version TEXT NOT NULL,
        data JSONB NOT NULL
      );
    `);

    // Create corsair_events table
    await client.query(`
      CREATE TABLE IF NOT EXISTS corsair_events (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        account_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        payload JSONB NOT NULL,
        status TEXT NULL
      );
    `);

    // Create corsair_permissions table
    await client.query(`
      CREATE TABLE IF NOT EXISTS corsair_permissions (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
        token TEXT NOT NULL,
        plugin TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        args TEXT NOT NULL,
        tenant_id TEXT NOT NULL,
        status TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        error TEXT NULL
      );
    `);

    console.log("All corsair_* database tables created/verified successfully!");
  } catch (err) {
    console.error("Error creating tables:", err);
  } finally {
    await client.end();
  }
}

initDb();
