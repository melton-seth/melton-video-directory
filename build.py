#!/usr/bin/env python3
"""
build.py
Reads data.json and renders the Melton Video Directory index.html.
The SITE_PASSWORD is injected at build time via environment variable.
"""

import json
import os
import hashlib

SITE_PASSWORD = os.environ.get("SITE_PASSWORD", "")
if not SITE_PASSWORD:
    import sys
    print("WARNING: SITE_PASSWORD not set.", file=sys.stderr)

pw_hash = hashlib.sha256(SITE_PASSWORD.encode()).hexdigest() if SITE_PASSWORD else ""

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

generated = data.get("generated", "")
videos = data.get("videos", [])
showcases = data.get("showcases", [])

COPY_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
LINK_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'
CHEV_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>'


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")


def attr(s):
    return s.replace("'", "&#39;").replace('"', "&quot;")


def video_row(v, context="all"):
    title = esc(v["title"])
    title_attr = attr(v["title"])
    url = v["url"]
    date = v["date"]
    date_raw = v.get("date_raw", "")
    description = (v.get("description") or "").strip()

    disc_btn = (
        f'<button class="desc-toggle" onclick="toggleDesc(this)" aria-expanded="false" title="Show description">'
        f'{CHEV_SVG}</button>'
    ) if description else '<span class="desc-toggle-placeholder"></span>'

    desc_row = (
        f'<tr class="desc-row" hidden>'
        f'<td colspan="4" class="desc-cell">{esc(description)}</td>'
        f'</tr>'
    ) if description else ""

    row = (
        f'<tr data-title="{esc(v["title"].lower())}" data-date="{date_raw}" data-context="{context}">'
        f'<td class="title-cell">{disc_btn}<a href="{url}" target="_blank" rel="noopener">{title}</a></td>'
        f'<td class="date-col">{date}</td>'
        f'<td class="copy-col">'
        f'<button class="copy-btn copy-url" data-url="{url}" title="Copy link" aria-label="Copy link">{COPY_SVG}</button>'
        f'<button class="copy-btn copy-md" data-url="{url}" data-title="{title_attr}" title="Copy as Markdown" aria-label="Copy as Markdown">{LINK_SVG}</button>'
        f'</td>'
        f'</tr>'
        f'{desc_row}'
    )
    return row


def showcase_section(s, idx):
    title = esc(s["title"])
    title_attr = attr(s["title"])
    url = s["url"]
    count = len(s["videos"])
    count_label = f"{count} video{'s' if count != 1 else ''}"
    rows = "".join(video_row(v, "showcase") for v in s["videos"]) if s["videos"] else \
        '<tr><td colspan="4" class="empty-row">No videos in this showcase.</td></tr>'

    return (
        f'<section class="showcase-section" data-showcase-idx="{idx}">'
        f'<button class="showcase-header" onclick="toggleShowcase(this)" aria-expanded="false">'
        f'<div class="showcase-title-row">'
        f'<span class="showcase-chevron">{CHEV_SVG}</span>'
        f'<span class="showcase-title"><a href="{url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">{title}</a></span>'
        f'<span class="showcase-count">{count_label}</span>'
        f'<span class="showcase-copy-btns">'
        f'<button class="copy-btn copy-url showcase-copy" data-url="{url}" title="Copy showcase link" aria-label="Copy showcase link" onclick="event.stopPropagation()">{COPY_SVG}</button>'
        f'<button class="copy-btn copy-md showcase-copy" data-url="{url}" data-title="{title_attr}" title="Copy as Markdown" aria-label="Copy showcase as Markdown" onclick="event.stopPropagation()">{LINK_SVG}</button>'
        f'</span>'
        f'</div>'
        f'</button>'
        f'<div class="showcase-body" hidden>'
        f'<table class="video-table">'
        f'<thead><tr><th>Title</th><th class="date-col">Date Added</th><th class="copy-col"></th></tr></thead>'
        f'<tbody>{rows}</tbody>'
        f'</table>'
        f'</div>'
        f'</section>'
    )


all_videos_html = "".join(video_row(v, "all") for v in videos)
all_showcases_html = "".join(showcase_section(s, i) for i, s in enumerate(showcases))
total_videos = len(videos)
total_showcases = len(showcases)

