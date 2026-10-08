# Case Study: Refactoring & IBCS-Standardisierung der Carrier-Analyse

Stand: September 2026 · Format: Power BI Enhanced Report Format (PBIR)
Seiten-ID: `64ffaee9178b1930a0d5` · Canvas: 1920x1080 · Theme: "Mirza Data Supply Chain v2"

---

## 1. Ausgangsbefund & UX-Audit (Messung via PBIR JSON)

| # | Problem | Technischer Beleg aus der Definition |
|---|---------|--------------------------------------|
| 1 | **Keine Slicer auf der Seite** | Seiten "Übersicht" und "Routen" haben je 4 Slicer bei y=112. Carrier sprang vom Header direkt in die Charts. |
| 2 | **Raster gebrochen** | Bar x=24/w=948, Scatter x=972/w=948 → rechte Kante bei 1920 (0 px Außenrand). Tabelle x=40/w=1840 war ein drittes Margin-System. |
| 3 | **Subpixel-Koordinaten** | Ungenaue Fließkommawerte im Header und Scatter (x=23.808680, y=15.305580, h=79.929141, y=112.857143). |
| 4 | **Gestörter vertikaler Rhythmus** | Content startete bei y=113 statt y=216 (wie auf Seite 1 und 3); unten blieben nach der Tabelle 90 px toter Raum. |
| 5 | **Unstrukturierte Tabellendaten** | Standard-Tabelle belegte 37 % der Fläche für 15 Zeilen x 6 Spalten ohne bedingte Formatierung, Datenbalken oder Sortierung. |
| 6 | **Unvollständige Risiko-Matrix** | Nur eine X-Referenzlinie (400.000 t·km) vorhanden. Ohne Y-Linie beim 95 %-Ziel fehlte die 4-Quadranten-Trennung. |
| 7 | **Anonyme Datenpunkte** | Keine Kategorie-Datenbeschriftung im Scatter-Plot → jeder Carrier musste einzeln gehovert werden. |
| 8 | **Default-Label sichtbar** | Referenzlinie trug den Standardnamen `X-Axis Constant Line 1`. |
| 9 | **Fehlender Management-Anker** | Keine KPI-Karten zur aggregierten Ersteinschätzung des Portfoliorisikos. |

---

## 2. Raster-Architektur (Konsistentes 24-px-System)

Zur Harmonisierung über alle drei Berichtsseiten wurde ein striktes **24er-Raster** definiert:

- Außenrand: **24 px**, Gutter (Spaltenabstand): **24 px**
- 4 Spalten à **450 px** → Nutzbare Inhaltsbreite: 1.872 px (x = 24 … 1.896)
- 2 Hauptblöcke à **924 px** (24 + 924 + 24 + 924 = 1.896)
- Vertikale Zonierung:
  - Header: y = 16
  - Globalfilter: y = 112
  - KPI-Ebene: y = 216
  - Analyseblöcke (Bar / Scatter): y = 376
  - Detail-Scorecard: y = 728 (Abschluss Unterkante: 1.056 px = 24 px Rand)

---

## 3. Layout-Bauplan Seite "Carrier"

| Zone | Visual | Typ | x | y | w | h | tabOrder |
|------|--------|-----|---|---|---|---|---|
| Header | Titel + Subline | `textbox` | 24 | 16 | 1398 | 80 | 0 |
| Header | Seitennavigation | `pageNavigator` | 1470 | 24 | 420 | 32 | 1000 |
| Filter | Zeitraum (Date, Between) | `slicer` | 24 | 112 | 450 | 90 | 2000 |
| Filter | carrier_type | `slicer` | 498 | 112 | 450 | 80 | 2100 |
| Filter | customer_segment | `slicer` | 972 | 112 | 450 | 80 | 2200 |
| Filter | region | `slicer` | 1446 | 112 | 450 | 80 | 2300 |
| KPI | OTIF-Quote % (+ Δ Ziel) | `cardVisual` | 24 | 216 | 450 | 136 | 3000 |
| KPI | Bester Carrier (OTIF %) | `cardVisual` | 498 | 216 | 450 | 136 | 3100 |
| KPI | Schwächster Carrier (OTIF %) | `cardVisual` | 972 | 216 | 450 | 136 | 3200 |
| KPI | Carrier-Spreizung OTIF (pp) | `cardVisual` | 1446 | 216 | 450 | 136 | 3300 |
| Block A | Carrier-Ranking vs. Ziel | `clusteredBarChart` | 24 | 376 | 924 | 328 | 4000 |
| Block A | Risiko-Matrix (4 Quadranten) | `scatterChart` | 972 | 376 | 924 | 328 | 4100 |
| Block B | Carrier-Scorecard | `tableEx` | 24 | 728 | 1872 | 328 | 5000 |

