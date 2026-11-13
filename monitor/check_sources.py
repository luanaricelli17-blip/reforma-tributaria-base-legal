#!/usr/bin/env python3
"""Monitoramento de sinais técnicos; não aprova nem publica legislação."""
import datetime as dt
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "monitor" / "sources.json"
STATE = ROOT / "monitor" / "state.json"
OUT = ROOT / "candidates"
OUT.mkdir(exist_ok=True)
HOSTS = ("gov.br", "planalto.gov.br", "cgibs.gov.br", "in.gov.br", "confaz.fazenda.gov.br")

def official(url):
    u = urlparse(url)
    h = (u.hostname or "").lower()
    return u.scheme == "https" and not u.username and not u.password and any(h == host or h.endswith("." + host) for host in HOSTS)

class StripHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript","svg"): self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ("script","style","noscript","svg"): self.hidden = max(0,self.hidden-1)
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data)

def normalize(raw, content_type):
    text = raw.decode("utf-8", "replace")
    if "html" in content_type.lower() or "<html" in text[:300].lower():
        parser = StripHTML()
        parser.feed(text)
        text = " ".join(parser.parts)
    return re.sub(r"\s+"," ",html.unescape(text)).strip()

def run():
    sources=json.loads(SOURCES.read_text(encoding="utf-8"))
    state=json.loads(STATE.read_text(encoding="utf-8"))
    changed=[]
    failures=[]
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    for src in sources:
        try:
            if not official(src["url"]): raise ValueError("Fonte não autorizada")
            req=urllib.request.Request(src["url"],headers={"User-Agent":"ReformaTributariaMonitor/0.1 (revisao humana)","Accept":"text/html,text/plain"})
            with urllib.request.urlopen(req,timeout=20) as resp:
                if not official(resp.geturl()): raise ValueError("Redirecionamento para domínio não autorizado")
                raw=resp.read(2_000_001)
                if len(raw)>2_000_000: raise ValueError("Fonte excede limite de 2MB")
                body=normalize(raw,resp.headers.get("Content-Type","text/html"))
            if len(body)<80: raise ValueError("Conteúdo insuficiente")
            digest=hashlib.sha256(body.encode("utf-8")).hexdigest()
            if digest!=state.get(src["id"]):
                state[src["id"]]=digest
                (OUT/(src["id"]+".json")).write_text(json.dumps({
                    "source_id":src["id"],"source_name":src["name"],
                    "official_url":src["url"],"sha256":digest,
                    "detected_at":now,"state":"PENDENTE_REVISAO",
                    "warning":"Mudança técnica na página não comprova mudança normativa ou vigência."
                },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
                changed.append(src["id"])
            print("OK",src["id"],"ALTERADA" if src["id"] in changed else "inalterada")
        except Exception as exc:
            failures.append(f"{src['id']}: {type(exc).__name__}: {exc}")
            print("FALHA",failures[-1],file=sys.stderr)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    if failures:
        (OUT/"_falhas-coleta.json").write_text(json.dumps({"status":"FALHAS","items":failures},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    else:
        (OUT/"_falhas-coleta.json").unlink(missing_ok=True)
    print("Alteradas",len(changed),"Falhas",len(failures))
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
