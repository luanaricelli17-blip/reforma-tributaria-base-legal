#!/usr/bin/env python3
"""Diagnóstico do MCP em produção, 100% somente leitura e sem credenciais.

Valida health, negociação MCP, descoberta de ferramentas e leitura do registro público.
"""
import json
import urllib.error
import urllib.request

BASE = "https://rtc-consulta-oficial-mcp.luana-ricelli17.workers.dev"
EXPECTED_ID = "lc214-2025-art1-v1"
PROTOCOL = "2025-11-25"
session = None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, hdrs, newurl):
        raise RuntimeError("Redirecionamento não autorizado no endpoint do MCP")


opener = urllib.request.build_opener(NoRedirect)


def send(path, obj=None):
    global session
    headers = {"Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    if obj is None:
        req = urllib.request.Request(BASE + path, headers=headers, method="GET")
    else:
        headers.update({"Content-Type": "application/json", "MCP-Protocol-Version": PROTOCOL})
        req = urllib.request.Request(
            BASE + path,
            data=json.dumps(obj).encode("utf-8"),
            headers=headers,
            method="POST",
        )
    try:
        with opener.open(req, timeout=20) as response:
            status = response.status
            if response.headers.get("Mcp-Session-Id"):
                session = response.headers.get("Mcp-Session-Id")
            content_type = response.headers.get("Content-Type", "")
            data = response.read(500000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        server = e.headers.get("Server", "não informado")
        mitigated = e.headers.get("cf-mitigated", "não informado")
        auth = bool(e.headers.get("WWW-Authenticate"))
        kind = e.headers.get("Content-Type", "não informado")
        raise RuntimeError(
            "Endpoint %s retornou HTTP %s (server=%s, cf-mitigated=%s, www-authenticate=%s, content-type=%s)"
            % (path, e.code, server, mitigated, auth, kind)
        ) from None
    except urllib.error.URLError:
        raise RuntimeError("Falha de rede ao acessar %s" % path) from None
    if status == 202 and not data.strip():
        return None
    if "text/event-stream" in content_type:
        parts = [line[5:].strip() for line in data.splitlines() if line.startswith("data:")]
        if not parts:
            raise RuntimeError("SSE sem dados JSON-RPC")
        data = parts[-1]
    try:
        return json.loads(data)
    except ValueError:
        raise RuntimeError("Servidor retornou resposta não-JSON (%s)" % path) from None


def rpc(method, params=None, req_id=1):
    msg = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        msg["params"] = params
    out = send("/mcp", msg)
    if not isinstance(out, dict):
        raise RuntimeError("Resposta MCP inesperada para %s" % method)
    if "error" in out:
        err = out["error"]
        raise RuntimeError("Erro MCP em %s (código %s)" % (method, err.get("code", "?")))
    if "result" not in out:
        raise RuntimeError("Resposta MCP sem resultado em %s" % method)
    return out["result"]


def main():
    health = send("/health")
    if not isinstance(health, dict) or health.get("ok") is not True:
        raise RuntimeError("Healthcheck indisponível")
    print("OK: Worker /health respondeu.")

    init = rpc("initialize", {
        "protocolVersion": PROTOCOL,
        "capabilities": {},
        "clientInfo": {"name": "mcp-readonly-smoke-test", "version": "1.0.0"},
    }, 1)
    print("OK: MCP initialize; protocolo: %s." % init.get("protocolVersion", "não informado"))
    send("/mcp", {"jsonrpc": "2.0", "method": "notifications/initialized"})

    listing = rpc("tools/list", {}, 2)
    names = {t.get("name") for t in listing.get("tools", [])}
    required = {"status_base_verificada", "buscar_referencias_aprovadas", "obter_referencia_aprovada"}
    if not required.issubset(names):
        raise RuntimeError("Ferramentas obrigatórias ausentes: " + ", ".join(sorted(required - names)))
    print("OK: as três ferramentas MCP foram descobertas.")

    got = rpc("tools/call", {
        "name": "obter_referencia_aprovada",
        "arguments": {"record_id": EXPECTED_ID}
    }, 3)
    if got.get("isError"):
        raise RuntimeError("Ferramenta respondeu isError=true (verificar variáveis e RLS do Worker)")
    contents = got.get("content", [])
    texts = [x.get("text", "") for x in contents if x.get("type") == "text"]
    if not texts:
        raise RuntimeError("Resposta de obter_referencia_aprovada sem conteúdo")
    try:
        payload = json.loads(texts[0])
    except ValueError:
        raise RuntimeError("Resposta da ferramenta não contém JSON válido") from None
    record = payload.get("registro")
    if not isinstance(record, dict) or record.get("record_id") != EXPECTED_ID:
        raise RuntimeError("Registro publicado não foi recuperado pelo MCP")
    print("OK: registro aprovado %s recuperado via Worker MCP (sem gravação)." % EXPECTED_ID)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("FALHA:", str(e))
        raise SystemExit(1)
