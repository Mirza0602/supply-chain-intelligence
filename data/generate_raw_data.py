#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Erzeugt synthetische, referenziell integre Supply-Chain-Rohdaten (CSV).

Ausgabe: data/raw/{customers,materials,carriers,routes,shipments}.csv
Ausfuehren: python data/generate_raw_data.py
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_SHIPMENTS = 3000
PERIOD_START = date(2025, 1, 1)
PERIOD_END = date(2026, 8, 31)
SNAPSHOT = date(2026, 9, 12)  # Stichtag fuer In-Transit / offene Delayed

RAW_DIR = Path(__file__).resolve().parent / "raw"

CUSTOMERS: list[dict] = [
    {"customer_id": "CUS-001", "customer_name": "Schwaben Automotive GmbH", "country": "DE", "region": "Baden-Württemberg", "customer_segment": "Automotive"},
    {"customer_id": "CUS-002", "customer_name": "Bayerische Komponenten AG", "country": "DE", "region": "Bayern", "customer_segment": "Automotive"},
    {"customer_id": "CUS-003", "customer_name": "Nordstahl Mobility GmbH", "country": "DE", "region": "Niedersachsen", "customer_segment": "Automotive"},
    {"customer_id": "CUS-004", "customer_name": "Rheinland Auto Parts GmbH", "country": "DE", "region": "Nordrhein-Westfalen", "customer_segment": "Automotive"},
    {"customer_id": "CUS-005", "customer_name": "Sachsen Fahrzeugtechnik GmbH", "country": "DE", "region": "Sachsen", "customer_segment": "Automotive"},
    {"customer_id": "CUS-006", "customer_name": "Hessen Drive Systems GmbH", "country": "DE", "region": "Hessen", "customer_segment": "Automotive"},
    {"customer_id": "CUS-007", "customer_name": "Piemont Auto Forniture S.r.l.", "country": "IT", "region": "Piemont", "customer_segment": "Automotive"},
    {"customer_id": "CUS-008", "customer_name": "Moravia Auto a.s.", "country": "CZ", "region": "Mähren", "customer_segment": "Automotive"},
    {"customer_id": "CUS-009", "customer_name": "Wielkopolska Motoryzacja Sp. z o.o.", "country": "PL", "region": "Wielkopolskie", "customer_segment": "Automotive"},
    {"customer_id": "CUS-010", "customer_name": "Steiermark Fahrzeugteile GmbH", "country": "AT", "region": "Steiermark", "customer_segment": "Automotive"},
    {"customer_id": "CUS-011", "customer_name": "Alsace Automotive SAS", "country": "FR", "region": "Grand Est", "customer_segment": "Automotive"},
    {"customer_id": "CUS-012", "customer_name": "Brabant Mobility B.V.", "country": "NL", "region": "Noord-Brabant", "customer_segment": "Automotive"},
    {"customer_id": "CUS-013", "customer_name": "Neckar Pharma GmbH", "country": "DE", "region": "Baden-Württemberg", "customer_segment": "Pharma"},
    {"customer_id": "CUS-014", "customer_name": "BioValley Therapeutics AG", "country": "DE", "region": "Bayern", "customer_segment": "Pharma"},
    {"customer_id": "CUS-015", "customer_name": "Nordlicht Pharmaceuticals GmbH", "country": "DE", "region": "Hamburg", "customer_segment": "Pharma"},
    {"customer_id": "CUS-016", "customer_name": "Rhein-Main Pharma GmbH", "country": "DE", "region": "Hessen", "customer_segment": "Pharma"},
    {"customer_id": "CUS-017", "customer_name": "Basel Life Sciences AG", "country": "CH", "region": "Basel-Stadt", "customer_segment": "Pharma"},
    {"customer_id": "CUS-018", "customer_name": "Wien Medica GmbH", "country": "AT", "region": "Wien", "customer_segment": "Pharma"},
    {"customer_id": "CUS-019", "customer_name": "Lille Santé SAS", "country": "FR", "region": "Hauts-de-France", "customer_segment": "Pharma"},
    {"customer_id": "CUS-020", "customer_name": "Randstad Pharma B.V.", "country": "NL", "region": "Zuid-Holland", "customer_segment": "Pharma"},
    {"customer_id": "CUS-021", "customer_name": "Südwest Handel AG", "country": "DE", "region": "Baden-Württemberg", "customer_segment": "Retail"},
    {"customer_id": "CUS-022", "customer_name": "Bayern Retail Group GmbH", "country": "DE", "region": "Bayern", "customer_segment": "Retail"},
    {"customer_id": "CUS-023", "customer_name": "Hanseatic Stores GmbH", "country": "DE", "region": "Hamburg", "customer_segment": "Retail"},
    {"customer_id": "CUS-024", "customer_name": "NRW Verbrauchermarkt AG", "country": "DE", "region": "Nordrhein-Westfalen", "customer_segment": "Retail"},
    {"customer_id": "CUS-025", "customer_name": "Berlin Urban Retail GmbH", "country": "DE", "region": "Berlin", "customer_segment": "Retail"},
    {"customer_id": "CUS-026", "customer_name": "Hessen Shopping GmbH", "country": "DE", "region": "Hessen", "customer_segment": "Retail"},
    {"customer_id": "CUS-027", "customer_name": "Sachsen Discount AG", "country": "DE", "region": "Sachsen", "customer_segment": "Retail"},
    {"customer_id": "CUS-028", "customer_name": "Niedersachsen Handel GmbH", "country": "DE", "region": "Niedersachsen", "customer_segment": "Retail"},
    {"customer_id": "CUS-029", "customer_name": "Wien Retail GmbH", "country": "AT", "region": "Wien", "customer_segment": "Retail"},
    {"customer_id": "CUS-030", "customer_name": "Amsterdam Retail B.V.", "country": "NL", "region": "Noord-Holland", "customer_segment": "Retail"},
    {"customer_id": "CUS-031", "customer_name": "Lyon Magasins SAS", "country": "FR", "region": "Auvergne-Rhône-Alpes", "customer_segment": "Retail"},
    {"customer_id": "CUS-032", "customer_name": "Warszawa Handel Sp. z o.o.", "country": "PL", "region": "Mazowieckie", "customer_segment": "Retail"},
    {"customer_id": "CUS-033", "customer_name": "Schwaben Maschinenbau GmbH", "country": "DE", "region": "Baden-Württemberg", "customer_segment": "Industrie"},
    {"customer_id": "CUS-034", "customer_name": "Ruhr Industrieanlagen AG", "country": "DE", "region": "Nordrhein-Westfalen", "customer_segment": "Industrie"},
    {"customer_id": "CUS-035", "customer_name": "Saar Stahlverarbeitung GmbH", "country": "DE", "region": "Saarland", "customer_segment": "Industrie"},
    {"customer_id": "CUS-036", "customer_name": "Franken Anlagenbau GmbH", "country": "DE", "region": "Bayern", "customer_segment": "Industrie"},
    {"customer_id": "CUS-037", "customer_name": "Mittelhessen Technik GmbH", "country": "DE", "region": "Hessen", "customer_segment": "Industrie"},
    {"customer_id": "CUS-038", "customer_name": "Küstenindustrie GmbH", "country": "DE", "region": "Schleswig-Holstein", "customer_segment": "Industrie"},
    {"customer_id": "CUS-039", "customer_name": "Leipzig Process Tech GmbH", "country": "DE", "region": "Sachsen", "customer_segment": "Industrie"},
    {"customer_id": "CUS-040", "customer_name": "Hannover Heavy Industry GmbH", "country": "DE", "region": "Niedersachsen", "customer_segment": "Industrie"},
    {"customer_id": "CUS-041", "customer_name": "Magdeburg Chemieanlagen GmbH", "country": "DE", "region": "Sachsen-Anhalt", "customer_segment": "Industrie"},
    {"customer_id": "CUS-042", "customer_name": "Thüringen Fertigungstechnik GmbH", "country": "DE", "region": "Thüringen", "customer_segment": "Industrie"},
    {"customer_id": "CUS-043", "customer_name": "Brandenburg Metall AG", "country": "DE", "region": "Brandenburg", "customer_segment": "Industrie"},
    {"customer_id": "CUS-044", "customer_name": "Linz Industrie GmbH", "country": "AT", "region": "Oberösterreich", "customer_segment": "Industrie"},
    {"customer_id": "CUS-045", "customer_name": "Antwerpen Process N.V.", "country": "BE", "region": "Antwerpen", "customer_segment": "Industrie"},
    {"customer_id": "CUS-046", "customer_name": "Katowice Steel Sp. z o.o.", "country": "PL", "region": "Śląskie", "customer_segment": "Industrie"},
    {"customer_id": "CUS-047", "customer_name": "Ostrava Machinery a.s.", "country": "CZ", "region": "Moravskoslezský", "customer_segment": "Industrie"},
    {"customer_id": "CUS-048", "customer_name": "Stuttgart Präzision GmbH", "country": "DE", "region": "Baden-Württemberg", "customer_segment": "Industrie"},
    {"customer_id": "CUS-049", "customer_name": "München Hightech GmbH", "country": "DE", "region": "Bayern", "customer_segment": "Industrie"},
    {"customer_id": "CUS-050", "customer_name": "Köln Compound GmbH", "country": "DE", "region": "Nordrhein-Westfalen", "customer_segment": "Industrie"},
]

