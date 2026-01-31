import "server-only";

import { Pool, type QueryResult } from "pg";

const connectionString = process.env.DATABASE_URL;

if (!connectionString) {
  throw new Error("DATABASE_URL is required");
}

const globalForPg = globalThis as typeof globalThis & {
  _pgPool?: Pool;
};

const pool =
  globalForPg._pgPool ??
  new Pool({
    connectionString,
    max: 10,
    idleTimeoutMillis: 10_000,
    connectionTimeoutMillis: 2_000,
  });

if (process.env.NODE_ENV !== "production") {
  globalForPg._pgPool = pool;
}

export async function dbQuery<T>(
  text: string,
  params: ReadonlyArray<unknown> = []
): Promise<QueryResult<T>> {
  const client = await pool.connect();
  try {
    return await client.query<T>(text, params);
  } finally {
    client.release();
  }
}

