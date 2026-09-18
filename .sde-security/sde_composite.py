#!/usr/bin/env python3
import argparse, json, os, sys, time
from pathlib import Path
from urllib import error, request


def load_config():
    host = os.environ.get('SDE_HOST')
    key = os.environ.get('SDE_API_KEY')
    paths = [Path('.cursor/mcp.json'), Path.home() / 'Library/Application Support/Code/User/mcp.json', Path.home() / '.cursor/mcp.json']
    for path in paths:
        if host and key:
            break
        try:
            data = json.loads(path.read_text())
            servers = data.get('mcpServers', data.get('servers', {}))
            env = servers.get('sdelements', {}).get('env', {}) if isinstance(servers, dict) else {}
            host = host or env.get('SDE_HOST') or env.get('SDE_API_URL')
            key = key or env.get('SDE_API_KEY') or env.get('SDE_API_TOKEN')
            # Accept equivalent MCP header configuration when the named server
            # is absent (common in VS Code MCP settings).
            if not key and isinstance(servers, dict):
                for server in servers.values():
                    if not isinstance(server, dict):
                        continue
                    se = server.get('env', {})
                    sh = server.get('headers', {})
                    key = se.get('SDE_API_KEY') or se.get('SDE_API_TOKEN') or sh.get('SDE-API-Key') or sh.get('SDE_API-KEY')
                    if key:
                        break
        except (OSError, ValueError, TypeError):
            continue
    if not host or not key:
        raise SystemExit('SDE_HOST and SDE_API_KEY are required (environment or mcp.json)')
    return host.rstrip('/'), key


def post(url, payload, key):
    body = json.dumps(payload).encode()
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
               'Authorization': 'Bearer ' + key, 'X-API-Key': key}
    req = request.Request(url, data=body, headers=headers, method='POST')
    try:
        with request.urlopen(req, timeout=60) as response:
            raw = response.read()
            try: value = json.loads(raw.decode() or 'null')
            except ValueError: value = raw.decode(errors='replace')
            return response.status, value
    except error.HTTPError as exc:
        raw = exc.read()
        try: value = json.loads(raw.decode() or 'null')
        except ValueError: value = raw.decode(errors='replace')
        return exc.code, value
    except Exception as exc:
        return None, str(exc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    host, key = load_config()
    payload = json.loads(Path(args.input).read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get('composite_request'), list):
        raise SystemExit('input must contain composite_request')
    status, response = post(host + '/api/v2/composite/', payload, key)
    results = response.get('composite_response', response.get('responses', response.get('results', []))) if isinstance(response, dict) else response
    if not isinstance(results, list):
        results = []
    Path(args.out).write_text(json.dumps({'composite_response': results}, indent=2, ensure_ascii=False) + '\n')
    failed = [r for r in results if not isinstance(r, dict) or r.get('status', r.get('status_code', r.get('http_status'))) != 201]
    print(f'posted={len(results)-len(failed)} failed={len(failed)}')
    if failed: print('failed responses: ' + str(len(failed)))
    return 1 if failed else 0

if __name__ == '__main__': sys.exit(main())