MATERIALS: list[dict] = [
    {"material_id": "MAT-001", "material_name": "Bremsscheibe vorn", "material_group": "Automotive", "weight_kg_per_unit": 8.50},
    {"material_id": "MAT-002", "material_name": "Bremsscheibe hinten", "material_group": "Automotive", "weight_kg_per_unit": 6.20},
    {"material_id": "MAT-003", "material_name": "Stoßdämpfer", "material_group": "Automotive", "weight_kg_per_unit": 4.80},
    {"material_id": "MAT-004", "material_name": "Querlenker", "material_group": "Automotive", "weight_kg_per_unit": 3.10},
    {"material_id": "MAT-005", "material_name": "Radnabe", "material_group": "Automotive", "weight_kg_per_unit": 5.40},
    {"material_id": "MAT-006", "material_name": "Steuergerät Motor", "material_group": "Automotive", "weight_kg_per_unit": 1.20},
    {"material_id": "MAT-007", "material_name": "Kabelbaum Motorraum", "material_group": "Automotive", "weight_kg_per_unit": 2.80},
    {"material_id": "MAT-008", "material_name": "Scheinwerfer LED", "material_group": "Automotive", "weight_kg_per_unit": 3.60},
    {"material_id": "MAT-009", "material_name": "Außenspiegel komplett", "material_group": "Automotive", "weight_kg_per_unit": 1.90},
    {"material_id": "MAT-010", "material_name": "Sitzeinheit Fahrer", "material_group": "Automotive", "weight_kg_per_unit": 18.50},
    {"material_id": "MAT-011", "material_name": "Katalysator", "material_group": "Automotive", "weight_kg_per_unit": 7.20},
    {"material_id": "MAT-012", "material_name": "Turbolader", "material_group": "Automotive", "weight_kg_per_unit": 6.80},
    {"material_id": "MAT-013", "material_name": "Kupplungssatz", "material_group": "Automotive", "weight_kg_per_unit": 5.10},
    {"material_id": "MAT-014", "material_name": "Batteriemodul 48V", "material_group": "Automotive", "weight_kg_per_unit": 12.40},
    {"material_id": "MAT-015", "material_name": "Felge Aluminium 17 Zoll", "material_group": "Automotive", "weight_kg_per_unit": 11.80},
    {"material_id": "MAT-016", "material_name": "Reifen 225/45 R17", "material_group": "Automotive", "weight_kg_per_unit": 9.50},
    {"material_id": "MAT-017", "material_name": "Ölfilter", "material_group": "Automotive", "weight_kg_per_unit": 0.35},
    {"material_id": "MAT-018", "material_name": "Luftfilter", "material_group": "Automotive", "weight_kg_per_unit": 0.42},
    {"material_id": "MAT-019", "material_name": "Zylinderkopfdichtung", "material_group": "Automotive", "weight_kg_per_unit": 0.28},
    {"material_id": "MAT-020", "material_name": "Antriebswelle", "material_group": "Automotive", "weight_kg_per_unit": 8.90},
    {"material_id": "MAT-021", "material_name": "Ibuprofen 400mg Tabletten", "material_group": "Pharma", "weight_kg_per_unit": 0.08},
    {"material_id": "MAT-022", "material_name": "Paracetamol 500mg Tabletten", "material_group": "Pharma", "weight_kg_per_unit": 0.07},
    {"material_id": "MAT-023", "material_name": "Insulin-Patronen", "material_group": "Pharma", "weight_kg_per_unit": 0.15},
    {"material_id": "MAT-024", "material_name": "Impfstoff Influenza", "material_group": "Pharma", "weight_kg_per_unit": 0.12},
    {"material_id": "MAT-025", "material_name": "Infusionslösung NaCl 0.9%", "material_group": "Pharma", "weight_kg_per_unit": 1.05},
    {"material_id": "MAT-026", "material_name": "Sterile Spritzen 5ml", "material_group": "Pharma", "weight_kg_per_unit": 0.04},
    {"material_id": "MAT-027", "material_name": "Verbandsmaterial steril", "material_group": "Pharma", "weight_kg_per_unit": 0.22},
    {"material_id": "MAT-028", "material_name": "Blutdruckmessgerät", "material_group": "Pharma", "weight_kg_per_unit": 0.65},
    {"material_id": "MAT-029", "material_name": "Diagnostik-Kits PCR", "material_group": "Pharma", "weight_kg_per_unit": 0.18},
    {"material_id": "MAT-030", "material_name": "Antibiotika Ampicillin", "material_group": "Pharma", "weight_kg_per_unit": 0.09},
    {"material_id": "MAT-031", "material_name": "Kühlketten-Insulin Pens", "material_group": "Pharma", "weight_kg_per_unit": 0.21},
    {"material_id": "MAT-032", "material_name": "Medizinische Handschuhe", "material_group": "Pharma", "weight_kg_per_unit": 0.05},
    {"material_id": "MAT-033", "material_name": "Kanülen-Set", "material_group": "Pharma", "weight_kg_per_unit": 0.03},
    {"material_id": "MAT-034", "material_name": "Tablettenblister leer", "material_group": "Pharma", "weight_kg_per_unit": 0.02},
    {"material_id": "MAT-035", "material_name": "Wirkstoff API Losartan", "material_group": "Pharma", "weight_kg_per_unit": 0.55},
    {"material_id": "MAT-036", "material_name": "Laborreagenzien-Set", "material_group": "Pharma", "weight_kg_per_unit": 0.38},
    {"material_id": "MAT-037", "material_name": "Baumwoll-T-Shirt", "material_group": "Retail", "weight_kg_per_unit": 0.18},
    {"material_id": "MAT-038", "material_name": "Jeanshose", "material_group": "Retail", "weight_kg_per_unit": 0.62},
    {"material_id": "MAT-039", "material_name": "Sportschuhe", "material_group": "Retail", "weight_kg_per_unit": 0.78},
    {"material_id": "MAT-040", "material_name": "Winterjacke", "material_group": "Retail", "weight_kg_per_unit": 1.15},
    {"material_id": "MAT-041", "material_name": "Handtuchset", "material_group": "Retail", "weight_kg_per_unit": 0.95},
    {"material_id": "MAT-042", "material_name": "Kaffeemaschine", "material_group": "Retail", "weight_kg_per_unit": 4.20},
    {"material_id": "MAT-043", "material_name": "Bluetooth-Lautsprecher", "material_group": "Retail", "weight_kg_per_unit": 0.85},
    {"material_id": "MAT-044", "material_name": "Smartphone-Hülle", "material_group": "Retail", "weight_kg_per_unit": 0.08},
    {"material_id": "MAT-045", "material_name": "LED-Lampe E27", "material_group": "Retail", "weight_kg_per_unit": 0.12},
    {"material_id": "MAT-046", "material_name": "Geschirrset 12-teilig", "material_group": "Retail", "weight_kg_per_unit": 6.40},
    {"material_id": "MAT-047", "material_name": "Bettwäsche 135x200", "material_group": "Retail", "weight_kg_per_unit": 1.35},
    {"material_id": "MAT-048", "material_name": "Küchenmesser-Set", "material_group": "Retail", "weight_kg_per_unit": 1.80},
    {"material_id": "MAT-049", "material_name": "Spielekonsolen-Zubehör", "material_group": "Retail", "weight_kg_per_unit": 0.45},
    {"material_id": "MAT-050", "material_name": "Haarshampoo 250ml", "material_group": "Retail", "weight_kg_per_unit": 0.28},
    {"material_id": "MAT-051", "material_name": "Waschmittel 3kg", "material_group": "Retail", "weight_kg_per_unit": 3.10},
    {"material_id": "MAT-052", "material_name": "Toilettenpapier 8er", "material_group": "Retail", "weight_kg_per_unit": 1.60},
    {"material_id": "MAT-053", "material_name": "Cerealien 500g", "material_group": "Retail", "weight_kg_per_unit": 0.52},
    {"material_id": "MAT-054", "material_name": "Schokolade 100g", "material_group": "Retail", "weight_kg_per_unit": 0.10},
    {"material_id": "MAT-055", "material_name": "Mineralwasser 6x1.5l", "material_group": "Retail", "weight_kg_per_unit": 9.30},
    {"material_id": "MAT-056", "material_name": "Bürostuhl", "material_group": "Retail", "weight_kg_per_unit": 14.50},
    {"material_id": "MAT-057", "material_name": "Regalbrett Holz", "material_group": "Retail", "weight_kg_per_unit": 4.80},
    {"material_id": "MAT-058", "material_name": "Dekokissen", "material_group": "Retail", "weight_kg_per_unit": 0.55},
    {"material_id": "MAT-059", "material_name": "Stahlcoil kaltgewalzt", "material_group": "Industrie", "weight_kg_per_unit": 1250.00},
    {"material_id": "MAT-060", "material_name": "Aluminiumprofil 6m", "material_group": "Industrie", "weight_kg_per_unit": 18.40},
    {"material_id": "MAT-061", "material_name": "Hydraulikpumpe", "material_group": "Industrie", "weight_kg_per_unit": 42.00},
    {"material_id": "MAT-062", "material_name": "Elektromotor 15kW", "material_group": "Industrie", "weight_kg_per_unit": 85.00},
    {"material_id": "MAT-063", "material_name": "Kugellager 6205", "material_group": "Industrie", "weight_kg_per_unit": 0.12},
    {"material_id": "MAT-064", "material_name": "Industrieventil DN50", "material_group": "Industrie", "weight_kg_per_unit": 3.80},
    {"material_id": "MAT-065", "material_name": "Schaltschrank leer", "material_group": "Industrie", "weight_kg_per_unit": 28.00},
    {"material_id": "MAT-066", "material_name": "Frequenzumrichter", "material_group": "Industrie", "weight_kg_per_unit": 6.50},
    {"material_id": "MAT-067", "material_name": "Förderbandmodul", "material_group": "Industrie", "weight_kg_per_unit": 55.00},
    {"material_id": "MAT-068", "material_name": "Schweißdraht 15kg", "material_group": "Industrie", "weight_kg_per_unit": 15.20},
    {"material_id": "MAT-069", "material_name": "Industriekleber 20l", "material_group": "Industrie", "weight_kg_per_unit": 22.00},
    {"material_id": "MAT-070", "material_name": "Palettenfolie Stretch", "material_group": "Industrie", "weight_kg_per_unit": 16.80},
    {"material_id": "MAT-071", "material_name": "Europalette EPAL", "material_group": "Industrie", "weight_kg_per_unit": 25.00},
    {"material_id": "MAT-072", "material_name": "Kartonage Faltkarton", "material_group": "Industrie", "weight_kg_per_unit": 0.45},
    {"material_id": "MAT-073", "material_name": "Druckluftkompressor", "material_group": "Industrie", "weight_kg_per_unit": 95.00},
    {"material_id": "MAT-074", "material_name": "CNC-Fräswerkzeug", "material_group": "Industrie", "weight_kg_per_unit": 0.85},
    {"material_id": "MAT-075", "material_name": "Dichtungssatz EPDM", "material_group": "Industrie", "weight_kg_per_unit": 0.32},
    {"material_id": "MAT-076", "material_name": "Getriebe i=12", "material_group": "Industrie", "weight_kg_per_unit": 38.00},
    {"material_id": "MAT-077", "material_name": "Sensorik-Paket IO-Link", "material_group": "Industrie", "weight_kg_per_unit": 0.48},
    {"material_id": "MAT-078", "material_name": "Kühlschmierstoff 200l", "material_group": "Industrie", "weight_kg_per_unit": 185.00},
    {"material_id": "MAT-079", "material_name": "Transformator 50kVA", "material_group": "Industrie", "weight_kg_per_unit": 210.00},
    {"material_id": "MAT-080", "material_name": "Rohrleitung DN100 Stahl", "material_group": "Industrie", "weight_kg_per_unit": 12.60},
]

