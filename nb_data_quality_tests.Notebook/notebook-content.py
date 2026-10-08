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

# MARKDOWN ********************

# # Datenqualitätstests: Gold-Schicht und Semantikmodell
# **Zweck:** Dieses Notebook läuft nach `nb_gold_transformation` und prüft, ob die Daten, auf denen der Bericht steht, fachlich stimmen. Es ersetzt nicht den Blick ins Dashboard, sondern verhindert, dass ein falsches Dashboard überhaupt entsteht.
# **Hintergrund:** In einer früheren Version hing die Verspätungslogik in Silver am Status `Delivered`. Die 351 Sendungen mit Status `Delayed` bekamen dadurch weder `delay_days` noch `on_time_flag`. Der Bericht zeigte 176 statt 527 verspätete Sendungen, ohne dass irgendetwas abstürzte. Genau solche stillen Fehler fangen diese Tests ab.
# **Aufbau:**
# 1. Referenzielle Integrität zwischen Fakt und Dimensionen
# 2. Regressionstest für die Verspätungslogik
# 3. Plausibilität der Mengen- und Gewichtsangaben
# 4. Abgleich der DAX-Kennzahlen im Semantikmodell (Semantic Link)
# 5. Auswertung: Bei mindestens einem Fehlschlag bricht das Notebook mit einer Fehlermeldung ab, damit eine übergeordnete Pipeline stoppt.

# CELL ********************

from pyspark.sql import functions as F

# Die Rohdaten sind synthetisch und werden mit festem Seed erzeugt
# (data/generate_raw_data.py). Die Referenzwerte ändern sich daher nur bei
# neuen Rohdaten oder bewusst geänderter Geschäftslogik.
SEMANTIC_MODEL = "sm_supplychain_gold"
EXPECTED_LATE_SHIPMENTS = 527       # 176 (Delivered) + 351 (Delayed)
EXPECTED_OTIF_RATE = 0.8185         # 2.376 pünktlich / 2.903 zugestellt
RATE_TOLERANCE = 0.00005            # entspricht Rundung auf 0,01 Prozentpunkte

results = []


