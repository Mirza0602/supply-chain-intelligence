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

from pyspark.sql.functions import col, to_date, datediff, when, lit

# --- Stammdaten: 1:1 aus Bronze übernehmen, nur Silver-Tabelle anlegen ---
for t in ["customers", "materials", "carriers", "routes"]:
    df = spark.table(f"bronze_{t}")
    # allow schema overwrite in case Bronze schema changed
    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(f"silver_{t}")
    print(f"silver_{t}: {df.count()} Zeilen")

# --- Shipments: Typisierung + Business-Regeln ---
df = spark.table("bronze_shipments")

# Optional: start from a clean, well-defined on_time_flag (INT)
# This helps avoid Delta trying to merge incompatible existing definitions.
df = df.withColumn("on_time_flag", lit(None).cast("int"))

df = (df
    .withColumn("order_date", to_date(col("order_date")))
    .withColumn("planned_delivery_date", to_date(col("planned_delivery_date")))
    .withColumn("actual_delivery_date", to_date(col("actual_delivery_date")))
    .withColumn(
        "delay_days",
        when(
            col("actual_delivery_date").isNotNull(),
            datediff(col("actual_delivery_date"), col("planned_delivery_date"))
        ).otherwise(None)
    )
    .withColumn(
        "on_time_flag",
        when(
            col("delay_days").isNotNull(),
            col("delay_days") <= 0
        ).otherwise(None)
    )
    .filter((col("quantity") > 0) & (col("weight_kg") > 0))
)

# Overwrite Delta table and allow schema changes to resolve field merge issues
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("silver_shipments")

print(f"silver_shipments: {df.count()} Zeilen")

# Qualitäts-Check über ALLE Status-Werte:
df.groupBy("status", "on_time_flag").count().show()

# Und Gesamtübersicht nach Flag:
df.groupBy("on_time_flag").count().show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
