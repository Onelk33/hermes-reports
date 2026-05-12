#!/usr/bin/env python3
"""Auto-deploy reports to GitHub Pages"""
import json, os, subprocess, sys, urllib.request

TOKEN = open('/home/onelk/.hermes/.github_token').read().strip()
USER = 'Onelk33'
REPO = 'hermes-reports'

os.chdir('/home/onelk/reports')

# Step 1: Commit and push
subprocess.run(['git', 'add', '-A'], check=True, capture_output=True)
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
if not result.stdout.strip():
    print("ℹ️  Nothing to commit")
    sys.exit(0)

subprocess.run(['git', 'commit', '-m', f'Auto update {__import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")}'], check=True, capture_output=True)
subprocess.run(['git', 'push', 'origin', 'main'], check=True, capture_output=True)
print("✅ Pushed to GitHub")

# Step 2: Trigger Pages rebuild
try:
    req = urllib.request.Request(
        f'https://api.github.com/repos/{USER}/{REPO}/pages/builds',
        data=b'{}',
        method='POST',
        headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    print("✅ Pages build triggered")
except Exception as e:
    print(f"ℹ️  Pages build trigger: {e}")
