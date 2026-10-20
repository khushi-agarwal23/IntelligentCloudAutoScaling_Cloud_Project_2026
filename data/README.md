# Alibaba workload data and experiment reproduction

This folder documents the Alibaba Cluster Trace v2018 workload experiments in this repository. The trace is infrastructure utilization data, not e-commerce transactions or festival sales. Follow Alibaba's dataset terms and cite the source when reusing it.

## Source and access

The primary source is [Alibaba Cluster Trace Program](https://github.com/alibaba/clusterdata), specifically the [Cluster Trace v2018 description and download instructions](https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/trace_2018.md) and [schema](https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/schema.txt). The source may require completing Alibaba's survey to obtain a download. The project does not redistribute the raw trace.

The `machine_usage.tar.gz` archive is approximately 1.65 GB and expands to an approximately 8.58 GB `machine_usage.csv`. The archive's expected SHA-256 is:

```text
3e6ee87fd204bb85b9e234c5c75a5096580fdabc8f085b224033080090753a7a
```

The value above was checked against the official trace description and the local archive. Verify any teammate-provided copy before extraction:

```powershell
Get-FileHash .\data\alibaba2018\raw\machine_usage.tar.gz -Algorithm SHA256
```

For team sharing, prefer an institution-controlled OneDrive/SharePoint/Google Drive or equivalent with read access restricted to the project team. Share the archive there and put its stable location and version in the team channel or course materials; do not put a private link or credentials in Git. Alternatively, use Git LFS only after confirming LFS storage/bandwidth is enabled for this GitHub repository and approved for this dataset. Git LFS is installed locally, but this repository currently has no LFS-tracked files, and remote LFS availability has not been verified. Do not use ordinary Git for the archive or extracted CSV.

## Files needed for the 2018 experiments

### Minimum input for evaluations

The small processed input `data/alibaba2018/processed/machine_timeseries.csv` (currently about 3.13 MB) is enough to rerun the forecast, threshold, scaling-policy, plotting, and Alibaba-trained Q-learning experiments. The capacity-response sensitivity script additionally reads `models/alibaba2018_q_table.pkl`; regenerate that model with `scripts/train_alibaba2018_rl.py` first if it is absent. It contains one row per timestamp with `timestamp`, `cpu_mean`, `memory_mean`, and an aggregation count field. All evaluated models and policies derive from this time series.

Required code and evidence to share:

- `scripts/preprocess_alibaba2018.py` to derive the aggregated series from raw data.
- `scripts/evaluate_forecast_baseline.py` and `scripts/evaluate_ml_forecast.py` for persistence and Random Forest comparison.
- `scripts/analyze_alibaba2018_thresholds.py` for threshold sensitivity.
- `scripts/evaluate_alibaba2018_scaling.py` and `scripts/evaluate_capacity_response.py` for offline policy/capacity-response experiments.
- `scripts/train_alibaba2018_rl.py` for the separate Alibaba-trained offline Q-learning experiment.
- `scripts/plot_alibaba2018_workload.py` and `results/alibaba2018_workload_overview.png` for the workload plot.
- `docs/Workload_Analysis_and_Review.md` for methodology, checked metrics, interpretation, and limitations.
- `data/alibaba2018/processed/*` result CSVs and `final_experiment_summary.txt` as compact saved outputs. The `*_triple_split.csv` files are the revised chronological three-way results; unsuffixed forecast CSVs are older outputs and are retained for comparison, not as the current primary result.
- `models/alibaba2018_q_table.pkl` is the separately generated artifact from `train_alibaba2018_rl.py`; it is not the synthetic-workload Q-table used by the application.

Python requirements for these scripts are `pandas`, `numpy`, `scikit-learn`, and `matplotlib`. From the repository root, a clean environment can be prepared with:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pandas numpy scikit-learn matplotlib
```

The 2017 files under `data/alibaba/` are a separate earlier experiment and are not required to reproduce the Alibaba 2018 results described in the workload review.

## Expected folder layout

The raw data is intentionally external/untracked. Place the archive and extracted CSV as follows:

```text
data/
  README.md
  alibaba2018/
    raw/                         # ignored by Git
      machine_usage.tar.gz       # about 1.65 GB; shared/downloaded input
      extracted/                 # ignored by Git
        machine_usage.csv        # about 8.58 GB
    processed/
      machine_timeseries.csv     # compact aggregated input, shared in Git
      ...                        # saved experiment CSVs
```

From the repository root, create directories, download the official machine-usage archive using the Alibaba instructions, and save it as `data/alibaba2018/raw/machine_usage.tar.gz`. Then verify and extract:

```powershell
New-Item -ItemType Directory -Force data\alibaba2018\raw\extracted | Out-Null
Get-FileHash data\alibaba2018\raw\machine_usage.tar.gz -Algorithm SHA256
tar -xzf data\alibaba2018\raw\machine_usage.tar.gz -C data\alibaba2018\raw\extracted
```

If the archive extracts into a nested directory, move or copy only its `machine_usage.csv` to `data\alibaba2018\raw\extracted\machine_usage.csv`. The preprocessing script expects exactly that path. Do not overwrite the archive with extracted files.

## Reproduction commands

Run commands from the repository root with Python 3.12 and the required packages installed. The forecast/policy scripts read `data/alibaba2018/processed/machine_timeseries.csv`; preprocessing is only needed if rebuilding that file from the raw archive.

Rebuild the aggregated series from raw data (reads the CSV in chunks; creates temporary checkpoint chunks under `processed/checkpoints/`):

```powershell
py -3.12 scripts/preprocess_alibaba2018.py
```

Rerun the main forecast and threshold experiments:

```powershell
py -3.12 scripts/evaluate_forecast_baseline.py
py -3.12 scripts/evaluate_ml_forecast.py
py -3.12 scripts/analyze_alibaba2018_thresholds.py
```

Rerun offline scaling, train the separate Alibaba Q-table, then run sensitivity and regenerate the plot:

```powershell
py -3.12 scripts/evaluate_alibaba2018_scaling.py
py -3.12 scripts/train_alibaba2018_rl.py
py -3.12 scripts/evaluate_capacity_response.py
py -3.12 scripts/plot_alibaba2018_workload.py
```

These are offline trace experiments; they do not call AWS or measure production cost, latency, health, or real Auto Scaling behavior.

## Git and large-file policy

The repository `.gitignore` excludes all `data/**/raw/` folders and `data/alibaba2018/processed/checkpoints/`. Keep the archive, extracted CSV, and intermediate checkpoint chunks outside ordinary Git history. Commit the README, reproducible scripts, the small aggregated time series, compact result CSVs, plot, report, and separately generated small model artifact where relevant. Review `git status --short` and `git check-ignore -v` before staging; stage only named files.

Raw dataset availability through this repository is **not verified**. It becomes team-accessible only after it is uploaded to an approved shared location or an enabled Git LFS remote and the teammates receive access.