# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "78098744-ced1-4845-b296-b6fdca3dca5a",
# META       "default_lakehouse_name": "lh_supplychain",
# META       "default_lakehouse_workspace_id": "27d78c9d-ba43-425e-8cb2-38d5ce5bfdd6",
# META       "known_lakehouses": [
# META         {
# META           "id": "78098744-ced1-4845-b296-b6fdca3dca5a"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import current_timestamp

# Bronze-Ingestion: CSV -> Delta-Tabelle (1:1, unverändert, nur Ladezeitstempel ergänzt)
tables = ["customers", "materials", "carriers", "routes", "shipments"]

for t in tables:
    df = spark.read.option("header", "true").option("inferSchema", "true") \
        .csv(f"Files/raw/{t}.csv")
    df = df.withColumn("_bronze_loaded_at", current_timestamp())
    df.write.format("delta").mode("overwrite").saveAsTable(f"bronze_{t}")
    print(f"{t}: {df.count()} Zeilen geladen -> bronze_{t}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
