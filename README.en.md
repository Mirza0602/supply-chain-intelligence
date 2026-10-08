# Supply Chain Intelligence – Fabric End-to-End

*Deutsche Version (vollständig): [README.md](README.md). This is a shorter English summary. Detailed documentation, such as the data agent test, is in German.*

Portfolio demo project: logistics data moves through a medallion architecture (bronze, silver, gold) on Microsoft Fabric, is served through a Direct Lake semantic model and analysed in a three-page Power BI report.

The data is **synthetic**. The project shows approach, modelling and quality assurance, not results from a real company. It is not a client project.

## What it shows

- A data flow from raw CSV files to a report on Fabric, developed with Azure DevOps as the source of truth. This repository is a snapshot of the state in October 2026.
- A star schema in the lakehouse and a Direct Lake model on top of it, with measures kept in the repository instead of in web modelling.
- Data quality tests that catch wrong figures before they reach the report.
- A report with a fixed layout grid and a consistent theme.

What it is **not**: a production system. There is no automated deployment pipeline, no pull request review and no load testing. Statements about performance are not measured. The data agent is a draft (not published, tested once). The Fabric capacity is paused.

Built with AI assistance (Claude Code). Architecture, decisions, troubleshooting and verification of results are mine.

## Data

| | |
|---|---|
| Source | `data/generate_raw_data.py` creates the CSV files in `data/raw/` (fixed seed 42) |
| Size | 3,000 shipments, 15 carriers, 50 customers, 80 materials, 40 routes |
| Period | Orders 01/2025 to 08/2026, reference date 12 Sep 2026 |
| Main metric | OTIF rate = shipments delivered on time / shipments delivered (currently 81.85%), target 95% |

## Architecture

```text
data/raw/*.csv
      |  nb_bronze_ingestion       raw data as Delta tables (bronze_*)
      v
Bronze
      |  nb_silver_transformation  typing, delay in days, OTIF flag
      v
Silver (silver_*)
      |  nb_gold_transformation    dimensions, fact table, date dimension
      v
Gold (lakehouse lh_supplychain)
      |  Direct Lake
      v
Semantic model sm_supplychain_gold
      |  PBIR, byPath
      v
Report rp_supplychain_overview
```

Two further notebooks act as a quality stage: `nb_data_quality_tests` checks gold and the model after transformation, `nb_model_bpa` runs the Best Practice Analyzer on the semantic model.

## Semantic model

- Tables: `fact_shipments`, `dim_carrier`, `dim_customer`, `dim_date`, `dim_material`, `dim_route`, the measure table `_Measures` and the calculation group `CG_Metric_Switch` (shipment volume or transport performance).
- Direct Lake: the model reads Delta tables from OneLake, there is no import refresh.
- Measures live in `sm_supplychain_gold.SemanticModel/definition/tables/_Measures.tmdl`.

## Report

Three pages (overview, carrier, routes), 1920 x 1080, a 24 px grid with four columns of 450 px. Colours and metric display are loosely based on IBCS without implementing the standard in full. Screenshots are in the [German README](README.md#report).

## Data quality

`nb_data_quality_tests` runs 20 checks: referential integrity, a regression test for the delay logic, plausibility of quantities and weights, a reconciliation of the model's DAX measures via Semantic Link, and a final evaluation that fails the run if any check fails.

Two real errors from development are documented:

- The delay logic depended on a status field. 351 shipments got neither a delay nor a flag, and the report showed 176 instead of 527 late shipments, without anything crashing. The regression test catches exactly that.
- Two consecutive lines in the gold notebook both set `weight_kg`; the second overwrote the first and left 0.00 for 154 shipments. No visual uses the column, so the report stayed correct. The plausibility test stopped the run, the lines were removed and all 20 tests passed again.

## AI layer: data agent

A Fabric data agent (`ag_supplychain`, draft) sits on the semantic model and answers questions in natural language. Ten test questions were run before and after adding instructions (details in German: [docs/ki-agent-test.md](docs/ki-agent-test.md)).

In short: seven of ten answers were correct without instructions. The agent read "OTIF" as "On Time In Full" and described 2,376 on-time shipments as "complete", although the model only captures punctuality. With instructions this was fixed. One detail query (late shipments in February) then ended in a timeout; the agent said so openly and invented nothing.

## Working model: three copies

Azure DevOps `main` is the single source of truth. The Fabric workspace is connected to it through Git integration, the local clone through push and pull. Notebooks are edited in Fabric, report layout and model locally. The full rules are in [CLAUDE.md](CLAUDE.md) (German).

## Deployment

1. Clone the repository:
   ```bash
   git clone https://github.com/Mirza0602/supply-chain-intelligence.git
   ```
2. Connect a Fabric workspace to branch `main` and run "Update all" in source control.
3. Run the notebooks in order: `nb_bronze_ingestion`, `nb_silver_transformation`, `nb_gold_transformation`, then `nb_data_quality_tests`.
4. Open `rp_supplychain_overview.pbip` in Power BI Desktop.

## License

MIT, see [LICENSE](LICENSE). All data is synthetic (`data/generate_raw_data.py`). Any resemblance to real companies is coincidental.
