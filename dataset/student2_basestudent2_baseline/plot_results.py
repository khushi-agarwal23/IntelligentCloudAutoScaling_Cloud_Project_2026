
import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv(r"data\workload.csv")
results = pd.read_csv(r"data\simulation_results.csv")

time = data["timestamp"] / 60000

fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)

# Graph 1: Workload
axes[0].plot(time, data["workload"], marker="o")
axes[0].set_ylabel("HTTP workload")
axes[0].set_title("Alibaba Workload and Auto-Scaling Results")
axes[0].grid(True, alpha=0.3)

# Graph 2: CPU before and after scaling
axes[1].plot(time, results["cpu_before_percent"],
             marker="o", label="CPU before scaling")
axes[1].plot(time, results["cpu_after_percent"],
             marker=".", label="CPU after scaling")
axes[1].axhline(70, linestyle="--", label="Scale-out threshold")
axes[1].set_ylabel("Estimated CPU (%)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# Graph 3: Instance count and scaling decisions
instances = results["instances_after"]
axes[2].step(time, instances, where="post", label="Instances")

out = results["action"] == "SCALE OUT"
in_ = results["action"] == "SCALE IN"

axes[2].scatter(time[out], instances[out],
                marker="^", label="Scale out")
axes[2].scatter(time[in_], instances[in_],
                marker="v", label="Scale in")
axes[2].set_xlabel("Time (minutes)")
axes[2].set_ylabel("Instance count")
axes[2].set_ylim(0, 6)
axes[2].legend()
axes[2].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(r"data\scaling_results.png", dpi=200)
plt.close()

print("Updated graph saved to data\\scaling_results.png")