def check(name, passed, detail=""):
    """Protokolliert ein Testergebnis. Abgebrochen wird erst in der Auswertung,
    damit ein Lauf alle Verstöße auf einmal meldet statt nur den ersten."""
    results.append({"test": name, "passed": bool(passed), "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + ("" if passed else f" -> {detail}"))


fact = spark.table("fact_shipments").cache()
print(f"fact_shipments: {fact.count()} Zeilen")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 1. Referenzielle Integrität
# **Logik:** Jeder Fremdschlüssel in `fact_shipments` muss genau einen Treffer in seiner Dimension haben. Geprüft wird zweierlei: Die Schlüssel der Dimension sind eindeutig und nicht leer, und es gibt keine verwaisten Faktzeilen (Anti-Join).
# **Business-Relevanz:** Waisen landen im Bericht unter „(Leer)“ oder fallen bei Filtern still heraus. Summen je Carrier oder Kunde ergeben dann nicht mehr die Gesamtsumme, und niemand merkt es. Doppelte Dimensionsschlüssel verhindern im Modell die 1:n-Beziehung.

# CELL ********************

# (Dimension, Fremdschlüssel im Fakt, Primärschlüssel der Dimension)
relations = [
    ("dim_customer", "customer_id", "customer_id"),
    ("dim_material", "material_id", "material_id"),
    ("dim_carrier",  "carrier_id",  "carrier_id"),
    ("dim_route",    "route_id",    "route_id"),
    ("dim_date",     "order_date",  "Date"),
]

for dim_table, fk, pk in relations:
    dim = spark.table(dim_table)

    duplicate_keys = dim.groupBy(pk).count().filter(F.col("count") > 1).count()
    null_keys = dim.filter(F.col(pk).isNull()).count()
    check(
        f"{dim_table}.{pk} eindeutig und nicht leer",
        duplicate_keys == 0 and null_keys == 0,
        f"{duplicate_keys} doppelte, {null_keys} leere Schlüssel",
    )

    # Der Anti-Join erfasst auch leere Fremdschlüssel, weil NULL nie matcht.
    dim_keys = dim.select(F.col(pk).alias(fk)).distinct()
    orphans = fact.join(dim_keys, on=fk, how="left_anti")
    orphan_count = orphans.count()
    sample = [r[fk] for r in orphans.select(fk).distinct().limit(5).collect()]
    check(
        f"fact_shipments.{fk} -> {dim_table}: keine Waisen",
        orphan_count == 0,
        f"{orphan_count} Zeilen ohne Treffer, Beispiele: {sample}",
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 2. Regressionstest Verspätungslogik
# **Logik:** Maßgeblich für Pünktlichkeit ist allein das tatsächliche Lieferdatum, nicht der Status.
# - Jede Sendung mit `actual_delivery_date` hat `delay_days` und `on_time_flag`.
# - `on_time_flag` ist genau dann `True`, wenn `delay_days <= 0`.
# - Offene Sendungen (ohne Lieferdatum, z. B. `In Transit`, `Cancelled`) haben beide Werte leer, damit sie nicht in den Nenner der Liefertreue fallen.
# **Business-Relevanz:** Das ist der Fehler, der hier bereits einmal aufgetreten ist. Die Liefertreue ist die Kern-KPI des Berichts, eine stille Abweichung würde jede Carrier-Bewertung verfälschen.

# CELL ********************

delivered = fact.filter(F.col("actual_delivery_date").isNotNull())
open_shipments = fact.filter(F.col("actual_delivery_date").isNull())

missing_values = delivered.filter(
    F.col("on_time_flag").isNull() | F.col("delay_days").isNull()
)
missing_count = missing_values.count()
missing_by_status = {r["status"]: r["count"] for r in missing_values.groupBy("status").count().collect()}
check(
    "Zugestellte Sendungen haben delay_days und on_time_flag",
    missing_count == 0,
    f"{missing_count} Zeilen ohne Wert, nach Status: {missing_by_status}",
)

# eqNullSafe, damit auch NULL-Kombinationen als Abweichung zählen
inconsistent = delivered.filter(
    ~F.col("on_time_flag").eqNullSafe(F.col("delay_days") <= 0)
).count()
check(
    "on_time_flag entspricht exakt delay_days <= 0",
    inconsistent == 0,
    f"{inconsistent} Zeilen mit widersprüchlichem Flag",
)

open_with_values = open_shipments.filter(
    F.col("on_time_flag").isNotNull() | F.col("delay_days").isNotNull()
).count()
check(
    "Offene Sendungen haben kein Flag und keine Verzögerung",
    open_with_values == 0,
    f"{open_with_values} offene Sendungen mit Wert, sie würden die Liefertreue verfälschen",
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 3. Plausibilität Mengen und Gewichte
# **Logik:** `quantity` und `weight_kg` müssen vorhanden und größer 0 sein. Silver filtert solche Zeilen bereits, der Test stellt sicher, dass dieser Filter in Gold auch wirklich gegriffen hat. Zusätzlich muss jede Sendung eine Distanz aus `dim_route` haben, sonst fehlt sie in den Tonnen-km.
# **Business-Relevanz:** Tonnen-km sind die Basis für „Transportleistung im Risiko“. Eine Sendung ohne Gewicht oder Distanz verschwindet dort still aus der Summe.

# CELL ********************

for column in ["quantity", "weight_kg", "distance_km"]:
    # coalesce: NULL gilt ebenfalls als Verstoß
    invalid = fact.filter(~F.coalesce(F.col(column) > 0, F.lit(False))).count()
    check(
        f"{column} vorhanden und > 0",
        invalid == 0,
        f"{invalid} Zeilen leer oder <= 0",
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 4. Kennzahlen im Semantikmodell (Semantic Link)
# **Logik:** Über `sempy.fabric.evaluate_measure` werden die DAX-Measures direkt im Direct-Lake-Modell `sm_supplychain_gold` ausgewertet, also genau die Zahlen, die der Bericht anzeigt. Zwei Abgleiche je Kennzahl:
# - **Modell gegen Lakehouse:** Das DAX-Ergebnis muss der unabhängigen PySpark-Berechnung auf den Delta-Tabellen entsprechen. Eine Abweichung heißt: geänderte DAX-Logik oder ein Modell, das noch auf einem alten Tabellenstand steht.
# - **Modell gegen validierten Referenzwert:** 527 verspätete Sendungen und 81,85 % Liefertreue wurden gegen die Rohdaten nachgerechnet. Weicht der Wert ab, hat sich Logik oder Datenbasis verändert, und das muss bewusst entschieden werden.
# **Voraussetzung:** Das Modell liegt im selben Workspace, die automatische Direct-Lake-Aktualisierung ist aktiv.
# **Business-Relevanz:** Die PySpark-Tests sichern die Daten, dieser Block sichert die Zahl auf dem Bildschirm. Erst beide zusammen belegen, dass das Management die richtige Kennzahl sieht.


# CELL ********************

import math
import sempy.fabric as fabric

measures = fabric.evaluate_measure(
    dataset=SEMANTIC_MODEL,
    measure=["Verspätete Sendungen", "OTIF-Quote %"],
)


def measure_value(name):
    """Liest einen Measure-Wert. Ein leeres Ergebnis ist selbst ein Fehler."""
    value = measures[name].iloc[0] if name in measures.columns and len(measures) > 0 else None
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise AssertionError(f"Measure [{name}] liefert im Modell {SEMANTIC_MODEL} keinen Wert.")
    return float(value)


late_model = measure_value("Verspätete Sendungen")
otif_model = measure_value("OTIF-Quote %")

# Unabhängige Referenzrechnung auf den Delta-Tabellen
late_lake = delivered.filter(F.col("on_time_flag") == False).count()  # noqa: E712
otif_lake = delivered.filter(F.col("on_time_flag") == True).count() / delivered.count()  # noqa: E712

print(f"Verspätete Sendungen: Modell {late_model:.0f} | Lakehouse {late_lake} | Referenz {EXPECTED_LATE_SHIPMENTS}")
print(f"OTIF-Quote:           Modell {otif_model:.4%} | Lakehouse {otif_lake:.4%} | Referenz {EXPECTED_OTIF_RATE:.2%}")

check(
    "[Verspätete Sendungen] Modell = Lakehouse",
    late_model == late_lake,
    f"Modell {late_model:.0f}, Lakehouse {late_lake}",
)
check(
    "[Verspätete Sendungen] = validierter Referenzwert",
    late_model == EXPECTED_LATE_SHIPMENTS,
    f"Modell {late_model:.0f}, erwartet {EXPECTED_LATE_SHIPMENTS}",
)
check(
    "[OTIF-Quote %] Modell = Lakehouse",
    abs(otif_model - otif_lake) < 1e-9,
    f"Modell {otif_model:.6f}, Lakehouse {otif_lake:.6f}",
)
check(
    "[OTIF-Quote %] = validierter Referenzwert",
    abs(otif_model - EXPECTED_OTIF_RATE) <= RATE_TOLERANCE,
    f"Modell {otif_model:.4%}, erwartet {EXPECTED_OTIF_RATE:.2%}",
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## 5. Auswertung und Abbruch
# **Logik:** Alle Ergebnisse werden zusammengefasst. Schlägt mindestens ein Test fehl, wirft das Notebook einen `AssertionError` mit der vollständigen Liste der Verstöße. Die Notebook-Aktivität einer Fabric-Pipeline endet damit als fehlgeschlagen, nachgelagerte Schritte (z. B. Benachrichtigung „Bericht aktualisiert“) laufen nicht mehr.

# CELL ********************

fact.unpersist()

failed = [r for r in results if not r["passed"]]
print(f"\n{len(results) - len(failed)} von {len(results)} Tests bestanden.")

if failed:
    report = "\n".join(f"- {r['test']}: {r['detail']}" for r in failed)
    raise AssertionError(
        f"Datenqualitätstests fehlgeschlagen ({len(failed)} von {len(results)}):\n{report}"
    )

print("Alle Datenqualitätstests bestanden.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
