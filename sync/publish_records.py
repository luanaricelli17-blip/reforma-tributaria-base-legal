#!/usr/bin/env python3
"""Publica SOMENTE arquivos approved/*.record.json já revisados; sem credenciais no código."""
import json
import os
import sys
import urllib.error
import urllib.request
from validate_records import load_validated

FIELDS={"record_id","document_key","version","norm_type","norm_number","title","summary",
"official_url","reference_label","verified_excerpt","source_id","source_snapshot_sha256",
"retrieved_on","published_on","effective_from","effective_until","applicability","reviewed_by",
"reviewed_at","review_pr_url","publication_state"}

def publish():
    rows=load_validated()
    if not rows:
        print("Nenhum registro aprovado; não há mudanças no Supabase.")
        return
    base=os.environ.get("SUPABASE_URL","").rstrip("/")
    secret=os.environ.get("SUPABASE_SECRET_KEY","")
    if not base.startswith("https://") or not secret.startswith("sb_secret_"):
        raise RuntimeError("Configure SUPABASE_URL e SUPABASE_SECRET_KEY nos Secrets do GitHub, nunca no repositório.")
    endpoint=base+"/rest/v1/legal_norm_versions?on_conflict=record_id"
    for row in rows:
        record={k:row[k] for k in FIELDS if k in row}
        record.setdefault("publication_state","published")
        req=urllib.request.Request(endpoint,data=json.dumps(record,ensure_ascii=False).encode("utf-8"),
          headers={"apikey":secret,"Accept":"application/json","Content-Type":"application/json",
                   "Prefer":"resolution=ignore-duplicates,return=minimal"},
          method="POST")
        try:
            with urllib.request.urlopen(req,timeout=20) as res:
                if res.status not in (200,201,204): raise RuntimeError("HTTP "+str(res.status))
        except urllib.error.HTTPError as e:
            raise RuntimeError("Falha ao publicar "+row["record_id"]+" (HTTP "+str(e.code)+")") from e
        print("Inserido ou já existente:",row["record_id"])

if __name__=="__main__":
    try: publish()
    except Exception as exc:
        print("ERRO:",exc,file=sys.stderr); raise SystemExit(1)
