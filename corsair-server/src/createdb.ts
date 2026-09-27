import pg from 'pg';

async function createDatabase() {
  const client = new pg.Client({
    connectionString: "postgresql://postgres:mahesh567@localhost:5432/postgres"
  });
  try {
    await client.connect();
    await client.query("CREATE DATABASE mydb;");
    console.log("Database 'mydb' created successfully!");
  } catch (err: any) {
    if (err.code === '42P04') {
      console.log("Database 'mydb' already exists.");
    } else {
      console.error("Error creating database:", err);
    }
  } finally {
    await client.end();
  }
}

createDatabase();
