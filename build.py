#!/usr/bin/env python3
"""
build.py
Reads data.json and renders the Melton Video Directory index.html.
The SITE_PASSWORD is injected at build time via environment variable.
"""

import json
import os
import sys
import hashlib

SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")
if not SITE_PASSWORD:
    print("WARNING: SITE_PASSWORD not set — page will have no password protection.", file=sys.stderr)

# Hash the password so it's not stored in plain text in the HTML
pw_hash = hashlib.sha256(SITE_PASSWORD.encode()).hexdigest() if SITE_PASSWORD else ""

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

generated = data.get("generated", "")
videos = data.get("videos", [])
showcases = data.get("showcases", [])


def video_row(v):
    title = v["title"].replace('"', "&quot;").replace("<", "&lt;")
    url = v["url"]
    date = v["date"]
    return f"""
        <tr>
          <td><a href="{url}" target="_blank" rel="noopener">{title}</a></td>
          <td class="date-col">{date}</td>
        </tr>"""


def showcase_section(s):
    title = s["title"].replace('"', "&quot;").replace("<", "&lt;")
    url = s["url"]
    videos_html = "".join(video_row(v) for v in s["videos"])
    count = len(s["videos"])
    count_label = f"{count} video{'s' if count != 1 else ''}"

    if not s["videos"]:
        videos_html = '<tr><td colspan="2" class="empty-row">No videos in this showcase.</td></tr>'

    return f"""
    <section class="showcase-section">
      <div class="showcase-header">
        <div class="showcase-title-row">
          <h2 class="showcase-title">
            <a href="{url}" target="_blank" rel="noopener">{title}</a>
          </h2>
          <span class="showcase-count">{count_label}</span>
        </div>
      </div>
      <table class="video-table">
        <thead>
          <tr>
            <th>Title</th>
            <th class="date-col">Date Added</th>
          </tr>
        </thead>
        <tbody>
          {videos_html}
        </tbody>
      </table>
    </section>"""


