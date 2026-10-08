# Fly Brain Explorer (website)

**Live site:** https://service-ai-hq.github.io/fly-brain/

This folder is the whole website. GitHub Pages serves it straight from
`main` → `/docs`, so any change pushed here goes live in about a minute.
There's no build step.

## What's in here

| File | What it is |
|---|---|
| `index.html` | The entire page: layout, styles, brain map, spike raster, neuron table, playback |
| `data/experiments.json` | List of experiments shown as tabs |
| `data/<experiment>.json` | One file per experiment: active neurons (cell type, class, position, rate, first spike) and every spike |
| `data/brain.json` | 20,000 sampled neuron positions that draw the grey brain outline |

## Working on it from another computer

You don't need Python, a GPU, or the simulator to view or edit the site.

1. Clone the repo:
   ```bash
   git clone https://github.com/Service-AI-HQ/fly-brain.git
   cd fly-brain/docs
   ```
2. Preview locally (the page loads its data with `fetch`, so open it through a
   server, not by double-clicking the file):
   ```bash
   python3 -m http.server 8000
   ```
   then open http://localhost:8000
3. Edit `index.html`, refresh to check, then commit and push. The live site updates on its own.

Experiment descriptions shown under the tabs are in the `DESCRIPTIONS` object
near the top of the `<script>` in `index.html`.

## Adding a new experiment

This step needs a computer that can run the simulation (any recent Mac or PC
works on CPU; 1 s of brain time takes about 5–6 minutes on an M3 Pro).

1. Define the experiment in `EXPERIMENTS` in [`code/benchmark.py`](../code/benchmark.py)
   (FlyWire IDs of the neurons to stimulate, and a rate in Hz).
2. Run it with its **own** run label (runs that share a label overwrite each other's spike file):
   ```bash
   python main.py --pytorch --experiment <key> --t_run 1 --n_run 1 --run-label mac_<key>
   ```
3. Re-export every run you want on the site:
   ```bash
   python web/export_demo_data.py --run-label mac_sugar mac_p9 mac_<key> \
       --annotations Supplemental_file1_neuron_annotations.tsv
   ```
   The annotations file is from
   [flyconnectome/flywire_annotations](https://github.com/flyconnectome/flywire_annotations/tree/main/supplemental_files).
4. Add a one-line description for `<key>` in `DESCRIPTIONS` in `index.html`, then commit and push.

The raw run folders (`data/results/mac_*`) aren't committed; only the exported
JSON in `docs/data/` is needed for the site.

## Current runs

| Experiment | Stimulated | Neurons that fired | Spikes (1 s) | Run on |
|---|---|---|---|---|
| Sugar GRNs, 200 Hz | 21 sugar taste neurons | 398 | 17,400 | PyTorch CPU, Apple M3 Pro, 2026-10-07 |
| P9 forward walking, 100 Hz | 2 P9 descending neurons | 138 | 833 | PyTorch CPU, Apple M3 Pro, 2026-10-07 |
