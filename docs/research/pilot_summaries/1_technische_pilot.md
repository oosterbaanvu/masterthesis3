# Verslag 1 - Technische pilot: mechanisme-bewuste detectorselectie

| | |
|---|---|
| Datum | 18 oktober 2026 |
| Branch | `claude/msc-thesis-feasibility-pilot-ozdfue` |
| Hoort bij | het *oorspronkelijke* voorstel (`docs/Thesis_Proposal.pdf`) |
| Volledig rapport | [`results/pilot/report.md`](../results/pilot/report.md) (HTML: `results/pilot/report.html`), [`docs/pilot_implications.md`](../docs/pilot_implications.md), [`docs/pilot_design.md`](../docs/pilot_design.md) |
| Status | Afgerond. De technische lessen gelden nog. De interpretatie van het CDC-voordeel is in verslag 4 bijgesteld. |

## Onderzoeksvraag

Kun je een detector die is gekozen op fouten van het ene mechanisme (ECAR) vertrouwen als de fouten volgens een ander mechanisme ontstaan (EAR, ENAR)? En werkt het onderzoeksprotocol technisch van begin tot eind?

## Conclusies

1. **Het protocol werkt technisch.** Foutinjectie met tab_err, de detectoren en de vergelijking van twee selectiestrategieën draaien volledig en reproduceerbaar op een gewone CPU. Er waren 96 gecorrumpeerde tabellen en 960 detectorruns. Een tweede run gaf exact dezelfde resultaten.
2. **Eén detector won overal.** Conformal Data Cleaning (CDC) had in beide scenario's en onder alle drie de mechanismen de hoogste F1.
3. **Daardoor maakte selectie geen verschil.** ECAR-only selectie en mechanisme-bewuste selectie kozen in 15 van 18 situaties dezelfde detector. De maximale *regret* was 0,013 F1. **De onderzoeksvraag is met deze pilot dus niet beantwoord**, in geen van beide richtingen.
4. **Mechanismen veranderen wel de rangorde onder de winnaar.** Onder ENAR stortten de regelbaseline en LUCARIO in. Met kandidaten die meer op elkaar lijken kan dat de keuze wel veranderen.
5. **CDC geeft veel valse meldingen op kolommen die niet gecorrumpeerd zijn.** Op schone data markeerde CDC 261 van 1.200 AGE-cellen en 202 van 1.200 LIMIT_BAL-cellen. Over de hele tabel gemeten won daardoor de eenvoudige regelbaseline in scenario 1.
6. **De spreiding is groot.** Opnieuw trainen van CDC met een andere seed veranderde de F1 met maximaal 0,13. Dat is net zo groot als sommige verschillen tussen detectoren, dus de thesis heeft meer seeds en betrouwbaarheidsintervallen nodig.

## Wat is er gedaan

- **Data:** de publieke UCI-tabel *Default of Credit Card Clients* (Taiwan, 2005). Er is een steekproef van 6.000 records genomen, verdeeld in referentie 3.600 / selectie 1.200 / test 1.200.
- **Fouten (gesimuleerd met tab_err):**
  - S1: BILL_AMT1 × 10;
  - S2: verwisseling van de PAY_0-code.
  Beide met 5% en 10% fouten, onder ECAR, EAR en ENAR, met steeds exact hetzelfde aantal fouten per mechanisme.
- **Detectoren:**
  - regelbaseline (Tukey-grenzen, toegestane codes);
  - CDC zoals CURED die gebruikt;
  - de AISTATS-versie van CDC (AutoGluon) als extra kandidaat;
  - LUCARIO.
- **Selectie:** strategie A koos op ECAR-fouten, strategie B op alle drie de mechanismen, met hetzelfde budget. De testdata is alleen achteraf gebruikt om de regret te meten.

## Belangrijkste cijfers

| Scenario | CDC (c = 0,99) | Regels (Tukey k = 3) | LUCARIO |
|---|---|---|---|
| S1: rekeningbedrag × 10, test-F1 | 0,78-0,89 | 0,26-0,58 | 0,00 |
| S2: betaalstatuscode verwisseld, test-F1 | 0,66-0,72 | 0,33-0,39 | 0,00-0,48 |

| Selectie | Resultaat |
|---|---|
| Dezelfde keuze door A en B | 15 van 18 situaties |
| Grootste regret (gemiddelde / slechtste mechanisme) | 0,003-0,004 / 0,013 F1 |
| Rangorde onder EAR/ENAR anders dan onder ECAR | 10 van 24 vergelijkingen (winnaar 5 keer gewisseld, telkens tussen CDC-varianten) |

## Wat dit betekent (en wat in verslag 4 is bijgesteld)

- De pilot liet zien dat de *opzet* haalbaar is, niet dat mechanisme-bewuste selectie beter is.
- **Bijstelling uit verslag 4:** de regelbaseline in deze pilot was zwak (alleen Tukey-grenzen). Een engineer zou ook een check "saldo ≤ kredietlimiet" schrijven. Die zou 62-65% van de ×10-fouten op rekeningbedragen al vangen. Het voordeel van CDC in S1 is dus waarschijnlijk overschat en moet opnieuw worden gemeten tegen een sterke set dbt-checks.

## Beperkingen

- Gesimuleerde fouten op één publieke dataset, met weinig seeds.
- De EAR-conditie gebruikte een *synthetisch* veld (`source_system`).
- Geen uitspraak over echte bankdata, echte foutpercentages of productierijpheid.
