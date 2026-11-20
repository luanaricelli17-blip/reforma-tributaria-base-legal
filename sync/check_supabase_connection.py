#!/usr/bin/env python3
"""Verificação read-only dos Secrets do GitHub Actions para a API do Supabase.

Não grava ou altera dados. Nunca revela valores de Secrets nem conteúdo da resposta.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request

def main():
    base = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_SECRET_KEY", "")
    if not re.fullmatch(r"https://[a-z0-9-]+\.supabase\.co", base):
        raise RuntimeError("SUPABASE_URL não configurada ou formato não permitido.")
    if not key.startswith("sb_secret_"):
        raise RuntimeError("SUPABASE_SECRET_KEY não configurada ou formato inválido.")

    class RejectRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            raise RuntimeError("Supabase retornou redirecionamento; conexão abortada.")

    endpoint = base + "/rest/v1/legal_norm_versions?select=record_id&limit=1"
    req = urllib.request.Request(
        endpoint,
        headers={"apikey": key, "Accept": "application/json"},
        method="GET",
    )
    opener = urllib.request.build_opener(RejectRedirects())
    try:
        with opener.open(req, timeout=20) as response:
            status = response.status
            body = response.read(1024 * 1024)
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Falha na consulta de leitura ao Supabase (HTTP %d)." % exc.code) from None
    except urllib.error.URLError:
        raise RuntimeError("Falha de rede na consulta de leitura ao Supabase.") from None

    if status != 200:
        raise RuntimeError("Supabase respondeu com status inesperado (HTTP %d)." % status)
    try:
        result = json.loads(body)
    except (ValueError, UnicodeError):
        raise RuntimeError("Supabase não retornou JSON válido.") from None
    if not isinstance(result, list):
        raise RuntimeError("Resposta inesperada: a tabela deveria retornar uma lista.")
    print("OK: Supabase API acessível por GET com Secret; tabela legal_norm_versions consultada sem gravar dados.")
    print("Observação: conexão read-only verificada. Permissões de INSERT e publicação efetiva NÃO foram testadas.")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ERRO:", str(exc), file=sys.stderr)
        sys.exit(1)
