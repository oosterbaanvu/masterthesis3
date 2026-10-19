# Verslag 4 - Value pilot fase 0: financiële datasets en bankcasus

| | |
|---|---|
| Datum | 19 oktober 2026 |
| Branch | `claude/value-pilot-phase0` (commits 834d972 en ea1a8d8) |
| Hoort bij | het *nieuwe* voorstel (*MSc_Thesis_Proposal_Banking_Data_Quality_2026*) en de *Value & Feasibility Pilot brief*, fase 0 |
| Volledig rapport | [`reports/value_pilot/00_data_and_use_case.md`](../reports/value_pilot/00_data_and_use_case.md) (Engels, 14 secties), datasetmatrix [`reports/value_pilot/dataset_matrix.csv`](../reports/value_pilot/dataset_matrix.csv), uitkomsten in `results/value_pilot/` |
| Status | **Actueel. Wacht op jouw review.** Er is geen detector gedraaid. Brief-fase 1 is niet gestart. |

## Onderzoeksvraag

Welke publieke financiële datasets zijn geschikt voor de nieuwe onderzoeksrichting (onboarding van een nieuwe financiële databron)? Is AuditBench bruikbaar als onafhankelijke benchmark? En is er naast goede dbt-checks ruimte voor een artefact dat echt waarde toevoegt?

## Conclusies

1. **UCI Credit is geschikt als hoofddataset, maar niet aantoonbaar schoon.**
   - De gedocumenteerde codecontroles keuren al 66,9% van de betaalstatus-cellen af.
   - 1,2% van de rijen heeft een niet-gedocumenteerde opleidingscode.
   - Een engineer moet die checks dus versoepelen, en dan komen ook geldige maar foute codes erdoorheen.
   - Er is geen tijdsas tussen rijen, dus alleen willekeurige testsets zijn mogelijk.
2. **BAF Base (Feedzai) is voorwaardelijk geschikt als tweede financiële casus.**
   - Het is de enige kandidaat met echte maandbatches (maand 0-7), zodat je "een nieuwe batch onboarden" kunt nabootsen met maand 6-7.
   - Er zijn drie voorwaarden: (a) de data staat alleen op Kaggle, en Kaggle is hier geblokkeerd, dus jij moet de bestanden downloaden; (b) de licentie (CC BY-NC-ND 4.0) moet worden bevestigd; (c) de fraudelabel van BAF is **geen** datakwaliteitslabel en wordt daarom niet als fout-label gebruikt.
3. **AuditBench is afgewezen als benchmark.**
   - Slechts 166 van 1.484 records (11,2%) geven een exact label met tabel, rij, kolom, foute waarde, juiste waarde en fouttype. In het bestand met meerdere fouten zijn dat er 0 van 372.
   - 75% van de "fouten" zijn ontbrekende, toegevoegde of verplaatste regels, geen celfouten.
   - 50 foutieve tabellen bevatten commentaar van de generator, zoals "// Numerical error introduced here".
   - Elke tabel is één jaarrekening van één bedrijf, met 1.805 verschillende regelnamen. Dat past niet bij detectoren die over veel records met dezelfde kolommen leren.
   - De repository heeft geen licentie.
4. **TableEG blijft alleen bruikbaar voor herkomstanalyse.** Dit volgt uit verslag 3: de labels zijn ingevulde schattingen en originele antwoorden, geen echte fouten. TableEG Marketing is niet UCI Bank Marketing.
5. **Een extra financiële dataset is nu niet nodig.** UCI Bank Marketing is de reserve. Het belangrijkste negatieve resultaat: **geen enkele publieke dataset bevat echte, op celniveau gelabelde fouten in financiële data.** Een extra dataset lost dat niet op. De thesis moet dit als beperking vermelden.
6. **Goede dbt-checks vangen veel, maar niet alles.**
   - Een check "saldo ≤ 1,5 × kredietlimiet" vangt 62-65% van de ×10-fouten op rekeningbedragen. Een simpele bereikcheck vangt er 7-19%.
   - Het CDC-voordeel uit verslag 1 is dus gemeten tegen een te zwakke baseline.
   - Bij betalingsbedragen valt een ×10-fout maar in 0,3-2,2% van de gevallen op. Ook geldige maar foute codes en verschoven maanden komen ongezien door. Daar is ruimte voor aanvullende detectie.
7. **Een artefact kan waarde toevoegen, maar smaller dan voorgesteld.** dbt, Great Expectations en Deequ bieden geen manier om systematisch te testen *welke plausibele fouten je huidige checks niet zien*. Ze geven ook geen onderbouwd advies "voeg wel of geen detector toe".

