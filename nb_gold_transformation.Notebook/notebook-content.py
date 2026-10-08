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

# MAGIC %%sql 
# MAGIC SET spark.sql.parquet.vorder.default=TRUE

# METADATA ********************

# META {
# META   "language": "sparksql",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import (
    col, to_date, year, quarter, month, dayofmonth,
    dayofweek, weekofyear, date_format
)
from pyspark.sql import functions as F

# --- Dim_Date: Kalendertabelle für DAX-Zeitintelligenz ---
date_range = spark.sql("""
    SELECT explode(sequence(to_date('2025-01-01'), to_date('2026-12-31'), interval 1 day)) as Date
""")

dim_date = (date_range
    .withColumn("DateKey", date_format(col("Date"), "yyyyMMdd").cast("int"))
    .withColumn("Year", year(col("Date")))
    .withColumn("Quarter", quarter(col("Date")))
    .withColumn("Month", month(col("Date")))
    .withColumn("MonthName", date_format(col("Date"), "MMMM"))
    .withColumn("Day", dayofmonth(col("Date")))
    .withColumn("DayOfWeek", dayofweek(col("Date")))
    .withColumn("DayName", date_format(col("Date"), "EEEE"))
    .withColumn("WeekOfYear", weekofyear(col("Date")))
    .withColumn("YearMonth", date_format(col("Date"), "yyyy-MM"))
    .withColumn("IsWeekend", col("DayOfWeek").isin([1, 7]))
)

dim_date.write.format("delta").mode("overwrite").saveAsTable("Dim_Date")
print(f"Dim_Date: {dim_date.count()} Zeilen")

# --- Dimensionen: 1:1 aus Silver übernehmen, Bronze-Audit-Spalte rausfiltern ---
dim_map = {
    "customers": "Dim_Customer",
    "materials": "Dim_Material",
    "carriers": "Dim_Carrier",
    "routes": "Dim_Route",
}

for silver_name, gold_name in dim_map.items():
    df = spark.table(f"silver_{silver_name}")
    if "_bronze_loaded_at" in df.columns:
        df = df.drop("_bronze_loaded_at")
    df.write.format("delta") \
        .mode("overwrite") \
        .option("overwriteSchema", "true") \
        .saveAsTable(gold_name)
    print(f"{gold_name}: {df.count()} Zeilen")

# --- Fact_Shipments: Join mit Silver-Routes für distance_km, Tonnen-km berechnen ---
shipments = spark.table("silver_shipments")
routes = spark.table("silver_routes").select("route_id", "distance_km")

fact_shipments = (shipments
    .join(routes, on="route_id", how="left")
    .withColumn("tonnen_km", (col("weight_kg") / 1000) * col("distance_km"))
    .select(
        "shipment_id", "customer_id", "material_id", "carrier_id", "route_id",
        "order_date", "planned_delivery_date", "actual_delivery_date",
        "quantity", "weight_kg", "status", "delay_days", "on_time_flag",
        "distance_km", "tonnen_km"
    )
)

fact_shipments.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable("Fact_Shipments")
print(f"Fact_Shipments: {fact_shipments.count()} Zeilen")

fact_shipments.agg(F.round(F.sum("tonnen_km"), 0).alias("gesamt_tonnen_km")).show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
