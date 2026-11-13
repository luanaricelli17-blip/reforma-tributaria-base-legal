#!/usr/bin/env python3
"""Validação estrutural e de proveniência. Exige revisão jurídica humana independente."""
import datetime as dt
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parent.parent
OFFICIAL=("gov.br","planalto.gov.br","cgibs.gov.br","in.gov.br","confaz.fazenda.gov.br")
REQUIRED=("record_id","document_key","version","norm_type","norm_number","title","summary",
 "official_url","reference_label","verified_excerpt","source_id","source_snapshot_sha256",
 "retrieved_on","published_on","effective_from","applicability","reviewed_by","reviewed_at","review_pr_url")

def official(url):
    u=urlparse(url)
    h=(u.hostname or "").lower()
    return u.scheme=="https" and not u.username and not u.password and any(h==x or h.endswith("."+x) for x in OFFICIAL)

def validate(row, state):
    missing=[k for k in REQUIRED if not row.get(k)]
    if missing: raise ValueError("Campos obrigatórios ausentes: "+", ".join(missing))
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{5,90}",row["record_id"]): raise ValueError("ID inválido")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{3,70}",row["document_key"]): raise ValueError("Chave do documento inválida")
    if type(row["version"]) is not int or row["version"]<1: raise ValueError("Versão inválida")
    if not official(row["official_url"]): raise ValueError("URL não oficial")
    if len(row["summary"])<20 or len(row["verified_excerpt"])<30: raise ValueError("Resumo ou trecho insuficiente")
    if not re.fullmatch(r"[a-f0-9]{64}",row["source_snapshot_sha256"]): raise ValueError("SHA256 da fonte inválido")
    if state.get(row["source_id"])!=row["source_snapshot_sha256"]: raise ValueError("Fonte divergente de monitor/state.json: revisão necessária")
    for k in ("retrieved_on","published_on","effective_from"):
        dt.date.fromisoformat(row[k])
    if row.get("effective_until"):
        dt.date.fromisoformat(row["effective_until"])
        if row["effective_until"]<=row["effective_from"]: raise ValueError("Intervalo de vigência invertido")
    reviewed=dt.datetime.fromisoformat(row["reviewed_at"])
    if reviewed.tzinfo is None: raise ValueError("Revisão exige data com fuso")
    pr=urlparse(row["review_pr_url"])
    if pr.scheme!="https" or pr.hostname!="github.com" or "/pull/" not in pr.path: raise ValueError("PR de revisão inválido")
    if "autom" in row["reviewed_by"].lower(): raise ValueError("Revisão humana obrigatória")
    if row.get("publication_state","published")!="published": raise ValueError("Publicação não aprovada")
    allowed=set(REQUIRED)|{"effective_until","publication_state"}
    extra=set(row)-allowed
    if extra: raise ValueError("Campos inesperados: "+", ".join(sorted(extra)))
    return row

def load_validated():
    state=json.loads((ROOT/"monitor/state.json").read_text(encoding="utf-8"))
    all_rows=[]; ids=set(); versions=set()
    for path in sorted((ROOT/"approved").glob("*.record.json")):
        row=validate(json.loads(path.read_text(encoding="utf-8")),state)
        key=(row["document_key"],row["version"])
        if row["record_id"] in ids or key in versions: raise ValueError("Registro ou versão duplicada: "+path.name)
        ids.add(row["record_id"]); versions.add(key); all_rows.append(row)
    return all_rows

if __name__=="__main__":
    rows=load_validated()
    print("Validação estrutural OK:",len(rows),"registros; revisão jurídica humana é separada")
