# Verslag 2 - Datasetacquisitie zonder Google Drive

| | |
|---|---|
| Datum | 18 oktober 2026 |
| Branch | `claude/msc-thesis-feasibility-pilot-ozdfue` (commits e56d697 en 940a3c7) |
| Hoort bij | het *oorspronkelijke* voorstel |
| Volledig rapport | [`docs/dataset_acquisition.md`](../docs/dataset_acquisition.md), uitkomsten in `results/acquisition/` |
| Status | Afgerond. Grotendeels vervangen door verslag 3 (datastudie) en verslag 4 (bankfocus). |

## Onderzoeksvraag

Welke datasets met schone en vervuilde versies en met foutlabels zijn beschikbaar zonder Google Drive? Kan elke dataset technisch door de bestaande pipeline?

## Conclusies

1. **TableEG en CleanML waren hier niet bereikbaar.** TableEG staat op Google Drive en CleanML op Dropbox. Ook de officiële UCI-site, Kaggle en ProPublica waren geblokkeerd. Alles is daarom via GitHub binnengehaald: 47 bestanden uit 10 repositories, elk vastgelegd met commit en SHA-256-controlegetal.
2. **Dezelfde naam betekent niet dezelfde data.** Hospital bestaat in minstens vijf versies. Zo heeft de versie van ZeroED een ander "schoon" bestand, met 781 in plaats van 509 fouten.
3. **De fouten in Hospital zijn kunstmatig.** 508 van de 509 fouten vervangen een letter door "x" (bijvoorbeeld `birmingham` → `birminghxm`).
4. **"Credit" is niet één dataset.** De Credit-tabel van CleanML en TableEG is Kaggle's *Give Me Some Credit*, niet de UCI-tabel uit de pilot.
5. **Zes datasets doorlopen de pipeline:** UCI Credit, Hospital, COMPAS, Beers, Flights en Adult. Van de 182 stappen slaagden er 180. De twee mislukte stappen waren CDC op tabellen met ontbrekende waarden.
6. **Raha Flights is de beste onafhankelijke controle.** De fouten zijn echte tegenstrijdige vertrekijden uit verschillende webbronnen, met gedocumenteerde ground truth. De dataset is wel niet-financieel.

## Wat is er gedaan

- **Toegang:** per bron getest of die bereikbaar is.
- **Vergelijking:** versies met dezelfde naam zijn cel voor cel vergeleken.
- **Integratietest:** per dataset één keer injectie plus alle detectoren draaien, zonder de detectiekwaliteit te meten.
- **Onafhankelijkheid:** de foutlabels zijn alleen toegankelijk voor testrijen, zodat ze niet per ongeluk de selectie beïnvloeden.

## Technische bevindingen die nog gelden

- CDC (de CURED-versie) weigert tabellen met ontbrekende waarden.
- CDC behandelt veel gehele-getalkolommen (leeftijd, aantallen) als categorieën.
- De Typo-fout van tab_err negeerde zijn seed. Dat is in onze code opgelost.
- De kalibratiesets van CDC zijn bij de meeste datasets kleiner dan de 1.000 rijen die CDC zelf adviseert.

## Wat is vervangen

- **De TableEG-vraag** is in verslag 3 beantwoord: jij leverde de TableEG-ZIP's aan, en de labels bleken geen echte fouten.
- **De datasetkeuze** over meerdere domeinen (COMPAS, Adult, Hospital, Beers) is na het nieuwe voorstel vervangen door de bankfocus van verslag 4.
