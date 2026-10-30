"""Check the real Ollama JSON decoder without loading a model or generating text."""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from sweagent_transport import ollama_messages as original
from sweagent_transport_v2 import ollama_messages as corrected

history = [dict(role='user', content=[dict(type='text', text='schema check',
           cache_control={'type': 'ephemeral'})])]
records = []
for label, convert, expected in [('original', original, 400), ('corrected', corrected, 404)]:
    body = dict(model='resai-schema-check-nonexistent:latest', messages=convert(history),
                stream=False)
    request = urllib.request.Request('http://127.0.0.1:18939/api/chat',
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            code, result = response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        code, result = error.code, error.read().decode()
    records.append(dict(variant=label, request=body, status=code, response=result))
    if code != expected:
        raise RuntimeError(f'{label}: expected HTTP {expected}, got {code}: {result}')
Path(sys.argv[1]).write_text(json.dumps(dict(status='REAL_OLLAMA_SCHEMA_CHECK_PASSED',
    model_calls=0, records=records), indent=2)+'\n')
print('REAL_OLLAMA_SCHEMA_CHECK_PASSED')
