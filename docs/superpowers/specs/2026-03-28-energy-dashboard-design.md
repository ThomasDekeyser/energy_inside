# Energy Dashboard SPA — Design Spec

## Overview

A single static HTML page that fetches today's `active_power_w` readings from the DoltHub read API and displays them as an interactive Plotly.js line chart. Hosted on static hosting (GitHub Pages or Netlify).

## Architecture

```
[Browser] --fetch--> [DoltHub Read API] --JSON--> [Plotly.js chart]
```

Single `index.html` file, no build step. Plotly.js loaded from CDN.

## Layout

- Light theme with "Energy Inside" title and current date
- Summary stats bar: Current power (latest reading), Peak (max), Average, Min
- Plotly.js line chart: `active_power_w` over time with hover tooltips, zoom, and pan
- Stats are computed client-side from the fetched data

## Data Flow

1. On page load, build a SQL query to fetch today's readings:
   ```
   SELECT timestamp, active_power_w FROM readings WHERE timestamp >= '<today 00:00 UTC>' ORDER BY timestamp
   ```
2. Fetch from DoltHub read API:
   ```
   GET https://www.dolthub.com/api/v1alpha1/thomasdekeyser/energy_inside/main?q=<URL-encoded SQL>
   ```
3. Parse the `rows` array from the JSON response. Each row contains `timestamp` and `active_power_w`.
4. Compute summary stats client-side:
   - Current: last value in the array
   - Peak: max value
   - Average: mean of all values
   - Min: min value
5. Render Plotly.js line chart with timestamps on x-axis, watts on y-axis

## DoltHub Read API Response Format

```json
{
  "query_execution_status": "Success",
  "query_execution_message": "",
  "repository_owner": "thomasdekeyser",
  "repository_name": "energy_inside",
  "commit_ref": "...",
  "sql_query": "...",
  "schema": [
    {"columnName": "timestamp", "columnType": "Datetime"},
    {"columnName": "active_power_w", "columnType": "Decimal(10,3)"}
  ],
  "rows": [
    {"timestamp": "2026-03-28 00:00:00", "active_power_w": "77.000"},
    ...
  ]
}
```

Note: Values in `rows` are returned as strings and must be parsed to numbers.

## Error Handling

- If the API is unreachable or returns an error, show a message in place of the chart: "Failed to load data from DoltHub"
- If no rows are returned (no readings yet today), show "No readings available for today"

## Hosting

- Static file deployed to GitHub Pages or Netlify
- No backend required
- No API keys needed (DoltHub read API is public for public repos)

## Project Structure

```
energy_inside/
├── dashboard/
│   └── index.html    # Single page application
├── collect.py
├── ...
```

## Manual refresh

The page shows a snapshot of data at load time. Refresh the browser to see updated readings.
