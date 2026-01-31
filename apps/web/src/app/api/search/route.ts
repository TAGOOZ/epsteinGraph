import { NextResponse } from "next/server";

type MeiliSearchResponse = {
  hits: Array<Record<string, unknown>>;
  offset: number;
  limit: number;
  estimatedTotalHits?: number;
  totalHits?: number;
  processingTimeMs: number;
  query: string;
};

const MEILI_HOST = process.env.MEILI_HOST;
const MEILI_MASTER_KEY = process.env.MEILI_MASTER_KEY;

export async function GET(request: Request) {
  if (!MEILI_HOST || !MEILI_MASTER_KEY) {
    return NextResponse.json(
      { error: "MEILI_HOST and MEILI_MASTER_KEY are required" },
      { status: 500 }
    );
  }

  const { searchParams } = new URL(request.url);
  const q = (searchParams.get("q") ?? "").trim();
  const limit = Number(searchParams.get("limit") ?? 20);
  const offset = Number(searchParams.get("offset") ?? 0);

  if (!q) {
    return NextResponse.json({ error: "q is required" }, { status: 400 });
  }

  const response = await fetch(`${MEILI_HOST}/indexes/chunks/search`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${MEILI_MASTER_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      q,
      limit,
      offset,
      attributesToHighlight: ["text"],
      highlightPreTag: "<mark>",
      highlightPostTag: "</mark>",
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    const errorText = await response.text();
    return NextResponse.json(
      { error: "search_failed", details: errorText },
      { status: 502 }
    );
  }

  const data = (await response.json()) as MeiliSearchResponse;

  return NextResponse.json({
    query: data.query,
    hits: data.hits,
    offset: data.offset,
    limit: data.limit,
    total: data.estimatedTotalHits ?? data.totalHits ?? 0,
  });
}
