#!/usr/bin/env python3
"""Create GitHub repo and push reports"""
import json, os, subprocess, sys

TOKEN = open('/home/onelk/.hermes/.github_token').read().strip()
REPO_NAME = 'hermes-reports'
USERNAME = 'onelk'

# Step 1: Create repo via API
import urllib.request

data = json.dumps({
    'name': REPO_NAME,
    'description': 'AI & Autonomous Driving Daily Report',
    'homepage': f'https://{USERNAME}.github.io/{REPO_NAME}',
    'private': False
}).encode()

req = urllib.request.Request(
    'https://api.github.com/user/repos',
    data=data,
    headers={
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    result = json.loads(resp.read())
    print(f"✅ Repo created: {result['html_url']}")
except urllib.request.HTTPError as e:
    body = e.read().decode()
    if 'already_exists' in body:
        print("ℹ️  Repo already exists")
    else:
        print(f"❌ Error: {e.code} {body[:200]}")
        sys.exit(1)

# Step 2: Init local git repo
os.chdir('/home/onelk/reports')
if not os.path.exists('.git'):
    subprocess.run(['git', 'init'], check=True, capture_output=True)
    subprocess.run(['git', 'checkout', '-b', 'main'], check=True, capture_output=True)
    print("✅ Git repo initialized")

# Step 3: Add GitHub remote
result = subprocess.run(['git', 'remote', 'get-url', 'origin'], capture_output=True, text=True)
if result.returncode != 0:
    subprocess.run(['git', 'remote', 'add', 'origin', f'https://{USERNAME}:{TOKEN}@github.com/{USERNAME}/{REPO_NAME}.git'], check=True)
    print("✅ Remote added")
else:
    subprocess.run(['git', 'remote', 'set-url', 'origin', f'https://{USERNAME}:{TOKEN}@github.com/{USERNAME}/{REPO_NAME}.git'], check=True)
    print("✅ Remote updated")

# Step 4: Create .gitignore
with open('.gitignore', 'w') as f:
    f.write('serve_reports.py\nstart_server.sh\nkeep_alive.py\nverify_links.py\nsearch.py\n*.pyc\n__pycache__/\n')

# Step 5: Commit and push
subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
if result.stdout.strip():
    subprocess.run(['git', 'commit', '-m', f'Daily report update - {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}'], check=True, capture_output=True)
    subprocess.run(['git', 'push', '-u', 'origin', 'main', '--force'], check=True, capture_output=True)
    print("✅ Pushed to GitHub")
else:
    print("ℹ️  Nothing to commit")

# Step 6: Enable GitHub Pages
pages_data = json.dumps({
    'source': {'branch': 'main', 'path': '/'}
}).encode()
req2 = urllib.request.Request(
    f'https://api.github.com/repos/{USERNAME}/{REPO_NAME}/pages',
    data=pages_data,
    method='POST',
    headers={
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }
)
try:
    resp2 = urllib.request.urlopen(req2, timeout=15)
    print("✅ GitHub Pages enabled")
except urllib.request.HTTPError as e:
    body2 = e.read().decode()
    if 'already' in body2.lower() or 'exists' in body2.lower():
        print("ℹ️  GitHub Pages already configured")
    else:
        print(f"Pages status: {e.code} {body2[:200]}")

print(f"\n🌐 公开访问地址: https://{USERNAME}.github.io/{REPO_NAME}/")