# Fiktive Carrier-Namen: Die Leistungswerte sind erfunden und dürfen keinem
# realen Unternehmen zugeordnet werden. Namen beeinflussen den Zufallsgenerator
# nicht, Sendungsdaten und Kennzahlen bleiben bei einer Umbenennung identisch.
CARRIERS: list[dict] = [
    {"carrier_id": "CAR-001", "carrier_name": "Nordkap Logistik GmbH", "carrier_type": "LKW", "reliability_score": 0.96},
    {"carrier_id": "CAR-002", "carrier_name": "Südring Transporte GmbH", "carrier_type": "LKW", "reliability_score": 0.94},
    {"carrier_id": "CAR-003", "carrier_name": "Rheinbogen Spedition KG", "carrier_type": "LKW", "reliability_score": 0.93},
    {"carrier_id": "CAR-004", "carrier_name": "Alpenpass Cargo GmbH", "carrier_type": "LKW", "reliability_score": 0.92},
    {"carrier_id": "CAR-005", "carrier_name": "Weserland Freight GmbH", "carrier_type": "LKW", "reliability_score": 0.90},
    {"carrier_id": "CAR-006", "carrier_name": "Donaukreis Logistics GmbH", "carrier_type": "LKW", "reliability_score": 0.87},
    {"carrier_id": "CAR-007", "carrier_name": "Mittelland Stückgut Verbund", "carrier_type": "LKW", "reliability_score": 0.85},
    {"carrier_id": "CAR-008", "carrier_name": "Heidetal Spedition GmbH", "carrier_type": "LKW", "reliability_score": 0.81},
    {"carrier_id": "CAR-009", "carrier_name": "Schienenwerk Cargo AG", "carrier_type": "Bahn", "reliability_score": 0.91},
    {"carrier_id": "CAR-010", "carrier_name": "Transalpin Rail GmbH", "carrier_type": "Bahn", "reliability_score": 0.89},
    {"carrier_id": "CAR-011", "carrier_name": "Nordmeer Reederei AG", "carrier_type": "See", "reliability_score": 0.88},
    {"carrier_id": "CAR-012", "carrier_name": "Atlantic Bridge Shipping", "carrier_type": "See", "reliability_score": 0.90},
    {"carrier_id": "CAR-013", "carrier_name": "Mediterra Container Lines", "carrier_type": "See", "reliability_score": 0.84},
    {"carrier_id": "CAR-014", "carrier_name": "Skyline Air Cargo AG", "carrier_type": "Luft", "reliability_score": 0.97},
    {"carrier_id": "CAR-015", "carrier_name": "Aerolink Freight", "carrier_type": "Luft", "reliability_score": 0.95},
]

