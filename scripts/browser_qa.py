#!/usr/bin/env python3
"""Compatibility entrypoint for the current consent-aware browser checks."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
for script in ['scripts/functional_qa.py','scripts/audit_browser.py','tests/ab_smoke.py','tests/signup_smoke.py']:
 subprocess.run([sys.executable,str(root/script)],check=True,cwd=root)
