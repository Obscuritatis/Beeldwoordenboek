# Beeldwoordenboek

Foto's en pictogrammen met het Nederlandse woord eronder en de uitspraak met één tik.
Bedoeld voor anderstalige collega's, op de smartphone.

- `index.html`, `sw.js`, `manifest.webmanifest`, `icons/`: de app (werkt offline, te installeren op het startscherm).
- `woorden.json` en `media/`: de eigen woorden, foto's en opnames.
- `bron/artifact-bron.html`: de broncode van de app.
- `tools/build_site.py`: bouwt `index.html`, `sw.js` en het manifest uit de bron.
- `tools/sync_from_artifact.py`: zet woorden uit de beheer-app om naar `woorden.json` en `media/`.
