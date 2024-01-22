Vergunningen API
=========

## Introductie

Deze api levert de volgende data:

- Vergunningen, zie `/app/zaaktypes.py` voor een overzicht van de types.

### Kenmerken
- Het bronsysteem is DecosJoin
- De output van de api is JSON formaat.

### Development & testen
- Er is geen uitgebreide lokale set-up waarbij ontwikkeld kan worden op basis van een "draaiende" api. Dit zou gemaakt / geïmplementeerd moeten worden.
- Alle tests worden dichtbij de geteste functionaliteit opgeslagen. B.v `some_service.py` en wordt getest in `test_some_service.py`.

### CI/CD
- De applicatie wordt verpakt in een Docker container.
- Bouwen en deployen van de applicatie gebeurt in Github en Azure DevOps.

### Release to production
```
~ cd scripts
~ sh release.sh --minor [--major [--patch]]
```