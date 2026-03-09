# NeelCollegePrep
This is to help Neel stay on top of his activities, planning and track progress towards his college app in Fall 2027

## Deploying On Render Free Tier

This repo is set up for a simple deploy flow:

1. Make changes locally.
2. Commit and push to `main` on GitHub.
3. Render auto-deploys the latest commit from `main`.

### Render settings

- Service type: `Web Service`
- Plan: `Free`
- Branch: `main`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

If you want Render to read settings from the repo, use the included `render.yaml` when creating a Blueprint service.

### Required environment variable

- `SECRET_KEY`: set this in Render, or let Render generate it from `render.yaml`

### Important free-tier limitation

This app currently stores data in a local SQLite file named `tracker.db`. Render free web services use an ephemeral filesystem, so app data stored in `tracker.db` can be lost on restart or redeploy. That means the code deploy pipeline works on the free tier, but durable data storage does not unless you move to an external database or a paid Render disk.