all_videos_html = "".join(video_row(v) for v in videos)
all_showcases_html = "".join(showcase_section(s) for s in showcases)
total_videos = len(videos)
total_showcases = len(showcases)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Melton Video Library</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --blue:        #0042b9;
      --blue-dark:   #002f85;
      --blue-mid:    #377fe2;
      --blue-light:  #7bafde;
      --blue-pale:   #d4f0ed;
      --orange:      #f4773b;
      --white:       #ffffff;
      --gray-bg:     #f4f6fb;
      --gray-border: #dce4f0;
      --gray-text:   #5a6a82;
      --text:        #1a243a;
      --font:        'Nunito', 'Segoe UI', sans-serif;
      --radius:      10px;
      --shadow:      0 2px 16px rgba(0,66,185,0.10);
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: var(--font);
      background: var(--gray-bg);
      color: var(--text);
      min-height: 100vh;
    }}

    /* ── PASSCODE GATE ── */
    #gate {{
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background: var(--blue);
      padding: 2rem;
    }}

    #gate.hidden {{ display: none; }}

    .gate-card {{
      background: var(--white);
      border-radius: 16px;
      padding: 3rem 2.5rem 2.5rem;
      max-width: 380px;
      width: 100%;
      text-align: center;
      box-shadow: 0 8px 40px rgba(0,0,0,0.25);
    }}

    .gate-logo {{
      width: 120px;
      margin-bottom: 1.5rem;
    }}

    .gate-card h1 {{
      font-size: 1.4rem;
      font-weight: 800;
      color: var(--blue);
      margin-bottom: 0.4rem;
    }}

    .gate-card p {{
      font-size: 0.9rem;
      color: var(--gray-text);
      margin-bottom: 1.8rem;
    }}

    .gate-input {{
      width: 100%;
      padding: 0.8rem 1rem;
      font-size: 1rem;
      font-family: var(--font);
      border: 2px solid var(--gray-border);
      border-radius: var(--radius);
      outline: none;
      transition: border-color 0.2s;
      margin-bottom: 1rem;
      text-align: center;
      letter-spacing: 0.1em;
    }}

    .gate-input:focus {{ border-color: var(--blue); }}
    .gate-input.error {{ border-color: #e53e3e; animation: shake 0.3s ease; }}

    @keyframes shake {{
      0%, 100% {{ transform: translateX(0); }}
      25% {{ transform: translateX(-6px); }}
      75% {{ transform: translateX(6px); }}
    }}

    .gate-btn {{
      width: 100%;
      padding: 0.85rem;
      background: var(--blue);
      color: var(--white);
      font-family: var(--font);
      font-size: 1rem;
      font-weight: 700;
      border: none;
      border-radius: var(--radius);
      cursor: pointer;
      transition: background 0.2s;
    }}

    .gate-btn:hover {{ background: var(--blue-dark); }}

    .gate-error {{
      margin-top: 0.75rem;
      font-size: 0.85rem;
      color: #e53e3e;
      min-height: 1.2em;
    }}

    /* ── MAIN CONTENT ── */
    #content {{ display: none; }}
    #content.visible {{ display: block; }}

    /* ── HEADER ── */
    .site-header {{
      background: var(--white);
      border-bottom: 3px solid var(--blue);
      padding: 1.2rem 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 12px rgba(0,66,185,0.08);
    }}

    .header-left {{
      display: flex;
      align-items: center;
      gap: 1.2rem;
    }}

    .header-logo {{
      height: 52px;
      width: auto;
    }}

    .header-divider {{
      width: 2px;
      height: 40px;
      background: var(--gray-border);
    }}

    .header-title {{
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--blue);
      letter-spacing: -0.01em;
    }}

    .header-subtitle {{
      font-size: 0.8rem;
      color: var(--gray-text);
      font-weight: 600;
      margin-top: 1px;
    }}

    .header-meta {{
      font-size: 0.78rem;
      color: var(--gray-text);
      text-align: right;
    }}

    /* ── STATS BAR ── */
    .stats-bar {{
      background: var(--blue);
      color: var(--white);
      display: flex;
      gap: 2rem;
      padding: 0.8rem 2rem;
    }}

    .stat {{
      display: flex;
      align-items: baseline;
      gap: 0.4rem;
    }}

    .stat-num {{
      font-size: 1.4rem;
      font-weight: 800;
    }}

    .stat-label {{
      font-size: 0.8rem;
      opacity: 0.8;
      font-weight: 600;
    }}

    /* ── TABS ── */
    .tabs-bar {{
      background: var(--white);
      border-bottom: 2px solid var(--gray-border);
      display: flex;
      padding: 0 2rem;
      gap: 0;
    }}

    .tab-btn {{
      padding: 1rem 1.5rem;
      font-family: var(--font);
      font-size: 0.9rem;
      font-weight: 700;
      color: var(--gray-text);
      background: none;
      border: none;
      border-bottom: 3px solid transparent;
      margin-bottom: -2px;
      cursor: pointer;
      transition: color 0.2s, border-color 0.2s;
    }}

    .tab-btn:hover {{ color: var(--blue); }}

    .tab-btn.active {{
      color: var(--blue);
      border-bottom-color: var(--orange);
    }}

    /* ── MAIN ── */
    main {{
      max-width: 1000px;
      margin: 0 auto;
      padding: 2rem;
    }}

    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}

    /* ── SHOWCASE SECTIONS ── */
    .showcase-section {{
      background: var(--white);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      margin-bottom: 1.5rem;
      overflow: hidden;
      border: 1px solid var(--gray-border);
    }}

    .showcase-header {{
      background: var(--blue);
      padding: 1rem 1.5rem;
    }}

    .showcase-title-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}

    .showcase-title {{
      font-size: 1.05rem;
      font-weight: 800;
      color: var(--white);
    }}

    .showcase-title a {{
      color: inherit;
      text-decoration: none;
    }}

    .showcase-title a:hover {{ text-decoration: underline; opacity: 0.9; }}

    .showcase-count {{
      font-size: 0.78rem;
      font-weight: 700;
      background: rgba(255,255,255,0.2);
      color: var(--white);
      padding: 0.25rem 0.7rem;
      border-radius: 20px;
      white-space: nowrap;
    }}

    /* ── TABLES ── */
    .video-table {{
      width: 100%;
      border-collapse: collapse;
    }}

    .video-table thead tr {{
      background: var(--blue-pale);
    }}

    .video-table th {{
      padding: 0.65rem 1.5rem;
      font-size: 0.72rem;
      font-weight: 800;
      color: var(--blue);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      text-align: left;
    }}

    .video-table td {{
      padding: 0.75rem 1.5rem;
      font-size: 0.9rem;
      border-bottom: 1px solid var(--gray-border);
      vertical-align: middle;
    }}

    .video-table tbody tr:last-child td {{ border-bottom: none; }}

    .video-table tbody tr:hover {{ background: #f0f5ff; }}

    .video-table a {{
      color: var(--blue);
      text-decoration: none;
      font-weight: 600;
    }}

    .video-table a:hover {{
      color: var(--orange);
      text-decoration: underline;
    }}

    .date-col {{
      white-space: nowrap;
      color: var(--gray-text);
      font-size: 0.82rem;
      width: 160px;
    }}

    .empty-row {{
      color: var(--gray-text);
      font-style: italic;
      text-align: center;
      padding: 1.5rem !important;
    }}

    /* ── ALL VIDEOS PANEL ── */
    .all-videos-card {{
      background: var(--white);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      border: 1px solid var(--gray-border);
      overflow: hidden;
    }}

    .all-videos-card .section-header {{
      background: var(--blue);
      padding: 1rem 1.5rem;
      color: var(--white);
      font-size: 1.05rem;
      font-weight: 800;
    }}

    /* ── FOOTER ── */
    .site-footer {{
      text-align: center;
      padding: 2rem;
      font-size: 0.78rem;
      color: var(--gray-text);
    }}

    .site-footer a {{
      color: var(--blue-mid);
      text-decoration: none;
    }}

    @media (max-width: 600px) {{
      .site-header {{ padding: 1rem; flex-wrap: wrap; }}
      main {{ padding: 1rem; }}
      .stats-bar {{ gap: 1rem; padding: 0.8rem 1rem; flex-wrap: wrap; }}
      .date-col {{ display: none; }}
      .tabs-bar {{ padding: 0 0.5rem; }}
    }}
  </style>
</head>
<body>

  <!-- PASSCODE GATE -->
  <div id="gate">
    <div class="gate-card">
      <img src="melton-logo.png" alt="Melton" class="gate-logo" />
      <h1>Video Library</h1>
      <p>Enter the access code to continue.</p>
      <input type="password" id="pw-input" class="gate-input" placeholder="••••••••" autocomplete="current-password" />
      <button class="gate-btn" onclick="checkPassword()">Enter</button>
      <div class="gate-error" id="gate-error"></div>
    </div>
  </div>

  <!-- MAIN CONTENT -->
  <div id="content">

    <header class="site-header">
      <div class="header-left">
        <img src="melton-logo.png" alt="Melton" class="header-logo" />
        <div class="header-divider"></div>
        <div>
          <div class="header-title">Video Library</div>
          <div class="header-subtitle">Florence Melton School of Adult Jewish Learning</div>
        </div>
      </div>
      <div class="header-meta">
        Updated {generated}
      </div>
    </header>

    <div class="stats-bar">
      <div class="stat">
        <span class="stat-num">{total_videos}</span>
        <span class="stat-label">Videos</span>
      </div>
      <div class="stat">
        <span class="stat-num">{total_showcases}</span>
        <span class="stat-label">Showcases</span>
      </div>
    </div>

    <div class="tabs-bar">
      <button class="tab-btn active" onclick="showTab('showcases', this)">Showcases</button>
      <button class="tab-btn" onclick="showTab('all-videos', this)">All Videos</button>
    </div>

    <main>

      <!-- SHOWCASES TAB -->
      <div id="tab-showcases" class="tab-panel active">
        {all_showcases_html if showcases else '<p style="color:var(--gray-text);padding:2rem 0;">No showcases found.</p>'}
      </div>

      <!-- ALL VIDEOS TAB -->
      <div id="tab-all-videos" class="tab-panel">
        <div class="all-videos-card">
          <div class="section-header">All Videos — sorted by date, newest first</div>
          <table class="video-table">
            <thead>
              <tr>
                <th>Title</th>
                <th class="date-col">Date Added</th>
              </tr>
            </thead>
            <tbody>
              {all_videos_html if videos else '<tr><td colspan="2" class="empty-row">No videos found.</td></tr>'}
            </tbody>
          </table>
        </div>
      </div>

    </main>

    <footer class="site-footer">
      <a href="https://meltonschool.org" target="_blank" rel="noopener">meltonschool.org</a>
      &nbsp;·&nbsp; Never stop seeking.
    </footer>

  </div>

  <script>
    const PW_HASH = "{pw_hash}";

    async function sha256(str) {{
      const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
    }}

    async function checkPassword() {{
      const val = document.getElementById("pw-input").value;
      const hash = await sha256(val);
      if (!PW_HASH || hash === PW_HASH) {{
        sessionStorage.setItem("mlv_auth", hash);
        document.getElementById("gate").classList.add("hidden");
        document.getElementById("content").classList.add("visible");
      }} else {{
        const input = document.getElementById("pw-input");
        const err = document.getElementById("gate-error");
        input.classList.add("error");
        err.textContent = "Incorrect passcode. Please try again.";
        setTimeout(() => input.classList.remove("error"), 400);
      }}
    }}

    document.getElementById("pw-input").addEventListener("keydown", e => {{
      if (e.key === "Enter") checkPassword();
    }});

    // Check session on load
    (async () => {{
      const stored = sessionStorage.getItem("mlv_auth");
      if (stored && (!PW_HASH || stored === PW_HASH)) {{
        document.getElementById("gate").classList.add("hidden");
        document.getElementById("content").classList.add("visible");
      }}
    }})();

    function showTab(name, btn) {{
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("tab-" + name).classList.add("active");
      btn.classList.add("active");
    }}
  </script>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"index.html written ({len(html):,} bytes).")
print(f"  {total_videos} videos, {total_showcases} showcases, generated: {generated}")