videos_json = json.dumps([{"date_raw": v.get("date_raw", "")} for v in videos])
showcase_videos_json = json.dumps([
    {"date_raw": v.get("date_raw", "")}
    for s in showcases for v in s["videos"]
])

# ── CSS (safe to use {{ }} escaping since no user content here) ──
CSS = """
    :root {
      --blue: #0042b9; --blue-dark: #002f85; --blue-mid: #377fe2;
      --blue-light: #7bafde; --blue-pale: #d4f0ed; --orange: #f4773b;
      --white: #ffffff; --gray-bg: #f4f6fb; --gray-border: #dce4f0;
      --gray-text: #5a6a82; --text: #1a243a; --green: #22c55e;
      --font: 'Nunito', 'Segoe UI', sans-serif; --radius: 10px;
      --shadow: 0 2px 16px rgba(0,66,185,0.10);
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: var(--font); background: var(--gray-bg); color: var(--text); min-height: 100vh; }
    #gate { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; background: var(--blue); padding: 2rem; }
    #gate.hidden { display: none; }
    .gate-card { background: var(--white); border-radius: 16px; padding: 3rem 2.5rem 2.5rem; max-width: 380px; width: 100%; text-align: center; box-shadow: 0 8px 40px rgba(0,0,0,0.25); }
    .gate-logo { width: 120px; margin-bottom: 1.5rem; }
    .gate-card h1 { font-size: 1.4rem; font-weight: 800; color: var(--blue); margin-bottom: 0.4rem; }
    .gate-card p { font-size: 0.9rem; color: var(--gray-text); margin-bottom: 1.8rem; }
    .gate-input { width: 100%; padding: 0.8rem 1rem; font-size: 1rem; font-family: var(--font); border: 2px solid var(--gray-border); border-radius: var(--radius); outline: none; transition: border-color 0.2s; margin-bottom: 1rem; text-align: center; letter-spacing: 0.1em; }
    .gate-input:focus { border-color: var(--blue); }
    .gate-input.error { border-color: #e53e3e; animation: shake 0.3s ease; }
    @keyframes shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-6px); } 75% { transform: translateX(6px); } }
    .gate-btn { width: 100%; padding: 0.85rem; background: var(--blue); color: var(--white); font-family: var(--font); font-size: 1rem; font-weight: 700; border: none; border-radius: var(--radius); cursor: pointer; transition: background 0.2s; }
    .gate-btn:hover { background: var(--blue-dark); }
    .gate-error { margin-top: 0.75rem; font-size: 0.85rem; color: #e53e3e; min-height: 1.2em; }
    #content { display: none; }
    #content.visible { display: block; }
    .site-header { background: var(--white); border-bottom: 3px solid var(--blue); padding: 1.2rem 2rem; display: flex; align-items: center; justify-content: space-between; gap: 1rem; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 12px rgba(0,66,185,0.08); }
    .header-left { display: flex; align-items: center; gap: 1.2rem; }
    .header-logo { height: 52px; width: auto; }
    .header-divider { width: 2px; height: 40px; background: var(--gray-border); }
    .header-title { font-size: 1.25rem; font-weight: 800; color: var(--blue); letter-spacing: -0.01em; }
    .header-subtitle { font-size: 0.8rem; color: var(--gray-text); font-weight: 600; margin-top: 1px; }
    .header-meta { font-size: 0.78rem; color: var(--gray-text); text-align: right; }
    .stats-bar { background: var(--blue); color: var(--white); display: flex; gap: 2rem; padding: 0.8rem 2rem; }
    .stat { display: flex; align-items: baseline; gap: 0.4rem; }
    .stat-num { font-size: 1.4rem; font-weight: 800; }
    .stat-label { font-size: 0.8rem; opacity: 0.8; font-weight: 600; }
    .tabs-bar { background: var(--white); border-bottom: 2px solid var(--gray-border); display: flex; padding: 0 2rem; }
    .tab-btn { padding: 1rem 1.5rem; font-family: var(--font); font-size: 0.9rem; font-weight: 700; color: var(--gray-text); background: none; border: none; border-bottom: 3px solid transparent; margin-bottom: -2px; cursor: pointer; transition: color 0.2s, border-color 0.2s; }
    .tab-btn:hover { color: var(--blue); }
    .tab-btn.active { color: var(--blue); border-bottom-color: var(--orange); }
    .filter-bar { background: var(--white); border-bottom: 1px solid var(--gray-border); padding: 0.75rem 2rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
    .search-wrap { position: relative; flex: 1; min-width: 200px; max-width: 360px; }
    .search-wrap svg { position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); width: 16px; height: 16px; color: var(--gray-text); pointer-events: none; }
    .search-input { width: 100%; padding: 0.55rem 0.75rem 0.55rem 2.2rem; font-family: var(--font); font-size: 0.88rem; border: 1.5px solid var(--gray-border); border-radius: var(--radius); outline: none; transition: border-color 0.2s; background: var(--gray-bg); }
    .search-input:focus { border-color: var(--blue); background: var(--white); }
    .filter-select { padding: 0.55rem 0.75rem; font-family: var(--font); font-size: 0.88rem; border: 1.5px solid var(--gray-border); border-radius: var(--radius); outline: none; background: var(--gray-bg); color: var(--text); cursor: pointer; }
    .filter-clear { padding: 0.5rem 0.9rem; font-family: var(--font); font-size: 0.82rem; font-weight: 700; color: var(--gray-text); background: none; border: 1.5px solid var(--gray-border); border-radius: var(--radius); cursor: pointer; transition: all 0.2s; white-space: nowrap; }
    .filter-clear:hover { color: var(--blue); border-color: var(--blue); }
    .filter-results { font-size: 0.8rem; color: var(--gray-text); margin-left: auto; white-space: nowrap; }
    main { max-width: 1000px; margin: 0 auto; padding: 2rem; }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .showcase-section { background: var(--white); border-radius: var(--radius); box-shadow: var(--shadow); margin-bottom: 1rem; overflow: hidden; border: 1px solid var(--gray-border); }
    .showcase-header { width: 100%; background: var(--blue); padding: 0.9rem 1.5rem; border: none; cursor: pointer; text-align: left; transition: background 0.15s; }
    .showcase-header:hover { background: var(--blue-dark); }
    .showcase-title-row { display: flex; align-items: center; gap: 0.75rem; }
    .showcase-chevron { flex-shrink: 0; width: 18px; height: 18px; color: rgba(255,255,255,0.7); transition: transform 0.2s; }
    .showcase-chevron svg { width: 100%; height: 100%; }
    .showcase-header[aria-expanded="true"] .showcase-chevron { transform: rotate(90deg); }
    .showcase-title { font-size: 1rem; font-weight: 800; color: var(--white); flex: 1; min-width: 0; }
    .showcase-title a { color: inherit; text-decoration: none; }
    .showcase-title a:hover { text-decoration: underline; opacity: 0.9; }
    .showcase-count { font-size: 0.75rem; font-weight: 700; background: rgba(255,255,255,0.2); color: var(--white); padding: 0.2rem 0.65rem; border-radius: 20px; white-space: nowrap; }
    .showcase-copy-btns { display: flex; gap: 2px; flex-shrink: 0; }
    .showcase-copy { color: rgba(255,255,255,0.5) !important; }
    .showcase-copy:hover { color: var(--white) !important; background: rgba(255,255,255,0.15) !important; }
    .video-table { width: 100%; border-collapse: collapse; }
    .video-table thead tr { background: var(--blue-pale); }
    .video-table th { padding: 0.6rem 1.2rem; font-size: 0.72rem; font-weight: 800; color: var(--blue); text-transform: uppercase; letter-spacing: 0.06em; text-align: left; }
    .video-table td { padding: 0.7rem 1.2rem; font-size: 0.9rem; border-bottom: 1px solid var(--gray-border); vertical-align: middle; }
    .video-table tbody tr:last-child td { border-bottom: none; }
    .video-table tbody tr:hover { background: #f0f5ff; }
    .video-table tbody tr.hidden { display: none; }
    .video-table a { color: var(--blue); text-decoration: none; font-weight: 600; }
    .video-table a:hover { color: var(--orange); text-decoration: underline; }
    .date-col { white-space: nowrap; color: var(--gray-text); font-size: 0.82rem; width: 150px; }
    .copy-col { width: 68px; text-align: right; white-space: nowrap; overflow: visible; }
    .empty-row { color: var(--gray-text); font-style: italic; text-align: center; padding: 1.5rem !important; }
    .no-results-row { display: none; }
    .no-results-row.visible { display: table-row; }
    .title-cell { display: flex; align-items: center; gap: 0.4rem; }
    .desc-toggle { background: none; border: none; cursor: pointer; padding: 0.2rem; border-radius: 4px; color: var(--blue-light); transition: color 0.15s, transform 0.2s; flex-shrink: 0; display: flex; align-items: center; }
    .desc-toggle svg { width: 14px; height: 14px; }
    .desc-toggle:hover { color: var(--blue); }
    .desc-toggle[aria-expanded="true"] { transform: rotate(90deg); color: var(--blue); }
    .desc-toggle-placeholder { display: inline-block; width: 22px; flex-shrink: 0; }
    .desc-row td { padding: 0 !important; }
    .desc-cell { padding: 0.6rem 1.2rem 0.8rem 3rem !important; font-size: 0.85rem; color: var(--gray-text); background: #f8faff; line-height: 1.6; white-space: pre-wrap; }
    .video-table tbody tr.desc-row { background: #f8faff; }
    .video-table tbody tr.desc-row:hover { background: #f8faff; }
    .copy-btn { background: none; border: none; cursor: pointer; padding: 0.3rem; border-radius: 6px; color: var(--blue-light); transition: color 0.15s, background 0.15s; position: relative; display: inline-flex; align-items: center; justify-content: center; }
    .copy-btn svg { width: 15px; height: 15px; }
    .copy-btn:hover { color: var(--blue); background: var(--blue-pale); }
    .copy-btn.copied { color: var(--green); }
    .copy-btn .tooltip { position: absolute; bottom: calc(100% + 6px); right: 0; background: var(--text); color: var(--white); font-size: 0.72rem; font-family: var(--font); padding: 0.25rem 0.5rem; border-radius: 4px; white-space: nowrap; pointer-events: none; opacity: 0; transition: opacity 0.15s; z-index: 200; }
    .copy-btn:hover .tooltip { opacity: 1; }
    .all-videos-card { background: var(--white); border-radius: var(--radius); box-shadow: var(--shadow); border: 1px solid var(--gray-border); overflow: hidden; }
    .all-videos-card .section-header { background: var(--blue); padding: 1rem 1.5rem; color: var(--white); font-size: 1.05rem; font-weight: 800; }
    .site-footer { text-align: center; padding: 2rem; font-size: 0.78rem; color: var(--gray-text); }
    .site-footer a { color: var(--blue-mid); text-decoration: none; }
    @media (max-width: 600px) {
      .site-header { padding: 1rem; flex-wrap: wrap; }
      main { padding: 1rem; }
      .stats-bar { gap: 1rem; padding: 0.8rem 1rem; flex-wrap: wrap; }
      .date-col { display: none; }
      .tabs-bar { padding: 0 0.5rem; }
      .filter-bar { padding: 0.75rem 1rem; }
    }
"""

