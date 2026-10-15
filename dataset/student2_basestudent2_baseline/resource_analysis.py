
import pandas as pd

dynamic = pd.read_csv(r"data\simulation_results.csv")

fixed_instances = 4
dynamic_average = dynamic["instances_after_action"].mean()

saved_instances = fixed_instances - dynamic_average
saving_percent = (saved_instances / fixed_instances) * 100

print("RESOURCE USAGE ANALYSIS")
print("-----------------------")
print("Fixed instance count:", fixed_instances)
print("Dynamic average instances:", round(dynamic_average, 2))
print("Average instances saved:", round(saved_instances, 2))
print("Estimated instance reduction:",
      round(saving_percent, 2), "%")
print("\nNote: This measures simulated instance usage,")
print("not actual monetary savings or cloud billing.")
