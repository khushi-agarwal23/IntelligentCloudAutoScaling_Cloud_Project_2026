import pandas as pd

data = pd.read_csv(r"data\workload.csv")
dynamic = pd.read_csv(r"data\simulation_results.csv")

CAPACITY = 350000
FIXED_INSTANCES = 4

# Fixed system: four instances at every timestamp
fixed_cpu = (
    data["workload"] / (FIXED_INSTANCES * CAPACITY) * 100
).clip(upper=100)

# Dynamic system: estimated CPU after scaling decisions
dynamic_cpu = dynamic["cpu_after_percent"]

print("FIXED VS DYNAMIC SCALING")
print("------------------------")

print("\nFIXED SYSTEM")
print("Instances:", FIXED_INSTANCES)
print("Average CPU:", round(fixed_cpu.mean(), 2), "%")
print("Maximum CPU:", round(fixed_cpu.max(), 2), "%")

print("\nDYNAMIC SYSTEM")
print("Average instances:",
      round(dynamic["instances_after"].mean(), 2))
print("Average CPU after scaling:",
      round(dynamic_cpu.mean(), 2), "%")
print("Maximum CPU after scaling:",
      round(dynamic_cpu.max(), 2), "%")
print("Scaling actions:",
      (dynamic["action"] != "MAINTAIN").sum())

saved = FIXED_INSTANCES - dynamic["instances_after"].mean()
reduction = saved / FIXED_INSTANCES * 100

print("\nAverage instance reduction:",
      round(reduction, 2), "%")