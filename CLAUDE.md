# CLAUDE.md — supply-chain-intelligence

Projektregeln für Claude Code. Diese Datei ersetzt die früheren Einzel-Arbeitsaufträge:
Was hier steht, gilt für jede Änderung am Report und am Modell.

## Projekt

Portfolio-Demoprojekt "Fabric Supply Chain End-to-End": Bronze/Silver/Gold auf Microsoft
Fabric, PySpark-Notebooks, Direct-Lake-Semantikmodell, Power-BI-Report mit drei Seiten.
Zweck ist ein vorzeigbares Fabric-Referenzprojekt — Optik und fachliche Stringenz zählen
so viel wie die Technik.

Remote: Azure DevOps `midata-de/supply-chain-intelligence`, Fabric-Workspace `ws-dev-analytics`.

## Struktur

```
data/                              Generator + synthetische Rohdaten (CSV)
nb_bronze_ingestion.Notebook/      Bronze-Ingestion
nb_silver_transformation.Notebook/ Bereinigung, OTIF-Flag, Delay
nb_gold_transformation.Notebook/   Dimensionen, Fact, Dim_Date
nb_data_quality_tests.Notebook/    Datenqualitätstests
nb_model_bpa.Notebook/             Best Practice Analyzer auf dem Modell
sm_supplychain_gold.SemanticModel/ TMDL — Tabellen, Beziehungen, Measures
rp_supplychain_overview.Report/    PBIR — Seiten und Visuals
docs/                              Screenshots für Case Study
```

Der Report zeigt per `byPath` auf das lokale Semantikmodell — Measures werden im Repo
gepflegt (`sm_supplychain_gold.SemanticModel/definition/tables/_Measures.tmdl`),
nicht in der Fabric-Web-Modellierung.

## PBIR-Konventionen (Report)

- Jedes Visual ist ein eigener Ordner unter `definition/pages/<pageId>/visuals/<visualId>/visual.json`.
  **Der Ordnername muss identisch sein mit der `name`-Property in der Datei.**
- Dateien sind UTF-8 mit CRLF, Einrückung 2 Leerzeichen, `$schema` bleibt erste Property.
- Beim Bearbeiten: JSON laden, ändern, mit `indent=2` zurückschreiben und CRLF erhalten.
- Nach jeder Änderung: jede berührte Datei mit einem JSON-Parser gegenlesen.
- Seitenreihenfolge steht in `definition/pages/pages.json` (`pageOrder`).

Seiten-IDs:
| Seite | ID |
|---|---|
| Übersicht | `539fde1e5b2116483bb0` |
| Carrier | `64ffaee9178b1930a0d5` |
| Routen | `4495d9cad802d2a65008` |

## Design-System

Canvas 1920x1080, `displayOption: FitToPage`.

**Horizontales Raster:** Außenrand 24, Gutter 24, vier Spalten à 450.
Inhaltsbreite 1872, x läuft von 24 bis 1896.
Erlaubte x-Startwerte: 24 · 498 · 972 · 1446. Halbe Breite = 924. Drittel = 613/614.

**Vertikales Raster:**
| Zone | y | Höhe |
|---|---|---|
| Header-Textbox | 16 | 80 |
| pageNavigator (x=1470, w=420) | 24 | 32 |
| Slicer-Zeile | 112 | 80 (Datums-Slicer 90) |
| KPI-Karten | 216 | 136 |
| Content-Block A | 376 | 328 |
| Content-Block B | 728 | 328 |

Unterkante des letzten Visuals = 1056. Keine Subpixel-Koordinaten — alle Positions- und
Größenwerte sind ganze Zahlen.

**Theme** `Mirza_Data_Supply_Chain_v223260744685180235.json` (RegisteredResources):
Akzent `#13325B`, Primärdaten `#1F66B8`, Text `#1E2733`, Sekundärtext `#586476`,
Tertiär `#8A94A6`, Rahmen `#D8E0EA` (Radius 8), Flächen hell `#F5F8FC`,
gut `#548235`, schlecht `#C00000`.
Farben nie hart ins Visual schreiben, wenn das Theme sie liefert.

## Measures

Alle Measures liegen in der Tabelle `_Measures`. Kartenbeschriftungen kommen aus dem
Measure-Namen — Namen deshalb so wählen, dass sie im Visual lesbar sind
(z. B. `Transportleistung im Risiko (t·km)`, nicht `RiskTkm`).

Konventionen im Bestand: Zielwert über `OTIF Ziel %` (0.95), Abweichung in Prozentpunkten
über `OTIF Abweichung pp`, Farbsteuerung über Farb-Measures (`OTIF-Ampel`,
`OTIF Farbe relativ`, `Carrier Balkenfarbe`, `Heatmap Farbe OTIF`), dynamische Titel über
`Titel …`-Measures. Neue Logik an diese Muster anschließen statt parallele Mechanik bauen.

## Was NICHT ins JSON geschrieben wird

Diese Formatierungen in Power BI Desktop setzen, nicht von Hand serialisieren — ihre
PBIR-Struktur ist versionsabhängig, ein fehlerhafter Block macht den Report unöffenbar:

