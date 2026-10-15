
import pandas as pd

input_file = r"data\MSRTQps\MSRTQps_0.csv"
output_file = r"data\workload.csv"

parts = []

for chunk in pd.read_csv(input_file, chunksize=500000):
    http = chunk[chunk["metric"] == "HTTP_MCR"]

    if not http.empty:
        grouped = http.groupby("timestamp")["value"].sum()
        parts.append(grouped)

workload = pd.concat(parts).groupby(level=0).sum().sort_index()

result = workload.reset_index()
result.columns = ["timestamp", "workload"]
result.to_csv(output_file, index=False)

print("Workload dataset created!")
print("Number of timestamps:", len(result))
print(result.head(10).to_string(index=False))
print("Saved to:", output_file)
