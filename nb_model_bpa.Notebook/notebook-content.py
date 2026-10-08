# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

%pip install semantic-link-labs --quiet

import sempy_labs as labs

df_bpa = labs.run_model_bpa(dataset="sm_supplychain_gold", return_dataframe=True)
print(f"{len(df_bpa)} Befunde")
print(df_bpa.to_string())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

print(df_bpa.groupby(["Severity", "Category", "Rule Name"]).size().sort_values(ascending=False).to_string())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
