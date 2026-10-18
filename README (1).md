# Descriptive Statistics API

FastAPI service for `GET /stats?values=1,2,3`, with exact-origin CORS and per-response request metrics.

## Included behavior

- Computes `count`, `sum`, `min`, `max`, and arithmetic `mean` from every request's input; no fixture or hard-coded statistics.
- Returns the configured `APP_EMAIL` exactly as the service identity.
- Allows browser CORS only from `https://dash-scfih4.example.com`; no wildcard `Access-Control-Allow-Origin` is configured.
- Accepts `GET` in a preflight from the allowed origin. Other origins receive no `Access-Control-Allow-Origin` header.
- Adds a fresh UUID `X-Request-ID` and numeric non-negative `X-Process-Time` to HTTP responses, including CORS preflight responses.

## Run locally

Python 3.10+ is recommended.

### PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:APP_EMAIL = "your-exact-logged-in-email@example.com"
uvicorn main:app --host 127.0.0.1 --port 8000
```

Use your actual logged-in email value, not the example address.

## Deploy on Render

1. Push the contents of this folder to a GitHub repository you control.
2. In Render, choose **New + → Blueprint** and connect that repository. Render reads `render.yaml` and creates the web service.
3. When prompted for `APP_EMAIL`, enter the exact email address used to log into the evaluation platform. This value is required; the service will return an error from `/stats` until it is configured.
4. After deployment succeeds, copy the public `https://...onrender.com` service URL. That is the base URL to submit; do not include `/stats`.

## Check the endpoints

Replace `BASE_URL` with your local or deployed base URL.

```bash
curl -i 'BASE_URL/stats?values=1,2,3,4'
```

Expected statistics for that sample: count `4`, sum `10`, min `1`, max `4`, mean `2.5`.

Allowed-origin preflight (should be successful and include the exact ACAO value):

```bash
curl -i -X OPTIONS 'BASE_URL/stats' \
  -H 'Origin: https://dash-scfih4.example.com' \
  -H 'Access-Control-Request-Method: GET'
```

Disallowed-origin preflight (must have no `Access-Control-Allow-Origin` header):

```bash
curl -i -X OPTIONS 'BASE_URL/stats' \
  -H 'Origin: https://evil.example' \
  -H 'Access-Control-Request-Method: GET'
```

Every HTTP response should include `X-Request-ID` and `X-Process-Time`.
