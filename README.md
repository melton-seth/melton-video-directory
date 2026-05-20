# Melton Video Library

A passcode-protected, auto-updating directory of Melton's Vimeo videos and showcases. Built as a static site hosted on GitHub Pages, refreshed nightly via GitHub Actions.

---

## Setup

### 1. Enable GitHub Pages

In the repo Settings → Pages:
- Source: **Deploy from a branch**
- Branch: `main`, folder: `/ (root)`

### 2. Add GitHub Secrets

In Settings → Secrets and variables → Actions → **New repository secret**:

| Secret name    | Value                                      |
|----------------|--------------------------------------------|
| `VIMEO_TOKEN`  | Your Vimeo personal access token           |
| `SITE_PASSWORD`| The passcode users will enter on the site  |

### 3. Add the logo

Commit `Melton__Logo2.png` to the repo root (already included).

### 4. Run the first build

Go to **Actions → Update Video Directory → Run workflow** to trigger the first fetch and build. This creates `data.json` and `index.html`, which are committed back to the repo automatically.

After the first run, the site will be live at:
```
https://melton-seth.github.io/melton-video-directory/
```

---

## How it works

| File | Purpose |
|------|---------|
| `fetch_videos.py` | Calls the Vimeo API, writes `data.json` |
| `build.py` | Reads `data.json`, renders `index.html` with password hash baked in |
| `.github/workflows/update.yml` | Runs both scripts nightly at 2 AM UTC; also triggerable manually |
| `data.json` | Intermediate data file (committed to repo) |
| `index.html` | The generated site (committed to repo, served by Pages) |

## Schedule

The workflow runs every night at **2:00 AM UTC**. To trigger a manual refresh:
1. Go to the **Actions** tab
2. Click **Update Video Directory**
3. Click **Run workflow**

## Updating the password

1. Go to Settings → Secrets → update `SITE_PASSWORD`
2. Trigger a manual workflow run to rebuild `index.html` with the new hash

---

*Florence Melton School of Adult Jewish Learning · meltonschool.org*
