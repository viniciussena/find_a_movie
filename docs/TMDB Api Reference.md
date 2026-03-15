# TMDB API Reference

## Executive summary

This document is a concise reference for using **TMDB API v3** to build the **Find a Movie** dataset: ingest movie IDs and metadata into a Bronze layer, transform into clean Silver staging models, and publish analytics-ready Gold facts/dimensions. It is intentionally optimized for AI agents generating ingestion code: it includes authentication, pagination/rate-limit rules, high-value endpoints, and a recommended extraction workflow (IDs → details → enrichments). 

## Authentication and base URL

**Base URL (v3):**

- `https://api.themoviedb.org/3` (all endpoints below are under `/3/...`). 

**Auth methods (application-level):**

TMDB v3 can be authenticated **either** by:

1. Query param `api_key=...`, **or**
2. Header `Authorization: Bearer <API Read Access Token>` (recommended; works across v3 and v4). 

**Recommended headers:**

```http
Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>
Accept: application/json
```

**cURL example (Bearer):**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/movie/11' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>' \
 --header 'accept: application/json'
```

TMDB explicitly documents the Bearer approach as the “default method” for v3 when using the **API Read Access Token**. 

## Rate limiting and pagination

**Pagination rules (critical):**

- Most “list” endpoints support `page` (integer).
- Pages start at **1** and the max is **500**; requests outside this range return an “Invalid page” error. 

**Rate limiting (do not hardcode an exact limit):**

- TMDB disabled the *legacy* limit (“40 requests every 10 seconds”) in 2019.
- TMDB still enforces “upper limits” to deter high-volume scraping; documented as **somewhere in the ~40 requests/second range**, and it can change at any time. Treat the exact limit as **unspecified** and implement backoff + throttling. 
- If you exceed limits, expect HTTP **429** (Too Many Requests). TMDB’s error list includes a 429 message referencing an “allowed limit of (40)”, but the current exact enforcement is not guaranteed. 

**Change-list date window:**

- Change list endpoints accept `start_date` / `end_date` and must be a range no longer than **14 days** (or you’ll get an invalid date range error). 

## Daily ID exports from files.tmdb.org

TMDB provides **daily ID exports** (movie IDs, TV IDs, people IDs, etc.). These are **not full data exports**—they’re meant to give you valid IDs + a few high-level attributes (e.g., `adult`, `video`, `popularity`). 

Key operational details:

- Host: `https://files.tmdb.org`
- Export job runs daily around **07:00 UTC** and files are available by **08:00 UTC**.
- Files are retained for **3 months**. 
- Files are **gzip-compressed** and **not a single JSON document**. Instead, **each line is a JSON object** (JSONL), designed for streaming parses (no need to load full file into memory). 
- Currently no authentication for these files, but TMDB warns that it may change. 

Paths and naming (movies):

- Path: `/p/exports/`
- File: `movie_ids_MM_DD_YYYY.json.gz` 

**How to use in bulk ingestion:**

1. Download the daily file for the ingestion date.
2. Stream-decompress (`.gz`).
3. Parse **line-by-line** JSON objects to get `id` (+ flags).
4. Use IDs to drive detail/enrichment calls via the API.

## Endpoints for this project

### Endpoint summary

| Purpose | Method | Path | Key params (most used) |
|---|---:|---|---|
| Discover movies (filter by year/date/genres) | GET | `/discover/movie` | `page`, `language`, `region`, `sort_by`, `with_genres`, `primary_release_year`, `primary_release_date.gte/lte` |
| Movie details (core dimensions) | GET | `/movie/{movie_id}` | `language`, `append_to_response` |
| Movie change list (IDs changed) | GET | `/movie/changes` | `start_date`, `end_date`, `page` |
| Genre dictionary | GET | `/genre/movie/list` | `language` |
| Popular movies list | GET | `/movie/popular` | `page`, `language`, `region` |
| Movie credits (cast/crew) | GET | `/movie/{movie_id}/credits` | `language` *(also fetchable via `append_to_response=credits`)* |
| Search movies by title | GET | `/search/movie` | `query`, `page`, `language`, `region`, `include_adult`, `year` |
| Multi search (movie/tv/person) | GET | `/search/multi` | `query`, `page`, `language`, `include_adult` |
| Trending movies | GET | `/trending/movie/{time_window}` | `time_window=day|week`, `language` |

The parameter lists and example payload shapes above are defined in TMDB’s v3 OpenAPI file and reference pages. 

### Endpoint details with examples

#### Discover movies

**Method / path:** `GET /3/discover/movie` 

**Common filters (project-focused):**
- `primary_release_year` (e.g., `2025`)
- `primary_release_date.gte`, `primary_release_date.lte` (YYYY-MM-DD)
- `with_genres` (comma for AND, pipe for OR)
- `sort_by` (e.g., `popularity.desc`) 

**Sample request:**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/discover/movie?primary_release_year=2025&sort_by=popularity.desc&page=1&language=en-US' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>' \
 --header 'accept: application/json'