ROUTES: list[dict] = [
    {"route_id": "RTE-001", "origin_location": "Stuttgart (DE)", "destination_location": "München (DE)", "distance_km": 220, "mode": "Straße"},
    {"route_id": "RTE-002", "origin_location": "Stuttgart (DE)", "destination_location": "Hamburg (DE)", "distance_km": 640, "mode": "Straße"},
    {"route_id": "RTE-003", "origin_location": "Stuttgart (DE)", "destination_location": "Berlin (DE)", "distance_km": 630, "mode": "Straße"},
    {"route_id": "RTE-004", "origin_location": "München (DE)", "destination_location": "Leipzig (DE)", "distance_km": 360, "mode": "Straße"},
    {"route_id": "RTE-005", "origin_location": "Hamburg (DE)", "destination_location": "München (DE)", "distance_km": 780, "mode": "Straße"},
    {"route_id": "RTE-006", "origin_location": "Hamburg (DE)", "destination_location": "Köln (DE)", "distance_km": 430, "mode": "Straße"},
    {"route_id": "RTE-007", "origin_location": "Duisburg (DE)", "destination_location": "Warszawa (PL)", "distance_km": 950, "mode": "Straße"},
    {"route_id": "RTE-008", "origin_location": "Köln (DE)", "destination_location": "Antwerpen (BE)", "distance_km": 190, "mode": "Straße"},
    {"route_id": "RTE-009", "origin_location": "Frankfurt (DE)", "destination_location": "Paris (FR)", "distance_km": 575, "mode": "Straße"},
    {"route_id": "RTE-010", "origin_location": "Mannheim (DE)", "destination_location": "Lyon (FR)", "distance_km": 580, "mode": "Straße"},
    {"route_id": "RTE-011", "origin_location": "Nürnberg (DE)", "destination_location": "Praha (CZ)", "distance_km": 290, "mode": "Straße"},
    {"route_id": "RTE-012", "origin_location": "Dresden (DE)", "destination_location": "Wrocław (PL)", "distance_km": 270, "mode": "Straße"},
    {"route_id": "RTE-013", "origin_location": "Hannover (DE)", "destination_location": "Rotterdam (NL)", "distance_km": 430, "mode": "Straße"},
    {"route_id": "RTE-014", "origin_location": "Berlin (DE)", "destination_location": "Wien (AT)", "distance_km": 680, "mode": "Straße"},
    {"route_id": "RTE-015", "origin_location": "München (DE)", "destination_location": "Milano (IT)", "distance_km": 490, "mode": "Straße"},
    {"route_id": "RTE-016", "origin_location": "Karlsruhe (DE)", "destination_location": "Strasbourg (FR)", "distance_km": 80, "mode": "Straße"},
    {"route_id": "RTE-017", "origin_location": "Dortmund (DE)", "destination_location": "Amsterdam (NL)", "distance_km": 230, "mode": "Straße"},
    {"route_id": "RTE-018", "origin_location": "Leipzig (DE)", "destination_location": "Budapest (HU)", "distance_km": 710, "mode": "Straße"},
    {"route_id": "RTE-019", "origin_location": "Bremen (DE)", "destination_location": "Kopenhagen (DK)", "distance_km": 480, "mode": "Straße"},
    {"route_id": "RTE-020", "origin_location": "Ulm (DE)", "destination_location": "Zürich (CH)", "distance_km": 170, "mode": "Straße"},
    {"route_id": "RTE-021", "origin_location": "Saarbrücken (DE)", "destination_location": "Luxembourg (LU)", "distance_km": 95, "mode": "Straße"},
    {"route_id": "RTE-022", "origin_location": "Freiburg (DE)", "destination_location": "Basel (CH)", "distance_km": 70, "mode": "Straße"},
    {"route_id": "RTE-023", "origin_location": "Hamburg (DE)", "destination_location": "München (DE)", "distance_km": 780, "mode": "Schiene"},
    {"route_id": "RTE-024", "origin_location": "Duisburg (DE)", "destination_location": "Wien (AT)", "distance_km": 920, "mode": "Schiene"},
    {"route_id": "RTE-025", "origin_location": "Köln (DE)", "destination_location": "Milano (IT)", "distance_km": 890, "mode": "Schiene"},
    {"route_id": "RTE-026", "origin_location": "Leipzig (DE)", "destination_location": "Rotterdam (NL)", "distance_km": 620, "mode": "Schiene"},
    {"route_id": "RTE-027", "origin_location": "Stuttgart (DE)", "destination_location": "Berlin (DE)", "distance_km": 630, "mode": "Schiene"},
    {"route_id": "RTE-028", "origin_location": "München (DE)", "destination_location": "Verona (IT)", "distance_km": 410, "mode": "Schiene"},
    {"route_id": "RTE-029", "origin_location": "Hannover (DE)", "destination_location": "Praha (CZ)", "distance_km": 520, "mode": "Schiene"},
    {"route_id": "RTE-030", "origin_location": "Mannheim (DE)", "destination_location": "Lyon (FR)", "distance_km": 590, "mode": "Schiene"},
    {"route_id": "RTE-031", "origin_location": "Hamburg (DE)", "destination_location": "Rotterdam (NL)", "distance_km": 540, "mode": "See"},
    {"route_id": "RTE-032", "origin_location": "Hamburg (DE)", "destination_location": "Shanghai (CN)", "distance_km": 19800, "mode": "See"},
    {"route_id": "RTE-033", "origin_location": "Hamburg (DE)", "destination_location": "Singapore (SG)", "distance_km": 15600, "mode": "See"},
    {"route_id": "RTE-034", "origin_location": "Bremerhaven (DE)", "destination_location": "New York (US)", "distance_km": 6400, "mode": "See"},
    {"route_id": "RTE-035", "origin_location": "Hamburg (DE)", "destination_location": "Göteborg (SE)", "distance_km": 480, "mode": "See"},
    {"route_id": "RTE-036", "origin_location": "Rotterdam (NL)", "destination_location": "Busan (KR)", "distance_km": 20400, "mode": "See"},
    {"route_id": "RTE-037", "origin_location": "Frankfurt (DE)", "destination_location": "New York (US)", "distance_km": 6200, "mode": "Luft"},
    {"route_id": "RTE-038", "origin_location": "Frankfurt (DE)", "destination_location": "Shanghai (CN)", "distance_km": 8400, "mode": "Luft"},
    {"route_id": "RTE-039", "origin_location": "München (DE)", "destination_location": "Chicago (US)", "distance_km": 7350, "mode": "Luft"},
    {"route_id": "RTE-040", "origin_location": "Leipzig (DE)", "destination_location": "Dubai (AE)", "distance_km": 4800, "mode": "Luft"},
]

