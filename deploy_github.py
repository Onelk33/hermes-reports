#!/usr/bin/env python3
"""Auto-deploy reports to GitHub Pages.
Scans data/report-*.json, generates pure static index.html (no JS), commits and pushes."""
import json, os, subprocess, sys, urllib.request, re, glob
from datetime import datetime

TOKEN = open('/home/onelk/.hermes/.github_token').read().strip()
USER = 'Onelk33'
REPO = 'hermes-reports'
REPORTS_DIR = '/home/onelk/reports'

os.chdir(REPORTS_DIR)

# ── Step 0: discover reports ──────────────────────────────────────────
report_files = sorted(glob.glob('data/report-*.json'), reverse=True)
if not report_files:
    print("❌ No report files found")
    sys.exit(1)

all_reports = []
for f in report_files:
    date_str = f.replace('data/report-', '').replace('.json', '')
    with open(f) as fh:
        data = json.load(fh)
    all_reports.append({'date': date_str, 'data': data})

latest = all_reports[0]
print(f"📄 Latest report: {latest['date']}, {len(all_reports)} total")

# ── Step 1: generate static HTML ──────────────────────────────────────
def esc(s):
    """Basic HTML escape"""
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def render_cards(section_key, items, tag_class, tag_text):
    html = ''
    for item in items:
        html += '<div class="card">\n'
        html += f'<span class="tag {tag_class}">{esc(tag_text)}</span>\n'
        html += '<div class="meta">'
        if section_key == 'expert_opinions' and item.get('speaker'):
            html += f'<span class="speaker">🎤 {esc(item["speaker"])}</span>'
            if item.get('occasion'):
                html += f'<span>{esc(item["occasion"])}</span>'
        if item.get('date'):
            html += f'<span class="date">📅 {esc(item["date"])}</span>'
        html += '</div>\n'
        if section_key == 'expert_opinions' and item.get('title'):
            html += f'<h3>{esc(item["title"])}</h3>\n'
        elif section_key == 'expert_opinions' and item.get('speaker'):
            html += f'<h3>{esc(item["speaker"])}</h3>\n'
        else:
            html += f'<h3>{esc(item["title"])}</h3>\n'
        html += f'<p>{esc(item["summary"])}</p>\n'
        if item.get('link'):
            html += f'<a class="link" href="{esc(item["link"])}" target="_blank" rel="noopener">🔗 阅读原文 <span class="link-arrow">→</span></a>\n'
        html += '</div>\n'
    return html

def generate_index_html(reports):
    """Generate a pure static HTML page."""
    latest_report = reports[0]
    data = latest_report['data']

    # Archive links - point to static archive pages
    archive_links = ''
    for r in reports:
        is_active = r['date'] == latest_report['date']
        cls = ' class="active"' if is_active else ''
        archive_links += f'<a href="archive/report-{r["date"]}.html"{cls}>{r["date"]}</a>\n'

    # Build sections
    sections_html = ''
    section_config = [
        ('tog', '📜', 'To G 趋势洞察', 'AI/自动驾驶政策', 'policy', 'tag-policy', '政策文件'),
        ('industry', '🏭', '行业动态', 'AI &amp; 自动驾驶行业资讯', 'news', 'tag-news', '行业资讯'),
        ('expert_opinions', '🎙️', '大咖观点', '行业领袖公开发言', 'speech', 'tag-speech', '观点摘要'),
        ('reports', '📈', '研报精选', '最新研究报告', 'rpt', 'tag-report', '研究报告'),
    ]

    for key, icon, title, desc, icon_cls, tag_cls, tag_text in section_config:
        items = data['sections'].get(key, [])
        if not items:
            continue
        anchor = 'expert' if key == 'expert_opinions' else key
        sections_html += f'''
<div class="section" id="{anchor}">
<div class="section-header">
<div class="section-icon {icon_cls}">{icon}</div>
<div class="section-title">{title}</div>
<div class="section-desc">{desc}</div>
</div>
{render_cards(key, items, tag_cls, tag_text)}
</div>'''

    nav_items = [
        ('📜 政策', '#tog'), ('🏭 行业动态', '#industry'),
        ('🎙️ 大咖观点', '#expert'), ('📈 研报', '#report'),
        ('📚 历史归档', '#archive'),
    ]
    nav_html = '\n'.join(f'<a href="{h}">{t}</a>' for t, h in nav_items)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>日报 - AI &amp; 自动驾驶</title>
