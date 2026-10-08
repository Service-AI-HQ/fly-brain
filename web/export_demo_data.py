"""
Export simulation results to compact JSON for the static web demo in docs/.

Reads the spike parquet files listed in a run's manifest.csv, joins FlyWire
neuron annotations (cell type, class, side, position), and writes:
    docs/data/brain.json          sampled neuron positions for the brain outline
    docs/data/experiments.json    index of exported experiments
    docs/data/<key>.json          one file per experiment (neurons + spikes)

Usage:
    python web/export_demo_data.py --run-label mac_sugar mac_p9 --annotations path/to/annotations.tsv

Give each experiment its own --run-label when running main.py: spike files are
named by backend/duration/trials only, so two experiments under one label
overwrite each other's parquet.

The annotations file is Supplemental_file1_neuron_annotations.tsv from
https://github.com/flyconnectome/flywire_annotations (FlyWire v783).
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'code'))
from benchmark import EXPERIMENTS  # noqa: E402

ANNOT_COLS = ['root_id', 'pos_x', 'pos_y', 'pos_z', 'super_class',
              'cell_class', 'cell_type', 'side', 'top_nt']
BRAIN_SAMPLE = 20000


def load_annotations(path):
    a = pd.read_csv(path, sep='\t', usecols=ANNOT_COLS)
    a = a.drop_duplicates('root_id').set_index('root_id')
    return a.fillna('')


def clean(v):
    return '' if v is None or (isinstance(v, float) and np.isnan(v)) else v


def export_brain(annot, out_dir):
    sample = annot.sample(n=min(BRAIN_SAMPLE, len(annot)), random_state=0)
    pts = np.round(sample[['pos_x', 'pos_y']].to_numpy(float) / 100).astype(int)
    xs, ys = annot['pos_x'].astype(float), annot['pos_y'].astype(float)
    bounds = [round(xs.min() / 100), round(ys.min() / 100),
              round(xs.max() / 100), round(ys.max() / 100)]
    (out_dir / 'brain.json').write_text(json.dumps(
        {'bounds': bounds, 'points': pts.ravel().tolist()}, separators=(',', ':')))


def export_experiment(row, annot, out_dir):
    exp = EXPERIMENTS[row['experiment_key']]
    spikes = pd.read_parquet(root / row['spike_path'])
    spikes = spikes[spikes['trial'] == 0]
    t_run_ms = float(row['t_run']) * 1000
    stim = {int(n) for n in exp['neu_exc'] + exp.get('neu_exc2', [])}

    g = spikes.groupby('flywire_id')['time_ms']
    per = pd.DataFrame({'count': g.size(), 'first': g.min()})
    per = per.sort_values(['first', 'count'], ascending=[True, False])

    neurons, index = [], {}
    for i, (fid, r) in enumerate(per.iterrows()):
        a = annot.loc[fid] if fid in annot.index else None
        index[fid] = i
        neurons.append({
            'id': str(fid),
            'type': clean(a['cell_type']) if a is not None else '',
            'cls': clean(a['cell_class']) if a is not None else '',
            'sup': clean(a['super_class']) if a is not None else '',
            'side': clean(a['side']) if a is not None else '',
            'nt': clean(a['top_nt']) if a is not None else '',
            'x': round(float(a['pos_x']) / 100) if a is not None else None,
            'y': round(float(a['pos_y']) / 100) if a is not None else None,
            'rate': round(r['count'] / (t_run_ms / 1000), 1),
            'first': round(float(r['first']), 1),
            'stim': fid in stim,
        })

    pairs = np.column_stack([
        spikes['flywire_id'].map(index).to_numpy(),
        np.round(spikes['time_ms'].to_numpy() * 10).astype(int),  # 0.1 ms units
    ]).ravel().tolist()

    data = {
        'key': exp['key'], 'name': exp['name'], 'stim_rate': exp['stim_rate'],
        't_run_ms': t_run_ms, 'backend': row['framework'],
        'n_spikes': int(len(spikes)), 'neurons': neurons, 'spikes': pairs,
    }
    (out_dir / f"{exp['key']}.json").write_text(json.dumps(data, separators=(',', ':')))
    return {'key': exp['key'], 'name': exp['name'], 'stim_rate': exp['stim_rate'],
            't_run_ms': t_run_ms, 'n_active': len(neurons), 'n_spikes': int(len(spikes)),
            'n_stim': len(stim)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-label', nargs='+', required=True)
    p.add_argument('--annotations', required=True)
    p.add_argument('--out', default=str(root / 'docs' / 'data'))
    args = p.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    annot = load_annotations(args.annotations)
    export_brain(annot, out_dir)

    manifest = pd.concat([pd.read_csv(root / 'data' / 'results' / label / 'manifest.csv')
                          for label in args.run_label])
    manifest = manifest[manifest['status'] == 'success']
    # keep the latest successful run per experiment
    manifest = manifest.sort_values('timestamp').drop_duplicates('experiment_key', keep='last')

    index = [export_experiment(r, annot, out_dir) for _, r in manifest.iterrows()]
    index.sort(key=lambda e: list(EXPERIMENTS).index(e['key']))
    (out_dir / 'experiments.json').write_text(json.dumps(index, indent=1))
    for e in index:
        print(f"{e['key']}: {e['n_active']} active neurons, {e['n_spikes']} spikes")


if __name__ == '__main__':
    main()