---

## 4. Bereitgestellte DAX-Measures (Direct Lake Semantikmodell)

```dax
Carrier unter Ziel =
VAR Ziel = [OTIF Ziel %]
RETURN
COUNTROWS (
    FILTER (
        VALUES ( dim_carrier[carrier_name] ),
        NOT ISBLANK ( [OTIF-Quote %] ) && [OTIF-Quote %] < Ziel
    )
)

Transportleistung im Risiko (t·km) =
VAR Ziel = [OTIF Ziel %]
RETURN
SUMX (
    FILTER (
        VALUES ( dim_carrier[carrier_name] ),
        NOT ISBLANK ( [OTIF-Quote %] ) && [OTIF-Quote %] < Ziel
    ),
    [Gesamt Tonnen-km]
)

Schwächster Carrier (OTIF %) =
MINX (
    FILTER ( VALUES ( dim_carrier[carrier_name] ), NOT ISBLANK ( [OTIF-Quote %] ) ),
    [OTIF-Quote %]
)

Ø t·km je Carrier =
AVERAGEX ( VALUES ( dim_carrier[carrier_name] ), [Gesamt Tonnen-km] )

Insight Carrier Top/Flop =
VAR Top3 =
    CONCATENATEX (
        TOPN ( 3, VALUES ( dim_carrier[carrier_name] ), [OTIF-Quote %], DESC ),
        dim_carrier[carrier_name] & " " & FORMAT ( [OTIF-Quote %], "0.0%" ),
        "  ·  ", [OTIF-Quote %], DESC
    )
VAR Flop3 =
    CONCATENATEX (
        TOPN ( 3, VALUES ( dim_carrier[carrier_name] ), [OTIF-Quote %], ASC ),
        dim_carrier[carrier_name] & " " & FORMAT ( [OTIF-Quote %], "0.0%" ),
        "  ·  ", [OTIF-Quote %], ASC
    )
RETURN
"Top 3: " & Top3 & "      Flop 3: " & Flop3
```

---

## 5. Technische Umsetzung auf PBIR-Ebene

Basispfad: `./rp_supplychain_overview.Report/definition/pages/`

### 5.1 Positionen bestehender Visuals korrigieren

`64ffaee9178b1930a0d5/visuals/0117d33d00ee366e4631/visual.json` (Header-Textbox):

```json
"position": { "x": 24, "y": 16, "z": 0, "height": 80, "width": 1398, "tabOrder": 0 }
```

`64ffaee9178b1930a0d5/visuals/49f4f939e99c6e4729dd/visual.json` (Bar-Chart):

```json
"position": { "x": 24, "y": 376, "z": 4000, "height": 328, "width": 924, "tabOrder": 4000 }
```

`64ffaee9178b1930a0d5/visuals/633dddae19d2a4d63d01/visual.json` (Scatter):

```json
"position": { "x": 972, "y": 376, "z": 4100, "height": 328, "width": 924, "tabOrder": 4100 }
```

`64ffaee9178b1930a0d5/visuals/570102400a0670ba5eba/visual.json` (Tabelle):

```json
"position": { "x": 24, "y": 728, "z": 5000, "height": 328, "width": 1872, "tabOrder": 5000 }
```

### 5.2 Slicer-Zeile ergänzen

| Quelle (Seite `539fde1e5b2116483bb0`) | Feld | Ziel-Visualname | position |
| --- | --- | --- | --- |
| `visuals/37c1096b93587575ac07` | dim_date[Date] | `7b1e4c0a92d3f5016a41` | x 24, y 112, w 450, h 90, tab 2000 |
| `visuals/b82da107c90d85ecca52` | dim_carrier[carrier_type] | `7b1e4c0a92d3f5016a42` | x 498, y 112, w 450, h 80, tab 2100 |
| `visuals/dda4225500091949c437` | dim_customer[customer_segment] | `7b1e4c0a92d3f5016a43` | x 972, y 112, w 450, h 80, tab 2200 |
| `visuals/6555e7ef228a90a5195e` | dim_customer[region] | `7b1e4c0a92d3f5016a44` | x 1446, y 112, w 450, h 80, tab 2300 |

### 5.3 KPI-Karten (Visual Containers)

