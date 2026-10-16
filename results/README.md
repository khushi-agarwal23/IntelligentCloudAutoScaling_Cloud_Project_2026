# Results and figures

- `alibaba2018_workload_overview.png`: 10-second cluster mean CPU/memory for the selected continuous segment, with train/validation/test boundaries and training-derived p95 thresholds.
- Forecast metrics and threshold sweeps are saved in `data/alibaba2018/processed/`; the three-way chronological results use the `*_triple_split.csv` suffix.
- `final_experiment_summary.txt` and files without the `triple_split` suffix are existing earlier experiment outputs. See [the verified review report](../docs/Workload_Analysis_and_Review.md) for interpretation and limitations.

All workload and scaling-policy results are offline experiments. They are not real AWS performance or cost evidence.
