"""Bounded CPU initialization for a no-generation accelerator-unavailability check."""
import json


def warmup(model):
    # These settings only size the empty initialization run. No generation may
    # proceed after this fault: the unchanged residency requirement rejects it.
    options=dict(num_ctx=model.science['max_input_tokens']+model.science['max_new_tokens'],
        num_gpu=999,num_batch=32,num_thread=4)
    (model.out/'resource-warmup-options.json').write_text(json.dumps(options,indent=2)+'\n')
    model.request('/api/generate',dict(model=model.science['model'],prompt='',stream=False,
        keep_alive='10m',options=options))
    running=model.request('/api/ps')['models']
    (model.out/'loaded-model.json').write_text(json.dumps(running,indent=2)+'\n')
    if not any(m['name']==model.science['model'] and m.get('size_vram',0)>0 and m['size_vram']>=.95*m['size'] for m in running):
        raise RuntimeError('model did not load fully into GPU memory')
