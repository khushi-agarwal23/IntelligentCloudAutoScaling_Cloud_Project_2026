import pandas as pd

df = pd.read_csv(r"data\simulation_results.csv")

scale_out = (df["action"] == "SCALE OUT").sum()
scale_in = (df["action"] == "SCALE IN").sum()

print("UPDATED BASELINE EVALUATION")
print("---------------------------")
print("Workload points:", len(df))

print("Average CPU before scaling:",
      round(df["cpu_before_percent"].mean(), 2), "%")
print("Average CPU after scaling:",
      round(df["cpu_after_percent"].mean(), 2), "%")

print("Maximum CPU before scaling:",
      round(df["cpu_before_percent"].max(), 2), "%")
print("Maximum CPU after scaling:",
      round(df["cpu_after_percent"].max(), 2), "%")

print("Scale-out actions:", scale_out)
print("Scale-in actions:", scale_in)
print("Total scaling actions:", scale_out + scale_in)

print("Average instances:",
      round(df["instances_after"].mean(), 2))
print("Minimum instances:", df["instances_after"].min())
print("Maximum instances:", df["instances_after"].max())