**Karte 2 (`3e9f21b7c4a80d6512f2`):**

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json",
  "name": "3e9f21b7c4a80d6512f2",
  "position": { "x": 498, "y": 216, "z": 3100, "height": 136, "width": 450, "tabOrder": 3100 },
  "visual": {
    "visualType": "cardVisual",
    "query": {
      "queryState": {
        "Data": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": { "SourceRef": { "Entity": "_Measures" } },
                  "Property": "Carrier unter Ziel"
                }
              },
              "queryRef": "_Measures.Carrier unter Ziel",
              "nativeQueryRef": "Carrier unter Ziel"
            }
          ]
        }
      }
    },
    "objects": {
      "accentBar": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#C00000'" } } } } }
          },
          "selector": { "id": "default" }
        }
      ]
    },
    "drillFilterOtherVisuals": true
  }
}
```

*Karten 3 und 4 werden analog mit den Measures `Transportleistung im Risiko (t·km)` (x=972, z=3200) und `Schwächster Carrier (OTIF %)` (x=1446, z=3300) angelegt.*

### 5.4 Bar-Chart: Zielmarke & dynamische Subline

In `49f4f939e99c6e4729dd/visual.json`:

```json
"y1AxisReferenceLine": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "displayName": { "expr": { "Literal": { "Value": "'Ziel 95 %'" } } },
      "value": { "expr": { "Literal": { "Value": "0.95D" } } },
      "lineColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#2D3748'" } } } } },
      "transparency": { "expr": { "Literal": { "Value": "0D" } } },
      "width": { "expr": { "Literal": { "Value": "2D" } } },
      "style": { "expr": { "Literal": { "Value": "'dashed'" } } },
      "dataLabelShow": { "expr": { "Literal": { "Value": "true" } } },
      "dataLabelText": { "expr": { "Literal": { "Value": "'Value'" } } },
      "dataLabelColor": { "solid": { "color": { "expr": { "Literal": { "Value": "'#2D3748'" } } } } },
      "dataLabelHorizontalPosition": { "expr": { "Literal": { "Value": "'right'" } } }
    },
    "selector": { "id": "1" }
  }
]
```

### 5.5 Risiko-Matrix: Quadranten & Datenlabels

In `633dddae19d2a4d63d01/visual.json`:

```json
"categoryLabels": [
  {
    "properties": {
      "show": { "expr": { "Literal": { "Value": "true" } } },
      "fontSize": { "expr": { "Literal": { "Value": "9D" } } },
      "color": { "solid": { "color": { "expr": { "Literal": { "Value": "'#586476'" } } } } }
    }
  }
]
```

### 5.6 Carrier-Scorecard

In `570102400a0670ba5eba/visual.json`:

* Projektion geordnet: `carrier_name`, `carrier_type`, `Anzahl Sendungen`, `Verspätete Sendungen`, `Ø Verzögerung Tage`, `Gesamt Tonnen-km`, `OTIF-Quote %`, `OTIF Abweichung pp`.
* Feste Spaltenbreiten.
* Absteigende Sortierung nach `Gesamt Tonnen-km`.

---

## 6. Visuelle IBCS-Formatierung (Power BI Desktop UI)

1. **Integrierte Datenbalken:** Auf Spalten `Anzahl Sendungen` und `Gesamt Tonnen-km`.
2. **Konditionale Formatierung:**
   * Hintergrund von `OTIF-Quote %` als einfarbiger Verlauf von Hellgrau (`#E2E8F0`) zu Marineblau (`#1A365D`).
   * Schriftfarbe auf `OTIF Abweichung pp` via Feldwert `OTIF Farbe relativ`: Terrakotta nur bei deutlichen Ausreißern, sonst Grau.

---

## 7. Wechselwirkungssteuerung (`page.json`)

Entkopplung der Portfolio-Risikokennzahlen bei Selektion einzelner Carrier in `64ffaee9178b1930a0d5/page.json`:

```json
"visualInteractions": [
  { "source": "49f4f939e99c6e4729dd", "target": "3e9f21b7c4a80d6512f2", "type": "NoFilter" },
  { "source": "49f4f939e99c6e4729dd", "target": "3e9f21b7c4a80d6512f3", "type": "NoFilter" },
  { "source": "49f4f939e99c6e4729dd", "target": "3e9f21b7c4a80d6512f4", "type": "NoFilter" },
  { "source": "633dddae19d2a4d63d01", "target": "3e9f21b7c4a80d6512f2", "type": "NoFilter" },
  { "source": "633dddae19d2a4d63d01", "target": "3e9f21b7c4a80d6512f3", "type": "NoFilter" },
  { "source": "633dddae19d2a4d63d01", "target": "3e9f21b7c4a80d6512f4", "type": "NoFilter" }
]
```

