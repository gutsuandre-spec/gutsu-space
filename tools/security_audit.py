"""Fail closed on private files/credential signatures. Never print matched values."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SECRET=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AIza[0-9A-Za-z_-]{30,}|xox[baprs]-[0-9A-Za-z-]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{35,}|[0-9]{8,12}:[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
PRIVATE_FILE=re.compile(r'(?i)(?:\.sqlite3?(?:-|$)|\.xlsx?$|\.csv$|\.tsv$|\.pdf$|(?:^|/)\.env(?:\.|$)|(?:^|/)(?:qualification|commercial-funnel|last-daily|catalog-terms|finance-settings|business-settings)\.json$|\.internal\.json$|\.draft\.json$)')
PRIVATE_PUBLIC=re.compile(rb'(?i)(?:"(?:cashless_price|purchase_price|wholesale_price|price_opt_bn|gmail_access_token|refresh_token)"\s*:|SQLite format 3|\b(?:state_must_be_outside|CREATE TABLE sales_leads)\b)')

LEGACY_CSV={'telegram/30d-content-calendar.csv','telegram/30d-metrics.csv'}

def private_filename(name,data):
    if name in LEGACY_CSV: return False  # Historic editorial plan and aggregate targets; reviewed separately.
    if name=='telegram/lead-tracker.csv': return len(data.splitlines())>1
    return bool(PRIVATE_FILE.search(name))

def scan_public(files,root):
    for p in files:
        rel=str(p.relative_to(root)); data=p.read_bytes()
        if PRIVATE_FILE.search(rel) or SECRET.search(data) or PRIVATE_PUBLIC.search(data):
            raise ValueError('private_public_input:'+rel)

def audit(root=ROOT,history=False):
    def git(*args): return subprocess.check_output(['git','-C',str(root),*args])
    findings=[]; scanned=0
    files=git('ls-files','--cached','--others','--exclude-standard','-z').decode().split('\0')
    for name in files:
        if not name: continue
        p=root/name
        if not p.is_file(): continue
        scanned+=1
        if private_filename(name,p.read_bytes()): findings.append({'scope':'working_tree','path':name,'kind':'private_filename'})
        if SECRET.search(p.read_bytes()): findings.append({'scope':'working_tree','path':name,'kind':'credential_signature'})
    blobs=0
    if history:
        for row in git('rev-list','--objects','--all').decode().splitlines():
            parts=row.split(' ',1)
            if len(parts)!=2: continue
            oid,name=parts
            if git('cat-file','-t',oid).strip()!=b'blob': continue
            blobs+=1; data=git('cat-file','blob',oid)
            if SECRET.search(data): findings.append({'scope':'history','path':name,'blob':oid,'kind':'credential_signature'})
            if private_filename(name,data): findings.append({'scope':'history','path':name,'blob':oid,'kind':'private_filename'})
    return {'working_files_scanned':scanned,'history_blobs_scanned':blobs,'findings':findings,
            'limits':'Signature and filename checks do not prove absence of all secrets or personal data; review public business details, CSVs and historic content separately.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--history',action='store_true');a=p.parse_args()
    r=audit(history=a.history); print(json.dumps(r,ensure_ascii=False,indent=2)); raise SystemExit(bool(r['findings']))