- Datenbalken in Tabellen
- Hintergrund-/Schriftfarbe nach Feldwert (bedingte Formatierung über Farb-Measures)
- Sparkline-Spalten
- Top-N-Filter auf Visualebene

## Drei Kopien — Fabric, Repo, lokaler Clone

Es gibt drei Orte, an denen dieses Projekt existiert:

| Ort | Rolle |
|---|---|
| Azure DevOps `main` | **einzige Wahrheit** |
| Fabric-Workspace `ws-dev-analytics` | Arbeitskopie, per Git-Integration an `main` gekoppelt |
| Lokaler Clone (Windows) | Arbeitskopie, per push/pull an `main` gekoppelt |

Fabric committet selbst in den Branch (Commits heißen dort
`Committing N items from workspace …`). Dadurch kann der lokale Clone hinter `main`
liegen, ohne dass lokal jemand etwas getan hat.

**Grundregel: nie zwei Seiten gleichzeitig ändern.** Eine Seite ändern, synchronisieren,
dann erst die andere.

Feste Heimat je Artefakt, damit sich beide Seiten nicht in dieselbe Datei schreiben:

| Artefakt | Bearbeitet wird in | Danach |
|---|---|---|
| Notebooks (Bronze/Silver/Gold, DQ, BPA), Lakehouse | Fabric | dort sofort committen |
| Report-Layout (PBIR) | lokal (Claude Code / Desktop) | push, dann in Fabric „Alle aktualisieren" |
| Semantikmodell (TMDL, Measures) | lokal (`_Measures.tmdl` oder Desktop) | push, dann in Fabric „Alle aktualisieren" |

`sm_supplychain_gold.SemanticModel/definition/expressions.tmdl` **nie von Hand ändern** —
darin stehen Workspace- und Lakehouse-GUID der Direct-Lake-Bindung. Eine veraltete
Version davon zu pushen bricht die Verbindung zum Lakehouse.

Ablauf zu Beginn jeder Arbeitssession:
1. Fabric → Workspace → Quellcodeverwaltung: stehen dort nicht committete Änderungen?
   Wenn ja, zuerst dort committen.
2. Lokal: `git status` leer? `git pull --rebase` durchlaufen lassen.
3. Erst dann mit der Arbeit beginnen.

Ablauf am Ende: lokal committen und pushen, dann in Fabric „Alle aktualisieren".

**Modelländerungen testen:** Desktop lädt das Direct-Lake-Modell aus Fabric (Livebearbeitung),
nicht aus dem lokalen TMDL-Ordner. Ein neues Measure aus dem Repo existiert in Desktop erst,
nachdem es auf `main` liegt und in Fabric „Alle aktualisieren" gelaufen ist — vorher meldet
ein Visual darauf `Missing_References`. Reihenfolge deshalb: nach `main` pushen, in Fabric
aktualisieren, dann in Desktop prüfen. Nicht „New measure" in Desktop anlegen. Gibt es in
Fabric danach einen Konflikt am Modell, die Git-Version („Eingehende Änderungen annehmen") übernehmen.
Nach „Alle aktualisieren" den Report im Browser mit **Strg+Umschalt+R** hart neu laden (oder im
Inkognito-Fenster öffnen): Titel, Untertitel und Farben aus Format-Measures werden sonst teils
noch aus dem Cache gezeigt, obwohl das Modell schon aktuell ist.

## Git

Auf Windows arbeiten (Git Bash). Branch-Konvention `feature/<thema>`, Commits im
Conventional-Commits-Stil (`feat(report):`, `fix(model):`, `refactor(data):`).

Wenn eine Session über die Linux-Bridge (Cowork) auf das Repo zugreift, **dort überhaupt
kein `git` ausführen** — auch kein `git status`. Zwei Gründe:

- Das Arbeitsverzeichnis hat CRLF. Ein Linux-Git ohne `core.autocrlf` meldet alle ~78
  Dateien als geändert (symmetrische Insertions/Deletions); ein `git add -A` von dort
  committet einen Zeilenenden-Rewrite des gesamten Repos.
- Git legt beim Lesen `.git/index.lock` an und kann sie über den Mount nicht wieder
  entfernen. Die liegengebliebene Lock-Datei blockiert anschließend jeden Commit auf
  Windows („Unable to create index.lock: File exists"). Abhilfe: Datei löschen.

Dateien lesen und bearbeiten ist über die Bridge unproblematisch — nur Git nicht.

## Prüfliste nach Report-Änderungen

1. Jede geänderte `visual.json` ist valides JSON
2. `name`-Property == Ordnername, alle Namen auf der Seite eindeutig
3. Positions- und Größenwerte ganzzahlig
4. Linke Kante 24, rechte Kante 1896, Unterkante ≤ 1056
5. `visualInteractions` in `page.json` zeigen nur auf existierende Visual-IDs
6. Report in Power BI Desktop öffnen, bevor committet wird

## Arbeitsweise

Analyse, Fachlogik und Layout-Konzepte werden besprochen, bevor umgebaut wird.
Bei Änderungen am Report: erst den Ist-Zustand aus der Definition auslesen und die
Abweichung benennen, dann ändern — nicht auf Verdacht umbauen.