# ── JavaScript (safe — no user content interpolated here) ──
JS = """
    const PW_HASH = "PWHASH_PLACEHOLDER";
    const allVideoDates = ALLVIDEODATES_PLACEHOLDER;
    const showcaseVideoDates = SHOWCASEVIDEODATES_PLACEHOLDER;

    function getFY(d) {
      if (!d) return null;
      const dt = new Date(d), y = dt.getUTCFullYear(), m = dt.getUTCMonth();
      return m >= 6 ? y + 1 : y;
    }
    function getFYQ(d) {
      if (!d) return null;
      const m = new Date(d).getUTCMonth();
      if (m >= 6 && m <= 8)  return 1;
      if (m >= 9 && m <= 11) return 2;
      if (m >= 0 && m <= 2)  return 3;
      return 4;
    }

    let filtersInitialized = false;
    function initFilters() {
      if (filtersInitialized) return;
      filtersInitialized = true;
      const allDates = [...allVideoDates, ...showcaseVideoDates].map(v => v.date_raw).filter(Boolean);
      const fySet = new Set(), monthSet = new Set();
      allDates.forEach(d => {
        const fy = getFY(d); if (fy) fySet.add(fy);
        monthSet.add(new Date(d).getUTCMonth());
      });
      const fyEl = document.getElementById("filter-fy");
      [...fySet].sort((a,b) => b-a).forEach(fy => {
        const o = document.createElement("option"); o.value = fy; o.textContent = "FY" + fy; fyEl.appendChild(o);
      });
      const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
      const monthEl = document.getElementById("filter-month");
      [6,7,8,9,10,11,0,1,2,3,4,5].filter(m => monthSet.has(m)).forEach(m => {
        const o = document.createElement("option"); o.value = m; o.textContent = monthNames[m]; monthEl.appendChild(o);
      });
      document.querySelectorAll(".copy-url").forEach(btn => {
        const t = document.createElement("span"); t.className = "tooltip";
        t.textContent = btn.classList.contains("showcase-copy") ? "Copy showcase link" : "Copy link";
        btn.appendChild(t);
      });
      document.querySelectorAll(".copy-md").forEach(btn => {
        const t = document.createElement("span"); t.className = "tooltip"; t.textContent = "Copy as Markdown"; btn.appendChild(t);
      });
    }

    async function sha256(str) {
      const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(str));
      return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2,"0")).join("");
    }
    async function checkPassword() {
      const val = document.getElementById("pw-input").value;
      const hash = await sha256(val);
      if (!PW_HASH || hash === PW_HASH) {
        sessionStorage.setItem("mlv_auth", hash);
        document.getElementById("gate").classList.add("hidden");
        document.getElementById("content").classList.add("visible");
        initFilters();
      } else {
        const input = document.getElementById("pw-input");
        input.classList.add("error");
        document.getElementById("gate-error").textContent = "Incorrect passcode. Please try again.";
        setTimeout(() => input.classList.remove("error"), 400);
      }
    }
    document.getElementById("pw-input").addEventListener("keydown", e => { if (e.key === "Enter") checkPassword(); });
    (async () => {
      const stored = sessionStorage.getItem("mlv_auth");
      if (stored && (!PW_HASH || stored === PW_HASH)) {
        document.getElementById("gate").classList.add("hidden");
        document.getElementById("content").classList.add("visible");
        initFilters();
      }
    })();

    function showTab(name, btn) {
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.getElementById("tab-" + name).classList.add("active");
      btn.classList.add("active");
      applyFilters();
    }
    function toggleShowcase(btn) {
      const body = btn.nextElementSibling;
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      body.hidden = expanded;
    }
    function toggleDesc(btn) {
      const mainRow = btn.closest("tr");
      const descRow = mainRow.nextElementSibling;
      if (!descRow || !descRow.classList.contains("desc-row")) return;
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      descRow.hidden = expanded;
    }
    function getActiveTab() {
      return document.querySelector(".tab-panel.active").id === "tab-showcases" ? "showcases" : "all";
    }
    function applyFilters() {
      const q = document.getElementById("search-input").value.trim().toLowerCase();
      const fy = document.getElementById("filter-fy").value;
      const quarter = document.getElementById("filter-q").value;
      const month = document.getElementById("filter-month").value;
      const tab = getActiveTab();
      function rowMatches(row) {
        const title = row.dataset.title || "";
        const dateRaw = row.dataset.date || "";
        if (q && !title.includes(q)) return false;
        if (fy && getFY(dateRaw) != fy) return false;
        if (quarter && getFYQ(dateRaw) != quarter) return false;
        if (month !== "" && new Date(dateRaw).getUTCMonth() != month) return false;
        return true;
      }
      if (tab === "all") {
        const rows = document.querySelectorAll("#tab-all-videos tbody tr[data-title]");
        let visible = 0;
        rows.forEach(row => {
          const show = rowMatches(row);
          row.classList.toggle("hidden", !show);
          const next = row.nextElementSibling;
          if (next && next.classList.contains("desc-row")) next.classList.toggle("hidden", !show);
          if (show) visible++;
        });
        document.getElementById("all-no-results").classList.toggle("visible", visible === 0);
        updateResultsLabel(visible, rows.length);
      } else {
        let totalVisible = 0, totalRows = 0;
        document.querySelectorAll(".showcase-section").forEach(section => {
          const rows = section.querySelectorAll("tbody tr[data-title]");
          let vis = 0;
          rows.forEach(row => {
            const show = rowMatches(row);
            row.classList.toggle("hidden", !show);
            const next = row.nextElementSibling;
            if (next && next.classList.contains("desc-row")) next.classList.toggle("hidden", !show);
            if (show) vis++;
          });
          totalVisible += vis; totalRows += rows.length;
          const hasFilter = q || fy || quarter || month !== "";
          section.style.display = (hasFilter && vis === 0 && rows.length > 0) ? "none" : "";
          if (hasFilter && vis > 0) {
            section.querySelector(".showcase-header").setAttribute("aria-expanded", "true");
            section.querySelector(".showcase-body").hidden = false;
          }
        });
        updateResultsLabel(totalVisible, totalRows);
      }
    }
    function updateResultsLabel(visible, total) {
      const el = document.getElementById("filter-results");
      const hasFilter = document.getElementById("search-input").value.trim() ||
        document.getElementById("filter-fy").value ||
        document.getElementById("filter-q").value ||
        document.getElementById("filter-month").value !== "";
      el.textContent = hasFilter ? (visible + " of " + total + " videos") : "";
    }
    function clearFilters() {
      document.getElementById("search-input").value = "";
      document.getElementById("filter-fy").value = "";
      document.getElementById("filter-q").value = "";
      document.getElementById("filter-month").value = "";
      applyFilters();
      document.querySelectorAll(".showcase-header").forEach(btn => {
        btn.setAttribute("aria-expanded", "false");
        btn.nextElementSibling.hidden = true;
      });
      document.querySelectorAll(".showcase-section").forEach(s => s.style.display = "");
    }
    document.addEventListener("click", e => {
      const btn = e.target.closest(".copy-btn");
      if (!btn) return;
      const url = btn.dataset.url;
      const text = btn.classList.contains("copy-md") ? ("[" + (btn.dataset.title || url) + "](" + url + ")") : url;
      navigator.clipboard.writeText(text).then(() => {
        btn.classList.add("copied");
        const tip = btn.querySelector(".tooltip");
        if (tip) tip.textContent = "Copied!";
        setTimeout(() => {
          btn.classList.remove("copied");
          if (tip) tip.textContent = btn.classList.contains("copy-md") ? "Copy as Markdown" :
            (btn.classList.contains("showcase-copy") ? "Copy showcase link" : "Copy link");
        }, 1500);
      });
    });
"""

