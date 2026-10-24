"""Enumerate intended paired episodes; a planned row is never an execution receipt."""
import json
from pathlib import Path
import random
import re

ROOT=Path(__file__).resolve().parents[2]


def main():
    plan=json.loads((ROOT/'experiments/campaign/plan.json').read_text())
    order=random.Random(20261024)
    rows=[]
    for subject in plan['subjects']:
        slug=re.sub('[^a-z0-9]+','-',subject['name'].lower())
        for seed in plan['paired_seeds']:
            for episode_class in plan['episode_classes']:
                conditions=plan['conditions'][:]
                order.shuffle(conditions)
                for condition in conditions:
                    rows.append(dict(episode_id=f'{slug}-{seed}-{episode_class}-{condition}',
                        artifact=subject['name'],paired_seed=seed,episode_class=episode_class,
                        condition=condition,status='PLANNED_NATIVE_ADAPTER_PENDING'))
    assert len(rows)==plan['potential_episodes'] and len({r['episode_id'] for r in rows})==len(rows)
    out=ROOT/'experiments/results/campaign/planned-episodes.jsonl'
    out.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    print(f'{len(rows)} intended episodes; none are marked executed.')


if __name__=='__main__':
    main()