MODE_TO_CARRIER_TYPE = {"Straße": "LKW", "Schiene": "Bahn", "See": "See", "Luft": "Luft"}

# Segment -> bevorzugter Verkehrstraeger (Gewichte)
SEGMENT_MODE_WEIGHTS = {
    "Automotive": {"Straße": 0.62, "Schiene": 0.22, "See": 0.10, "Luft": 0.06},
    "Pharma": {"Straße": 0.55, "Schiene": 0.08, "See": 0.07, "Luft": 0.30},
    "Retail": {"Straße": 0.78, "Schiene": 0.10, "See": 0.08, "Luft": 0.04},
    "Industrie": {"Straße": 0.50, "Schiene": 0.18, "See": 0.28, "Luft": 0.04},
}

DELAY_REASONS = ("Wetter", "Zoll", "Kapazität", "Sonstiges")
VALID_STATUS = {"Delivered", "In Transit", "Delayed", "Cancelled"}


def fmt_weight(value: float) -> str:
    return f"{value:.2f}"


def fmt_score(value: float) -> str:
    return f"{value:.2f}"


def skip_sunday(d: date) -> date:
    if d.weekday() == 6:
        return d + timedelta(days=1)
    return d


def transit_days(mode: str, distance_km: int, rng: random.Random) -> int:
    if mode == "Straße":
        return max(1, round(distance_km / 550) + rng.choice([0, 1, 1]))
    if mode == "Schiene":
        return max(2, round(distance_km / 450) + rng.choice([1, 2]))
    if mode == "See":
        if distance_km < 1000:
            return rng.randint(3, 7)
        if distance_km < 8000:
            return rng.randint(12, 22)
        return rng.randint(24, 38)
    if mode == "Luft":
        return rng.randint(1, 3)
    raise ValueError(mode)