```

**Minimal response shape:**

```json
{
 "page": 1,
 "results": [
 {
 "id": 640146,
 "title": "Ant-Man and the Wasp: Quantumania",
 "release_date": "2023-02-15",
 "genre_ids": [28, 12, 878],
 "popularity": 9272.643,
 "vote_average": 6.5,
 "vote_count": 1856,
 "adult": false
 }
 ],
 "total_pages": 500,
 "total_results": 10000
}
```

Field names and filter params shown are consistent with TMDB’s OpenAPI example. Note that `page` is capped at 500 even if `total_pages` is higher. 

#### Movie details

**Method / path:** `GET /3/movie/{movie_id}` 

**Key params:**
- `language`
- `append_to_response` (comma-separated; max 20 appended calls) 

**Sample request (details only):**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/movie/550?language=en-US' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>' \
 --header 'accept: application/json'
```

**Minimal response shape:**

```json
{
 "id": 550,
 "imdb_id": "tt0137523",
 "title": "Fight Club",
 "original_language": "en",
 "release_date": "1999-10-15",
 "runtime": 139,
 "status": "Released",
 "genres": [{"id": 18, "name": "Drama"}],
 "budget": 63000000,
 "revenue": 100853753,
 "popularity": 73.433,
 "vote_average": 8.433,
 "vote_count": 26279
}
```

The example fields above mirror the OpenAPI example for this endpoint. 

#### Genre dictionary

**Method / path:** `GET /3/genre/movie/list` 

**Sample request:**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/genre/movie/list?language=en' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>' \
 --header 'accept: application/json'
```

**Minimal response shape:**

```json
{
 "genres": [
 {"id": 28, "name": "Action"},
 {"id": 12, "name": "Adventure"},
 {"id": 35, "name": "Comedy"}
 ]
}
```

#### Popular movies

**Method / path:** `GET /3/movie/popular` 

**Key params:** `page`, `language`, `region` (ISO-3166-1). 

**Sample request:**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/movie/popular?page=1&language=en-US&region=US' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>'
```

**Minimal response shape:** same pagination envelope as Discover. 

#### Search movies

**Method / path:** `GET /3/search/movie` 

**Key params:** `query` (required), `page`, `language`, `region`, `include_adult`, `year`, `primary_release_year`. 

**Sample request:**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/search/movie?query=Whiplash&language=de-DE&region=DE&page=1' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>' \
 --header 'accept: application/json'
```

TMDB documents `region` as a presentation filter for release dates (falls back to primary release date if missing). 

#### Multi search

**Method / path:** `GET /3/search/multi` 

**Key params:** `query` (required), `page`, `language`, `include_adult`. 

#### Trending movies

**Method / path:** `GET /3/trending/movie/{time_window}` where `time_window ∈ {day, week}` 

**Sample request:**

```bash
curl --request GET \
 --url 'https://api.themoviedb.org/3/trending/movie/day?language=en-US' \
 --header 'Authorization: Bearer <TMDB_API_READ_ACCESS_TOKEN>'
```

#### Movie change list

**Method / path:** `GET /3/movie/changes` 

**Key params:** `start_date`, `end_date` (YYYY-MM-DD), `page`. 

**Minimal response shape:**

```json
{
 "results": [{"id": 1120293, "adult": false}],
 "page": 1,
 "total_pages": 57,
 "total_results": 5700
}
```

This endpoint is the core of incremental sync (IDs changed → fetch updated details). TMDB notes the default window is 24 hours and can be extended up to 14 days. 

## Bulk ingestion best practices

**Avoid the “one giant Discover query” trap.** Because `page` is capped at 500, large queries can silently become incomplete if you expect to retrieve everything in one filter set. Partition by time windows (month/week) using `primary_release_date.gte/lte` and/or segment by genre when necessary. 

**Prefer ID-driven ingestion for completeness:**

- **Daily ID exports** are the best starting point for “many IDs” ingestion (streamable JSONL).  
- Use `/movie/changes` daily to update only IDs that changed, respecting the 14-day window constraint for backfills. 

**Use `append_to_response` to reduce calls:**

Movie details supports `append_to_response` (comma-separated, max 20 sub-requests). Use it to pull related objects in one HTTP round trip. 

**Throttle + backoff:**

TMDB’s current “upper limit” is described as ~40 req/s range and may change. Implement adaptive throttling and exponential backoff on 429. 

## Extraction workflow, code snippets, and warehouse mapping

### Suggested extraction workflow

1. **Seed dimensions:** `GET /genre/movie/list` → `dim_genre`. 
2. **Get IDs:** 
 - Initial load: download `movie_ids_MM_DD_YYYY.json.gz` (daily export) and/or use Discover partitions for a specific year (e.g., 2025). 
3. **Fetch details:** `GET /movie/{id}` (optionally with `append_to_response=credits`) → base movie rows. 
4. **Incremental:** daily `GET /movie/changes` → re-fetch details for changed IDs only.  

### Python snippets

**Paginated fetch with page cap + rate-limit backoff:**

```python
import time
import requests