## Advies: MODIFY

| | |
|---|---|
| Waarom niet GO | (1) AuditBench valt af, en er is geen publieke vervanger met echte gelabelde financiële fouten. (2) In verslag 1 maakte mechanisme-bewuste selectie geen verschil. (3) Het CDC-voordeel moet opnieuw worden gemeten tegen een sterke dbt-baseline. |
| Waarom niet PIVOT | (1) Er blijft meetbare ruimte boven sterke checks (betalingen, geldige maar foute codes, waarden binnen het bereik). (2) Er zijn twee bruikbare financiële casussen. (3) Een stresstest met de mogelijkheid tot "geen advies" bestaat nog niet in de gangbare tools. |
| Aanpassing | **Hoofdbijdrage:** een reproduceerbare stresstest van de dbt-checks van een engineer, plus meting van de *extra* waarde van detectoren. Het advies mag "geen extra detector" of "onvoldoende bewijs" zijn. **Nevenhypothese:** mechanisme-bewuste selectie, getoetst en niet aangenomen. |
| Go/no-go | **GO** voor brief-fase 1 op UCI Credit. **Voorwaardelijke GO** voor BAF. **NO-GO** voor een onafhankelijke financiële benchmark met echte celfouten, omdat die niet bestaat. |

## Datasets in één oogopslag

| Dataset | Besluit |
|---|---|
| UCI Credit | geaccepteerd (hoofddataset) |
| BAF Base | voorwaardelijk geaccepteerd (tweede casus, maandbatches) |
| BAF-varianten I-V | afgewezen (bedoeld voor fairness-tests; de kenmerken zijn bewust vervormd) |
| AuditBench | afgewezen als benchmark |
| TableEG Credit / Marketing | alleen herkomstanalyse / afgewezen |
| UCI Bank Marketing | uitgesteld (reserve) |
| Raha Flights | optioneel, alleen als niet-financiële softwarecontrole |

## De bankcasus in het kort

Een data-engineeringteam onboardt een nieuwe maandelijkse creditcardfeed (UCI-schema) of een batch rekeningaanvragen (BAF-schema). Zonder AI zijn er al:
- schemacontroles;
- dbt-tests (not_null, unique, accepted_values);
- bedrijfsregels (limieten, saldo-aansluiting);
- statistische drift-checks;
- aansluiting op controletotalen.

Wat daar plausibel doorheen glipt:
- foute bedragen binnen het normale bereik;
- gedeeltelijke eenheidsfouten;
- geldige maar verkeerde codes;
- -1 dat stilletjes 0 wordt;
- kolommen die een maand verschoven zijn;
- fouten die zich in één klantsegment concentreren.

Tien vragen om dit met mensen uit de praktijk te toetsen staan in sectie 8.3 van het volledige rapport. Ze zijn nog niet gesteld.

## Wat jij moet doen

**A. BAF downloaden** (verplicht voor de tweede casus)
1. Ga naar de officiële Kaggle-pagina `sgpjesus/bank-account-fraud-dataset-neurips-2022`, ingelogd met je eigen account. Gebruik geen kopieën van andere sites.
2. Download minimaal **Base**, ongewijzigd (CSV of Parquet).
3. Noteer:
   - het Kaggle-versienummer;
   - de licentietekst zoals die op de pagina staat;
   - de downloaddatum;
   - bestandsnamen en groottes;
   - de SHA-256 per bestand.
4. Zet de bestanden in `data/manual/baf/` van een lokale clone, of voeg ze toe in een volgende sessie. **Niet committen.** Een automatische intake-check controleert ze daarna.

**B. Licentie laten bevestigen.** CC BY-NC-ND 4.0 betekent niet-commercieel en geen bewerkingen delen. Laat je begeleider of een juridisch contactpersoon bevestigen dat dit past bij een thesis binnen Avanade/Rabobank. Gecorrumpeerde kopieën blijven lokaal. Dit is geen juridisch advies.

**C. Review.** Geef akkoord of commentaar op het MODIFY-advies. Pas daarna start brief-fase 1 (dbt-basislijnen).

## Beperkingen

- Kaggle, de UCI-site en arXiv waren hier niet bereikbaar. Wat daar staat (bijvoorbeeld de licentietekst op Kaggle) is niet zelf gecontroleerd en staat in het rapport als "niet geverifieerd".
- De bankcasus is een gedocumenteerde aanname totdat de vragen aan mensen uit de praktijk zijn beantwoord.
- Het gaat om publieke en synthetische data. Er wordt niets gezegd over echte bankdata of echte foutpercentages.
