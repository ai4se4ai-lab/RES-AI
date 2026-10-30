"""Launch the real model server only in a container with no accelerator devices."""
import glob
import json
import os
from pathlib import Path

devices=sorted(set(glob.glob('/dev/nvidia*')+glob.glob('/dev/dri/renderD*')+glob.glob('/dev/kfd')))
receipt=dict(accelerator_devices=devices,container_isolation=True,model_server='/ollama/bin/ollama')
Path('/fault-evidence/device-isolation.json').write_text(json.dumps(receipt,indent=2)+'\n')
if devices:
    raise SystemExit('resource fault isolation failed: accelerator device remains visible')
os.execv('/ollama/bin/ollama',['/ollama/bin/ollama','serve'])