# Replace placeholders with actual values (safe — JSON has no {{ }} issues)
JS = JS.replace("PWHASH_PLACEHOLDER", pw_hash)
JS = JS.replace("ALLVIDEODATES_PLACEHOLDER", videos_json)
JS = JS.replace("SHOWCASEVIDEODATES_PLACEHOLDER", showcase_videos_json)

# ── Assemble HTML via concatenation — no f-string over user content ──
html = (
    '<!DOCTYPE html>\n'
    '<html lang="en">\n'
    '<head>\n'
    '  <meta charset="UTF-8" />\n'
    '  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
    '  <title>Melton Video Library</title>\n'
    '  <link rel="icon" type="image/png" sizes="32x32" href="melton-logo.png" />\n'
    '  <link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700;800&display=swap" rel="stylesheet" />\n'
    '  <style>\n' + CSS + '\n  </style>\n'
    '</head>\n'
    '<body>\n'
    '\n'
    '  <div id="gate">\n'
    '    <div class="gate-card">\n'
    '      <img src="melton-logo.png" alt="Melton" class="gate-logo" />\n'
    '      <h1>Video Library</h1>\n'
    '      <p>Enter the access code to continue.</p>\n'
    '      <input type="password" id="pw-input" class="gate-input" placeholder="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022" autocomplete="current-password" />\n'
    '      <button class="gate-btn" onclick="checkPassword()">Enter</button>\n'
    '      <div class="gate-error" id="gate-error"></div>\n'
    '    </div>\n'
    '  </div>\n'
    '\n'
    '  <div id="content">\n'
    '    <header class="site-header">\n'
    '      <div class="header-left">\n'
    '        <img src="melton-logo.png" alt="Melton" class="header-logo" />\n'
    '        <div class="header-divider"></div>\n'
    '        <div>\n'
    '          <div class="header-title">Video Library</div>\n'
    '          <div class="header-subtitle">Florence Melton School of Adult Jewish Learning</div>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="header-meta">Updated ' + generated + '</div>\n'
    '    </header>\n'
    '    <div class="stats-bar">\n'
    '      <div class="stat"><span class="stat-num">' + str(total_videos) + '</span><span class="stat-label">Videos</span></div>\n'
    '      <div class="stat"><span class="stat-num">' + str(total_showcases) + '</span><span class="stat-label">Showcases</span></div>\n'
    '    </div>\n'
    '    <div class="tabs-bar">\n'
    '      <button class="tab-btn active" onclick="showTab(\'all-videos\', this)">All Videos</button>\n'
    '      <button class="tab-btn" onclick="showTab(\'showcases\', this)">Showcases</button>\n'
    '    </div>\n'
    '    <div class="filter-bar">\n'
    '      <div class="search-wrap">\n'
    '        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>\n'
    '        <input type="search" id="search-input" class="search-input" placeholder="Search videos\u2026" oninput="applyFilters()" />\n'
    '      </div>\n'
    '      <select id="filter-fy" class="filter-select" onchange="applyFilters()"><option value="">All Years</option></select>\n'
    '      <select id="filter-q" class="filter-select" onchange="applyFilters()">\n'
    '        <option value="">All Quarters</option>\n'
    '        <option value="1">Q1 (Jul\u2013Sep)</option>\n'
    '        <option value="2">Q2 (Oct\u2013Dec)</option>\n'
    '        <option value="3">Q3 (Jan\u2013Mar)</option>\n'
    '        <option value="4">Q4 (Apr\u2013Jun)</option>\n'
    '      </select>\n'
    '      <select id="filter-month" class="filter-select" onchange="applyFilters()"><option value="">All Months</option></select>\n'
    '      <button class="filter-clear" onclick="clearFilters()">Clear</button>\n'
    '      <span class="filter-results" id="filter-results"></span>\n'
    '    </div>\n'
    '    <main>\n'
    '      <div id="tab-all-videos" class="tab-panel active">\n'
    '        <div class="all-videos-card">\n'
    '          <div class="section-header">All Videos \u2014 sorted by date, newest first</div>\n'
    '          <table class="video-table" id="all-videos-table">\n'
    '            <thead><tr><th>Title</th><th class="date-col">Date Added</th><th class="copy-col"></th></tr></thead>\n'
    '            <tbody>\n'
    + (all_videos_html if videos else '<tr><td colspan="4" class="empty-row">No videos found.</td></tr>') +
    '\n              <tr class="no-results-row" id="all-no-results"><td colspan="4" class="empty-row">No videos match your filters.</td></tr>\n'
    '            </tbody>\n'
    '          </table>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div id="tab-showcases" class="tab-panel">\n'
    + (all_showcases_html if showcases else '<p style="color:#5a6a82;padding:2rem 0;">No showcases found.</p>') +
    '\n      </div>\n'
    '    </main>\n'
    '    <footer class="site-footer">\n'
    '      <a href="https://meltonschool.org" target="_blank" rel="noopener">meltonschool.org</a>\n'
    '      &nbsp;\u00b7&nbsp; Never stop seeking.\n'
    '    </footer>\n'
    '  </div>\n'
    '\n'
    '  <script>\n' + JS + '\n  </script>\n'
    '\n'
    '</body>\n'
    '</html>\n'
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"index.html written ({len(html):,} bytes).")
print(f"  {total_videos} videos, {total_showcases} showcases, generated: {generated}")