---

## 8. Empfohlene Implementierungsreihenfolge

1. **Measures anlegen:** DAX-Logiken im Semantikmodell bereitstellen (Abschnitt 4).
2. **Positionen anpassen:** Bestehende Container auf das 24er-Raster setzen (5.1).
3. **Container ergänzen:** Slicer und KPI-Karten integrieren (5.2, 5.3).
4. **Visuelle Logik patchen:** Bar-Chart- und Scatter-Definitionen aktualisieren (5.4, 5.5).
5. **Scorecard ausrichten:** Tabellenspalten und Sortierung festlegen (5.6).
6. **UI-Finishing:** Datenbalken und bedingte Formatierung in Desktop aktivieren (Abschnitt 6).
7. **Interaktionen sichern:** Filterentkopplung in `page.json` hinterlegen (Abschnitt 7).

---

## 9. Abnahmekriterien & Validierung

* [x] Durchgängiges 24-px-Raster (x = 24 bis 1.896) ohne Canvas-Überlauf.
* [x] Keine Subpixel-Fließkommawerte im Container-Layout.
* [x] Vier Slicer auf y=112 konsistent zu Seite 1 und 3.
* [x] Vollständige 4-Quadranten-Abgrenzung in der Risiko-Matrix.
* [x] Standard-Labels bereinigt; Carrier-Namen direkt lesbar.
* [x] Scorecard mit Datenbalken und einfarbigem Verlauf der Liefertreue operativ nutzbar.
* [x] Portfolio-KPIs bleiben bei Carrier-Interaktion stabil.

---

## 10. Nachträgliche Korrekturen (Oktober 2026)

Beim Prüfen in Power BI Desktop nach dem Umbau aufgefallen und behoben:

* **Raster:** Header-Textbox, eine KPI-Karte und zwei Content-Blöcke trugen noch Subpixel-Werte (zum Beispiel y = 725,64 oder x = 23,33) und lagen teils unter der Rasterkante von 1056. Alle Werte stehen jetzt auf ganzen Zahlen des Rasters.
* **Slicer-Titel:** Auf der Carrier-Seite standen die Rohfeldnamen (`carrier_type`, `region`). Sie heißen jetzt wie auf der Übersicht: Zeitraum, Carrier-Typ, Kundensegment, Region. Die Header-Schriftgröße ist auf allen Seiten explizit 12.
* **Wertachse Übersicht:** Das Balkendiagramm „Verspätete Sendungen nach Kundensegment“ hatte eine feste Achsenobergrenze von 100, die Werte reichen bis 218. Die Obergrenze ist entfernt.
* **Vierte KPI-Karte:** `Anteil Risiko-Volumen %` stand dauerhaft auf 100 %, weil alle Carrier unter dem Ziel von 95 % liegen. Damit wiederholte die Karte die Aussage der beiden Nachbarkarten. Sie ist durch `Schwächster Carrier (OTIF %)` ersetzt (aktuell 65,7 %), das Measure `Anteil Risiko-Volumen %` ist entfernt.
* **Offen:** Die Carrier-Scorecard hat 15 Zeilen und scrollt im vorgesehenen Block. Ein Top-N-Filter müsste in Power BI Desktop gesetzt werden und ist nicht umgesetzt.
* **Zweite Runde bei den KPI-Karten:** „Carrier unter Ziel“ (15 von 15) und „Transportleistung im Risiko“ (5 Mio. bei 4,81 Mio. gesamt) waren auf diesen Daten gesättigt und sagten praktisch „alle“. Die Karten zeigen jetzt Bester Carrier (OTIF %), Schwächster Carrier (OTIF %) und die Spreizung dazwischen in Prozentpunkten. Die Measures `Carrier unter Ziel` und `Transportleistung im Risiko (t·km)` sind entfernt.
* **Untertitel Ranking-Chart:** Der Text „Top 3 … Flop 3 …“ wurde abgeschnitten und zeigte englische Dezimalpunkte. Er zeigt jetzt Top 1 und Flop 1 mit deutschem Zahlenformat (`Insight Carrier Top/Flop`).
* Die Abschnitte 3, 4 und 5.3 beschreiben den Umbau im ursprünglichen Stand und führen die entfernten Measures noch auf.
