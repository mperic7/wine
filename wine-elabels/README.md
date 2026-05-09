# 🍷 Wine E-Label Generator

DIY sustav za generiranje e-label stranica i QR kodova za vina, u skladu s EU Uredbom 2021/2117.

## Što je uključeno

```
wine-elabels/
├── data/
│   └── wines.json              # Podatci o vinima (sastojci, analiza, nutritivne vrijednosti)
├── templates/
│   └── elabel.html             # HTML predložak za e-label stranicu
├── site/                       # Generirani output (ovo se deploya)
│   ├── elabel/                 # HTML stranice po vinu (HR + EN)
│   └── qrcodes/                # QR kodovi za tisak (PNG + SVG)
├── generate.py                 # Generator skripta
└── README.md
```

## Brzi početak

### 1. Instaliraj dependencies

```bash
pip install qrcode[pil]
```

### 2. Uredi podatke o vinima

Otvori `data/wines.json` i dodaj/uredi svoja vina. Za svako vino upiši:
- Podatke s laboratorijske analize (alkohol, šećeri, SO2...)
- Nutritivne vrijednosti (ili koristi `--recalc` za automatski izračun)
- Sastojke na HR i EN jeziku
- Alergene

### 3. Generiraj stranice i QR kodove

```bash
# S tvojom domenom
python generate.py --domain opg-peric.hr

# Za lokalno testiranje
python generate.py --test

# S automatskim izračunom nutritivnih vrijednosti iz analize
python generate.py --domain opg-peric.hr --recalc
```

### 4. Lokalni pregled

```bash
cd site
python -m http.server 8000
# Otvori http://localhost:8000/elabel/grasevina-2024.html
```

## Deploy na GitHub Pages

### Prvi put:

```bash
# 1. Kreiraj novi repozitorij na GitHub-u (npr. "wine-elabels")

# 2. Inicijaliziraj git u site/ direktoriju
cd site
git init
git add .
git commit -m "Initial e-label deploy"
git branch -M main
git remote add origin https://github.com/TVOJ-USERNAME/wine-elabels.git
git push -u origin main

# 3. Na GitHub-u: Settings → Pages → Source: "main" branch, root "/"

# 4. Spoji vlastitu domenu:
#    a) U GitHub repo Settings → Pages → Custom domain: opg-peric.hr
#    b) Na domene.hr dodaj DNS zapise:
#       - CNAME zapis: www → TVOJ-USERNAME.github.io
#       - Za root domenu, A zapisi:
#         185.199.108.153
#         185.199.109.153
#         185.199.110.153
#         185.199.111.153
```

### Ažuriranje:

```bash
# 1. Uredi wines.json (dodaj novo vino, promijeni podatke)
# 2. Regeneriraj
python generate.py --domain opg-peric.hr

# 3. Deploy
cd site
git add .
git commit -m "Dodana Frankovka 2024"
git push
```

## Dodavanje novog vina

1. Otvori `data/wines.json`
2. Kopiraj postojeći entry u `wines` array
3. Promijeni `id`, `name`, `vintage`, analizu i nutritivne podatke
4. Pokreni `python generate.py --domain opg-peric.hr`
5. Novi QR kod je u `site/qrcodes/NOVO-VINO-ID.svg`

## Izračun nutritivnih vrijednosti

Skripta može automatski izračunati nutritivne vrijednosti iz laboratorijske analize:

```bash
python generate.py --recalc
```

Formula (EU Uredba 1169/2011):
- Energija iz alkohola: alkohol (g) × 29 kJ / 7 kcal
- Energija iz šećera: šećeri (g) × 17 kJ / 4 kcal
- Energija iz kiselina: kiseline (g) × 13 kJ / 3 kcal

## QR kod za tisak

- **SVG** (preporučeno za tisak) — vektorski, skalabilan bez gubitka kvalitete
- **PNG** — rasterski, visoka rezolucija

Minimalna veličina na etiketi: **13 × 13 mm** s dovoljnom tihom zonom oko koda.

## Dodavanje novih jezika

1. Dodaj prijevode u `LABELS` dict u `generate.py`
2. Dodaj prijevode sastojaka u `wines.json` pod odgovarajući jezični ključ
3. Regeneriraj

## Napomene o usklađenosti

- E-label stranica **ne smije sadržavati marketinški sadržaj**
- **Bez kolačića**, bez trackinga, bez Google Analyticsa
- Stranica mora biti dostupna na jeziku zemlje u kojoj se vino prodaje
- Svaka berba/varijanta je zasebni proizvod = zasebni QR kod
- `<meta name="robots" content="noindex">` sprečava indeksiranje e-label stranica