def delay_probability(reliability: float, mode: str, order_date: date, international: bool) -> float:
    # Basis aus Carrier-Zuverlaessigkeit, skaliert auf Zielkorridor 15-20%
    base = (1.0 - reliability) * 1.35
    if mode == "See":
        base += 0.04
    elif mode == "Schiene":
        base += 0.015
    elif mode == "Luft":
        base -= 0.02
    if international:
        base += 0.025
    if order_date.month in (11, 12, 1, 2):
        base += 0.03
    if order_date.month == 3:
        base += 0.015
    return min(0.42, max(0.04, base))


def pick_delay_reason(order_date: date, mode: str, international: bool, rng: random.Random) -> str:
    weights = {"Wetter": 1.0, "Zoll": 0.35, "Kapazität": 1.1, "Sonstiges": 0.55}
    if order_date.month in (11, 12, 1, 2, 3):
        weights["Wetter"] *= 2.4
    if mode in ("See", "Luft") or international:
        weights["Zoll"] *= 3.2
    if mode == "Luft":
        weights["Wetter"] *= 1.2
    if order_date.month in (9, 11, 12, 3):
        weights["Kapazität"] *= 1.7
    keys = list(weights)
    vals = [weights[k] for k in keys]
    return rng.choices(keys, weights=vals, k=1)[0]


