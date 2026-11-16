# Stuudiumi kodutööd

Iga päev kell 15:00 (Tallinna aeg) logib GitHub Actions nähtamatu brauseriga
Stuudiumisse sisse, salvestab kodutööde lehed kausta `data/` ja logib välja.
Kell 15:40 loeb Claude'i ajastatud ülesanne need läbi, kirjutab lahenduskäigud
ja saadab teavituse Claude'i äppi.

## Seadistus (üks kord)

1. Hoia see repositoorium **privaatsena**.
2. Settings → Secrets and variables → Actions → New repository secret:
   - `STUUDIUM_URL` – sinu kooli Stuudiumi aadress, nt `https://minukool.ope.ee`
   - `STUUDIUM_USER` – Stuudiumi kasutajanimi / e-post
   - `STUUDIUM_PASS` – Stuudiumi parool
3. Actions → "Stuudiumi kodutööd" → Run workflow, et esimest korda proovida.

Kui midagi läheb valesti, on `data/status.json` failis veateade ja `data/viga.png`
näitab, kus brauser kinni jäi.
