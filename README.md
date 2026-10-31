# gemini-pr-review-bot

AI-powered GitHub App that automatically reviews pull requests using Google Gemini.

## Requirements

- Python 3.12+
- A GitHub App with webhook delivery enabled
- A webhook secret configured in the GitHub App
- Google Gemini credentials for the review integration

## Local setup

Create an isolated environment and install the pinned dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set the webhook secret before starting the service:

```bash
export GITHUB_WEBHOOK_SECRET="replace-with-a-random-secret"
```

The Gemini and GitHub integration credentials should also be provided through
environment variables when that integration is implemented. Do not commit
secrets or place them in source files.

## Run

Start the FastAPI application with Uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The health endpoint is available at `GET /health`. Configure the GitHub App
webhook URL to point to `https://your-host.example/api/webhook` and use the
same value as `GITHUB_WEBHOOK_SECRET`.

## Test

```bash
python -m unittest -v test_app.py
python -m compileall -q app.py test_app.py
```

Dependencies are pinned in `requirements.txt` so local and CI installations
resolve the same versions.

## Vercel deployment

This repository includes `vercel.json` and `api/index.py` for Vercel's Python
runtime. Import the repository into Vercel and configure these environment
variables for the deployed project:

- `GITHUB_WEBHOOK_SECRET`: the exact secret configured on the GitHub App webhook

After deployment, verify `https://your-project-domain/health` returns
`{"status":"healthy"}`, then configure the GitHub App webhook URL as
`https://your-project-domain/api/webhook`.

The current webhook implementation validates and routes pull-request events;
Gemini review generation and posting the review back to GitHub still require
implementation of the integration workflow.