<style>
:root{{--bg:#0f0f1a;--card-bg:#1a1a2e;--text:#e0e0e0;--text-dim:#888;--accent:#4a6cf7;--border:#2a2a4a}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);line-height:1.7;min-height:100vh}}
.header{{background:linear-gradient(135deg,#1a1a3e,#2932E1);padding:40px 20px;text-align:center;border-bottom:3px solid #2932E1}}
.header h1{{font-size:28px;font-weight:700;color:#fff;letter-spacing:2px}}
.header .subtitle{{color:rgba(255,255,255,0.7);font-size:14px;margin-top:8px}}
.header .period{{display:inline-block;background:rgba(255,255,255,0.15);color:#fff;padding:4px 16px;border-radius:20px;font-size:14px;margin-top:12px}}
.nav-bar{{background:var(--card-bg);padding:12px 24px;display:flex;gap:8px;border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100;overflow-x:auto}}
.nav-bar a{{color:var(--text-dim);text-decoration:none;padding:6px 14px;border-radius:6px;font-size:13px;white-space:nowrap;transition:all 0.2s}}
.nav-bar a:hover,.nav-bar a.active{{color:#fff;background:var(--accent)}}
.container{{max-width:960px;margin:0 auto;padding:24px 16px 80px}}
.section{{margin-bottom:40px}}
.section-header{{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:12px;border-bottom:2px solid var(--accent)}}
.section-icon{{width:36px;height:36px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0}}
.section-icon.policy{{background:#e74c3c22}}
.section-icon.news{{background:#3498db22}}
.section-icon.speech{{background:#f39c1222}}
.section-icon.rpt{{background:#2ecc7122}}
.section-title{{font-size:20px;font-weight:700;color:#fff}}
.section-desc{{font-size:13px;color:var(--text-dim);margin-left:auto}}
.card{{background:var(--card-bg);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:16px;transition:border-color 0.2s}}
.card:hover{{border-color:var(--accent)}}
.card .tag{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;margin-bottom:8px}}
.tag-policy{{background:#e74c3c33;color:#e74c3c}}
.tag-news{{background:#3498db33;color:#3498db}}
.tag-speech{{background:#f39c1233;color:#f39c12}}
.tag-report{{background:#2ecc7133;color:#2ecc71}}
.card h3{{font-size:16px;color:#fff;margin-bottom:8px;line-height:1.5}}
.card .meta{{font-size:12px;color:var(--text-dim);margin-bottom:10px;display:flex;flex-wrap:wrap;gap:12px}}
.card .meta .date{{color:#6b8aff}}
.card .meta .speaker{{color:#f39c12}}
.card p{{font-size:14px;color:var(--text);line-height:1.8}}
.card .link{{display:inline-block;margin-top:10px;font-size:13px;color:#6b8aff;text-decoration:none}}
.card .link:hover{{text-decoration:underline}}
.archive-panel{{background:var(--card-bg);border:1px solid var(--border);border-radius:10px;padding:20px;margin-top:40px}}
.archive-panel h3{{font-size:16px;color:#fff;margin-bottom:12px}}
.archive-list{{display:flex;flex-wrap:wrap;gap:8px}}
.archive-list a{{color:#6b8aff;text-decoration:none;padding:4px 12px;border:1px solid var(--border);border-radius:6px;font-size:13px;transition:all 0.2s}}
.archive-list a:hover{{border-color:var(--accent);background:var(--accent);color:#fff}}
.archive-list a.active{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.footer{{text-align:center;padding:30px;color:var(--text-dim);font-size:12px;border-top:1px solid var(--border)}}
@media(max-width:640px){{.header h1{{font-size:22px}}.card{{padding:16px}}}}
</style>
</head>
<body>

<div class="header">
<h1>📊 日报</h1>
<div class="subtitle">AI &amp; 自动驾驶 · 政策 · 行业动态 · 大咖观点 · 研报</div>
<div class="period">📅 {esc(data['cover_period'])}</div>
</div>

<div class="nav-bar">
{nav_html}
</div>

<div class="container">
{sections_html}

<div class="archive-panel" id="archive">
<h3>📚 历史日报归档</h3>
<div class="archive-list">
{archive_links}
</div>
<p style="color:var(--text-dim);font-size:13px;margin-top:12px;">点击日期切换查看各期日报。</p>
</div>

</div>

<div class="footer">
<p>日报 · 每日自动生成 · 保留所有历史版本</p>
<p style="margin-top:4px;">数据来源：公开政策文件、新闻资讯及研究报告 · 所有链接均需可验证</p>
</div>

</body>
</html>'''

def generate_static_pages(reports):
    """Generate static HTML pages for all reports."""
    # 1. Write index.html with the latest report
    index_html = generate_index_html(reports)
    with open('index.html', 'w') as f:
        f.write(index_html)
    print(f"✅ Generated index.html ({len(index_html)} bytes) - latest: {reports[0]['date']}")

    # 2. Generate archive pages for each report
    for r in reports:
        page_html = generate_index_html([r])
        filename = f'report-{r["date"]}.html'
        filepath = os.path.join('archive', filename)
        os.makedirs('archive', exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(page_html)
        print(f"   Archive: {filename}")

    print(f"✅ Generated {len(reports)} archive pages")

# ── Step 2: commit & push ─────────────────────────────────────────────
generate_static_pages(all_reports)

subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
if not result.stdout.strip():
    print("ℹ️ Nothing to commit")
    sys.exit(0)

subprocess.run(['git', 'commit', '-m', f'Auto update {datetime.now().strftime("%Y-%m-%d %H:%M")} - {latest["date"]}'],
               check=True, capture_output=True)
subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
print("✅ Pushed to GitHub")

# ── Step 3: trigger Pages rebuild ─────────────────────────────────────
try:
    req = urllib.request.Request(
        f'https://api.github.com/repos/{USER}/{REPO}/pages/builds',
        data=b'{}', method='POST',
        headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    print("✅ Pages build triggered")
except Exception as e:
    print(f"ℹ️ Pages build trigger: {e}")
