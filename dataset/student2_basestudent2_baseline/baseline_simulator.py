
import pandas as pd

data = pd.read_csv(r"data\workload.csv")

MIN_INSTANCES = 1
MAX_INSTANCES = 5
CAPACITY = 350000
SCALE_OUT = 70
SCALE_IN = 30

instances = 2
low_usage_count = 0
results = []

for _, row in data.iterrows():
    timestamp = int(row["timestamp"])
    workload = row["workload"]

    # CPU before scaling
    instances_before = instances
    cpu_before = min(
        workload / (instances * CAPACITY) * 100, 100
    )

    action = "MAINTAIN"

    # Scale out when estimated CPU is high
    if cpu_before > SCALE_OUT:
        low_usage_count = 0
        if instances < MAX_INSTANCES:
            instances += 1
            action = "SCALE OUT"

    # Scale in after two consecutive low readings
    elif cpu_before < SCALE_IN:
        if instances > MIN_INSTANCES:
            low_usage_count += 1
            if low_usage_count >= 2:
                instances -= 1
                low_usage_count = 0
                action = "SCALE IN"
        else:
            low_usage_count = 0
    else:
        low_usage_count = 0

    # CPU after scaling
    cpu_after = min(
        workload / (instances * CAPACITY) * 100, 100
    )

    results.append({
        "timestamp_ms": timestamp,
        "workload": round(workload, 2),
        "instances_before": instances_before,
        "cpu_before_percent": round(cpu_before, 2),
        "instances_after": instances,
        "cpu_after_percent": round(cpu_after, 2),
        "action": action
    })

output = pd.DataFrame(results)
output.to_csv(r"data\simulation_results.csv", index=False)

print(output.to_string(index=False))
print("\nSimulation completed successfully!")
print("Results saved to data\\simulation_results.csv")