def delay_days(mode: str, reason: str, rng: random.Random) -> int:
    if reason == "Zoll":
        high = 10 if mode == "See" else 6
        return rng.randint(2, high)
    if reason == "Wetter":
        return rng.randint(1, 5 if mode != "See" else 8)
    if reason == "Kapazität":
        return rng.randint(1, 7)
    return rng.randint(1, 4)


def quantity_for(material: dict, rng: random.Random) -> int:
    group = material["material_group"]
    unit_w = material["weight_kg_per_unit"]
    if group == "Automotive":
        return rng.randint(8, 240)
    if group == "Pharma":
        return rng.randint(40, 1600)
    if group == "Retail":
        return rng.randint(24, 520)
    if unit_w >= 200:
        return rng.randint(1, 6)
    if unit_w >= 40:
        return rng.randint(1, 18)
    return rng.randint(6, 90)


def weighted_choice(items: list, weights: list[float], rng: random.Random):
    return rng.choices(items, weights=weights, k=1)[0]


def customer_weights() -> list[float]:
    # Pareto: ein paar Stammkunden ziehen mehr Volumen
    weights = []
    for i, c in enumerate(CUSTOMERS):
        base = 1.0
        if i % 7 == 0:
            base = 2.8
        elif i % 5 == 0:
            base = 1.8
        if c["country"] == "DE":
            base *= 1.25
        weights.append(base)
    return weights


def materials_by_group() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for m in MATERIALS:
        grouped[m["material_group"]].append(m)
    return grouped


def routes_by_mode() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in ROUTES:
        grouped[r["mode"]].append(r)
    return grouped


def carriers_by_type() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for c in CARRIERS:
        grouped[c["carrier_type"]].append(c)
    return grouped


def pick_order_date(rng: random.Random) -> date:
    span = (PERIOD_END - PERIOD_START).days
    # Leichtes Wachstum 2026 vs 2025
    u = rng.random() ** 0.92
    return PERIOD_START + timedelta(days=int(u * span))


def generate_shipments(rng: random.Random) -> list[dict]:
    mats_group = materials_by_group()
    routes_mode = routes_by_mode()
    carriers_type = carriers_by_type()
    cust_w = customer_weights()

    rows: list[dict] = []
    for i in range(1, N_SHIPMENTS + 1):
        customer = weighted_choice(CUSTOMERS, cust_w, rng)
        segment = customer["customer_segment"]

        if rng.random() < 0.10:
            other_groups = [g for g in mats_group if g != segment]
            mat_group = rng.choice(other_groups)
        else:
            mat_group = segment
        material = rng.choice(mats_group[mat_group])

        mode = weighted_choice(
            list(SEGMENT_MODE_WEIGHTS[segment]),
            list(SEGMENT_MODE_WEIGHTS[segment].values()),
            rng,
        )
        route = rng.choice(routes_mode[mode])
        carrier_type = MODE_TO_CARRIER_TYPE[mode]
        carrier_pool = carriers_type[carrier_type]
        # Zuverlaessigere Carrier etwas haeufiger gebucht
        c_weights = [max(0.15, c["reliability_score"] - 0.75) for c in carrier_pool]
        carrier = weighted_choice(carrier_pool, c_weights, rng)

        order_date = pick_order_date(rng)
        planned = skip_sunday(order_date + timedelta(days=transit_days(mode, route["distance_km"], rng)))
        international = not (
            route["origin_location"].endswith("(DE)")
            and route["destination_location"].endswith("(DE)")
        )

        qty = quantity_for(material, rng)
        weight_kg = round(qty * float(material["weight_kg_per_unit"]), 2)

        cancelled = rng.random() < 0.028
        late_prob = delay_probability(
            carrier["reliability_score"], mode, order_date, international
        )
        is_late = (not cancelled) and rng.random() < late_prob

        actual: date | None = None
        status: str
        delay_reason: str = ""

        if cancelled:
            status = "Cancelled"
        elif is_late:
            reason = pick_delay_reason(order_date, mode, international, rng)
            actual_candidate = planned + timedelta(days=delay_days(mode, reason, rng))
            if actual_candidate > SNAPSHOT:
                status = "Delayed"
                delay_reason = reason
                actual = None
            elif planned > SNAPSHOT:
                status = "In Transit"
                actual = None
            else:
                actual = actual_candidate
                delay_reason = reason
                status = "Delayed" if (actual - planned).days >= 3 else "Delivered"
        else:
            early = rng.random() < 0.12
            actual_candidate = planned - timedelta(days=1) if early and planned > order_date else planned
            if actual_candidate < order_date:
                actual_candidate = planned
            if actual_candidate > SNAPSHOT:
                status = "In Transit"
                actual = None
            else:
                status = "Delivered"
                actual = actual_candidate

        rows.append(
            {
                "shipment_id": f"SHP-{i:06d}",
                "order_date": order_date.isoformat(),
                "planned_delivery_date": planned.isoformat(),
                "actual_delivery_date": actual.isoformat() if actual else "",
                "customer_id": customer["customer_id"],
                "material_id": material["material_id"],
                "carrier_id": carrier["carrier_id"],
                "route_id": route["route_id"],
                "quantity": qty,
                "weight_kg": fmt_weight(weight_kg),
                "status": status,
                "delay_reason": delay_reason,
            }
        )
    return rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict], float_fields: dict[str, callable] | None = None) -> None:
    float_fields = float_fields or {}
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            out = dict(row)
            for key, fn in float_fields.items():
                out[key] = fn(out[key])
            writer.writerow(out)


def parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def validate(shipments: list[dict]) -> None:
    cust_ids = {c["customer_id"] for c in CUSTOMERS}
    mat_ids = {m["material_id"] for m in MATERIALS}
    car_ids = {c["carrier_id"] for c in CARRIERS}
    rte_ids = {r["route_id"] for r in ROUTES}
    mat_by_id = {m["material_id"]: m for m in MATERIALS}

    assert len(CUSTOMERS) == 50, len(CUSTOMERS)
    assert len(MATERIALS) == 80, len(MATERIALS)
    assert len(CARRIERS) == 15, len(CARRIERS)
    assert len(ROUTES) == 40, len(ROUTES)
    assert len(shipments) == N_SHIPMENTS

    late = 0
    for s in shipments:
        assert s["customer_id"] in cust_ids, s["customer_id"]
        assert s["material_id"] in mat_ids, s["material_id"]
        assert s["carrier_id"] in car_ids, s["carrier_id"]
        assert s["route_id"] in rte_ids, s["route_id"]
        assert s["status"] in VALID_STATUS, s["status"]
        assert s["delay_reason"] in DELAY_REASONS or s["delay_reason"] == ""
        order_d = parse_date(s["order_date"])
        planned_d = parse_date(s["planned_delivery_date"])
        actual_d = parse_date(s["actual_delivery_date"])
        assert order_d is not None and PERIOD_START <= order_d <= PERIOD_END
        assert planned_d is not None and planned_d >= order_d
        expected_w = round(int(s["quantity"]) * float(mat_by_id[s["material_id"]]["weight_kg_per_unit"]), 2)
        assert abs(float(s["weight_kg"]) - expected_w) < 0.011, s["shipment_id"]
        if actual_d is not None and actual_d > planned_d:
            late += 1
        if s["status"] == "Cancelled":
            assert s["actual_delivery_date"] == ""
            assert s["delay_reason"] == ""
        if s["status"] == "In Transit":
            assert s["actual_delivery_date"] == ""

    share = late / N_SHIPMENTS
    assert 0.15 <= share <= 0.20, f"Late share {share:.3%} not in 15-20%"


def print_summary(shipments: list[dict]) -> None:
    late = 0
    late_by_carrier: Counter[str] = Counter()
    total_by_carrier: Counter[str] = Counter()
    late_by_route: Counter[str] = Counter()
    total_by_route: Counter[str] = Counter()
    status_c = Counter(s["status"] for s in shipments)
    reason_c = Counter(s["delay_reason"] or "(leer)" for s in shipments)

    for s in shipments:
        planned_d = parse_date(s["planned_delivery_date"])
        actual_d = parse_date(s["actual_delivery_date"])
        total_by_carrier[s["carrier_id"]] += 1
        total_by_route[s["route_id"]] += 1
        if actual_d is not None and planned_d is not None and actual_d > planned_d:
            late += 1
            late_by_carrier[s["carrier_id"]] += 1
            late_by_route[s["route_id"]] += 1

    print(f"Zeilen: customers={len(CUSTOMERS)} materials={len(MATERIALS)} "
          f"carriers={len(CARRIERS)} routes={len(ROUTES)} shipments={len(shipments)}")
    print(f"actual > planned: {late} ({late / N_SHIPMENTS:.1%})")
    print("Status:", dict(status_c))
    print("delay_reason:", dict(reason_c))
    print("Verspaetungsquote je Carrier:")
    car_name = {c["carrier_id"]: c["carrier_name"] for c in CARRIERS}
    for cid, n in sorted(total_by_carrier.items()):
        q = late_by_carrier[cid] / n
        print(f"  {cid} {car_name[cid]:32s} {q:5.1%}  ({late_by_carrier[cid]}/{n})")
    print("Top-5 Routen nach Verspaetungsquote (min. 20 Sendungen):")
    rte_name = {r["route_id"]: f"{r['origin_location']} -> {r['destination_location']}" for r in ROUTES}
    ranked = []
    for rid, n in total_by_route.items():
        if n >= 20:
            ranked.append((late_by_route[rid] / n, rid, n))
    for q, rid, n in sorted(ranked, reverse=True)[:5]:
        print(f"  {rid} {rte_name[rid]:40s} {q:5.1%}  ({late_by_route[rid]}/{n})")


def main() -> None:
    rng = random.Random(SEED)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    shipments = generate_shipments(rng)
    validate(shipments)

    write_csv(
        RAW_DIR / "customers.csv",
        ["customer_id", "customer_name", "country", "region", "customer_segment"],
        CUSTOMERS,
    )
    write_csv(
        RAW_DIR / "materials.csv",
        ["material_id", "material_name", "material_group", "weight_kg_per_unit"],
        MATERIALS,
        float_fields={"weight_kg_per_unit": fmt_weight},
    )
    write_csv(
        RAW_DIR / "carriers.csv",
        ["carrier_id", "carrier_name", "carrier_type", "reliability_score"],
        CARRIERS,
        float_fields={"reliability_score": fmt_score},
    )
    write_csv(
        RAW_DIR / "routes.csv",
        ["route_id", "origin_location", "destination_location", "distance_km", "mode"],
        ROUTES,
    )
    write_csv(
        RAW_DIR / "shipments.csv",
        [
            "shipment_id",
            "order_date",
            "planned_delivery_date",
            "actual_delivery_date",
            "customer_id",
            "material_id",
            "carrier_id",
            "route_id",
            "quantity",
            "weight_kg",
            "status",
            "delay_reason",
        ],
        shipments,
    )
    print_summary(shipments)
    print(f"geschrieben nach {RAW_DIR}")


if __name__ == "__main__":
    main()
