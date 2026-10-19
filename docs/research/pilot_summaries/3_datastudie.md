# Verslag 3 - Datastudie: twaalf datasets gecontroleerd

| | |
|---|---|
| Datum | 19 oktober 2026 |
| Branch | `claude/phase1-data-study` (commits 6a87045 en 68c04af) |
| Hoort bij | het *oorspronkelijke* voorstel. In de repository heet deze stap "Phase 1 data study". Dat is iets anders dan "fase 1" uit de nieuwe brief. |
| Volledig rapport | [`docs/data_study.md`](../docs/data_study.md), visueel rapport [`results/data_study/report.html`](../results/data_study/report.html), herkomst [`docs/dataset_provenance.md`](../docs/dataset_provenance.md) |
| Status | Afgerond. De bevindingen over de data kloppen nog. De voorgestelde keuze van datasets uit meerdere domeinen is vervangen door de bankfocus van verslag 4. |

## Onderzoeksvraag

Zijn de kandidaat-datasets betrouwbaar (herkomst, labels), welke eigenschappen hebben ze, welke fouttypen zijn er zinvol in, en hoe splits je ze zonder lekken tussen trainings- en testdata?

## Conclusies

1. **Twaalf datasets zijn beschikbaar en gecontroleerd.** Het gaat om UCI Credit, Diabetes, COMPAS, Adult, de door jou aangeleverde TableEG Credit en Marketing, en zes Raha-benchmarks. Waar meerdere kopieën bestaan, zijn die identiek.
2. **TableEG Credit bevat geen gegenereerde fouten.** Het "vervuilde" bestand is identiek aan het originele Kaggle-bestand (*Give Me Some Credit*). De 34.938 "fouten" zijn de eigen ontbrekende waarden van die bron (33.655) plus 1.283 uitschieters volgens een niet-gedocumenteerde regel. De "juiste waarden" zijn ingevulde schattingen (imputaties), geen gecontroleerde correcties.
3. **De labels van TableEG Marketing kloppen niet met de bron.** Het "vervuilde" bestand is de originele ESL-enquête uit 1987. De 24.121 "fouten" zijn dus originele antwoorden. Het is ook **niet** de UCI Bank Marketing-dataset.
4. **Beide TableEG-sets zijn daarom ongeschikt als onafhankelijke controle.** Raha Flights is wel geschikt: echte fouten, maar niet-financieel.
5. **Veel voor de hand liggende foutinjecties zijn triviaal.** Een simpele check vangt bijvoorbeeld ×10 op leeftijd of een ontbrekende waarde in een kolom die nooit leeg is. Zinvolle fouten zijn vooral:
   - geldige maar verkeerde categorieën;
   - verkeerde waarden binnen het normale bereik;
   - schaalfouten op scheef verdeelde bedragen. Zo valt ×10 op UCI-betalingen (PAY_AMT) maar bij 0-2% buiten het waargenomen maximum.
6. **Lekrisico's zijn afgedekt.** Patiënten, ziekenhuizen, vluchten en dubbele records blijven bij het splitsen bij elkaar. Geen enkele dataset heeft een groep die in meerdere partities terechtkomt.

## Wat is er gedaan

- **Bestanden:** opgehaald, gecontroleerd op SHA-256 en vastgelegd als alleen-lezen.
- **Inlezen:** waarden zijn letterlijk ingelezen, zonder stille conversies.
- **Analyse per dataset:** profiel, ontbrekende waarden, duplicaten, samenhang tussen kolommen en documentatiecontroles.
- **TableEG:** cel voor cel vergeleken met de originele bronnen (Kaggle GMSC, ESL-enquête in twee R-pakketten).
- **Geschiktheid:** per kolom en fouttype beoordeeld (zinvol, triviaal of niet van toepassing).
- **Splitsing:** referentie 60% / selectie 20% / test 20%, groepsbewust, seed 43.

## Belangrijkste cijfers

| Dataset | Rijen | Samenhang tussen kolommen (mediaan) | Opmerking |
|---|---|---|---|
| UCI Credit | 30.000 | 0,65 | geen ontbrekende waarden; wel niet-gedocumenteerde codes |
| Diabetes | 101.766 | 0,20 | veel ontbrekend; meerdere opnames per patiënt |
| COMPAS | 7.214 | 0,56 | persoonsgegevens: privacycheck nodig |
| Adult | 32.561 | 0,46 | "?" als ontbrekende waarde |
| Raha Flights | 2.376 | 0,94 | echte fouten (29,6%), niet-financieel |
| TableEG Credit | 150.000 | - | labels = eigen ontbrekende waarden en uitschieters |

## Wat is vervangen

- **De voorgestelde datasetkeuze** (UCI Credit, Diabetes, Adult en COMPAS als gecontroleerde datasets, met Flights als onafhankelijke controle) hoorde bij het oude, multi-domein voorstel. Het nieuwe voorstel richt zich op financiële data. Daarom gaat verslag 4 verder met alleen UCI Credit en BAF. De niet-financiële sets zijn niet meer nodig, op Raha Flights na als optionele softwarecontrole.
- **De bevindingen over UCI Credit en TableEG** zijn ongewijzigd overgenomen in verslag 4.