BASE_URL = "https://api.themoviedb.org/3"

def tmdb_get(session: requests.Session, path: str, token: str, params: dict | None = None,
 max_retries: int = 6) -> dict:
 url = f"{BASE_URL}{path}"
 headers = {"Authorization": f"Bearer {token}", "accept": "application/json"}

 delay = 1.0
 for attempt in range(max_retries):
 resp = session.get(url, headers=headers, params=params, timeout=30)

 if resp.status_code == 429:
 # Rate limit hit: exponential backoff (exact limit is unspecified and may change)
 time.sleep(delay)
 delay = min(delay * 2, 60)
 continue

 resp.raise_for_status()
 return resp.json()

 raise RuntimeError(f"Max retries exceeded for {url}")

def fetch_all_pages(session: requests.Session, path: str, token: str, params: dict) -> list[dict]:
 # TMDB pages start at 1 and max at 500
 out: list[dict] = []
 for page in range(1, 501):
 payload = tmdb_get(session, path, token, {**params, "page": page})
 out.extend(payload.get("results", []))

 total_pages = int(payload.get("total_pages", page))
 if page >= total_pages:
 break

 return out
```

Pagination cap and 429 guidance are based on TMDB’s docs (max page 500; respect 429). 

**Fetch movie details with `append_to_response`:**

```python
def fetch_movie_details(session: requests.Session, token: str, movie_id: int) -> dict:
 # Keep append list small; TMDB caps appended calls (max 20)
 params = {
 "language": "en-US",
 "append_to_response": "credits" # optional; can add "images,videos" etc
 }
 return tmdb_get(session, f"/movie/{movie_id}", token, params)
```

`append_to_response` semantics and maximum “remote calls” are documented by TMDB. 

### Error handling examples

TMDB maintains a canonical list of error codes/messages (e.g., invalid API key 401, resource not found 404, invalid page 400, 429 throttling). 

Representative payload shape for auth failures:

```json
{"status_code": 7, "status_message": "Invalid API key: You must be granted a valid key.", "success": false}
```

This structure is shown in the OpenAPI examples. 

### Suggested warehouse schema mapping

| Layer | Table | Grain | Suggested columns (core) |
|---|---|---|---|
| Bronze | `bronze_movie_ids` | 1 row per (ingestion_date, movie_id) | `ingestion_date`, `movie_id`, `adult`, `video`, `popularity`, `raw_line` |
| Bronze | `bronze_movies_raw` | 1 row per (movie_id, snapshot_ts) | `snapshot_ts`, `movie_id`, `raw_json` |
| Bronze | `bronze_movie_changes` | 1 row per (change_date, movie_id) | `change_date`, `movie_id`, `adult`, `page`, `raw_json` |
| Silver | `stg_movies` | 1 row per movie_id (latest) | parsed fields: `title`, `release_date`, `runtime`, `status`, `budget`, `revenue`, `popularity`, `vote_*`, `imdb_id`, … |
| Silver | `stg_movie_genres` | bridge | `movie_id`, `genre_id` |
| Silver | `stg_movie_credits` | cast/crew rows | `movie_id`, `person_id`, `credit_type`, `character`, `job`, `department`, `order` |
| Gold | `dim_movie` | 1 row per movie | conformed movie attributes |
| Gold | `dim_genre` | 1 row per genre | `genre_id`, `genre_name` |
| Gold | `dim_person` | 1 row per person | `person_id`, `name` |
| Gold | `fact_movie_popularity` | 1 row per movie snapshot | `movie_id`, `snapshot_date`, `popularity`, `vote_average`, `vote_count`, `revenue`, … |

### Minimal implementation checklist

**Airflow tasks**
- Download & load daily export `movie_ids_*.json.gz` (stream parse JSON lines).  
- Discover movies for a target year using date partitioning (stop at page 500).  
- Fetch movie details (optionally append credits) with rate-limit backoff.  
- Incremental sync via `/movie/changes` (daily).  

**dbt models**
- `stg_*` models to parse JSON, cast types, dedupe to latest snapshot
- `dim_*` and `fact_*` models with tests (unique keys + not nulls)

## Prioritized official sources

- Getting started: `https://developer.themoviedb.org/docs/getting-started` 
- Authentication (application): `https://developer.themoviedb.org/docs/authentication-application`  
- Rate limiting: `https://developer.themoviedb.org/docs/rate-limiting` 
- Errors: `https://developer.themoviedb.org/docs/errors` 
- Daily ID exports: `https://developer.themoviedb.org/docs/daily-id-exports`  
- Append to response: `https://developer.themoviedb.org/docs/append-to-response` 
- Tracking changes: `https://developer.themoviedb.org/docs/tracking-content-changes`  
- OpenAPI (v3): `https://developer.themoviedb.org/openapi/tmdb-api.json` 