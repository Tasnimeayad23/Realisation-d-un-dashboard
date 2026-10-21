import requests
import pandas as pd
from pathlib import Path
import time

# Coordonnées GPS approximatives du chef-lieu de chaque wilaya
WILAYAS = {
    "Adrar":       (1,  27.87,  -0.29),
    "Batna":       (5,  35.56,   6.17),
    "Biskra":      (7,  34.85,   5.73),
    "Alger":       (16, 36.75,   3.06),
    "Djelfa":      (17, 34.67,   3.26),
    "Jijel":       (18, 36.82,   5.77),
    "Setif":       (19, 36.19,   5.41),
    "Skikda":      (21, 36.88,   6.91),
    "Annaba":      (23, 36.90,   7.77),
    "Ouargla":     (30, 31.95,   5.32),
    "Oran":        (31, 35.70,  -0.63),
    "Tamanrasset": (11, 22.79,   5.53),
}

URL = "https://archive-api.open-meteo.com/v1/archive"
DOSSIER = Path("data/raw")
DOSSIER.mkdir(parents=True, exist_ok=True)

MAX_ESSAIS = 5

def telecharger(params):
    """Essaie plusieurs fois avant d'abandonner."""
    for essai in range(1, MAX_ESSAIS + 1):
        try:
            r = requests.get(URL, params=params, timeout=120)
            if r.status_code == 429:
                raise requests.exceptions.RequestException("Trop de requêtes (429)")
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            attente = 20 * essai
            print(f"   ⚠ Essai {essai}/{MAX_ESSAIS} échoué ({type(e).__name__}). "
                  f"Nouvelle tentative dans {attente} s...")
            time.sleep(attente)
    return None

echecs = []

for nom, (code, lat, lon) in WILAYAS.items():
    fichier = DOSSIER / f"{code:02d}_{nom}.csv"

    # On saute les fichiers déjà téléchargés
    if fichier.exists():
        print(f"⏭ {nom} : déjà téléchargé, on passe.")
        continue

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2005-01-01",
        "end_date": "2020-12-31",
        "daily": ",".join([
            "temperature_2m_mean",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "wind_speed_10m_max",
        ]),
        "timezone": "Africa/Algiers",
    }

    print(f"⏳ {nom} : téléchargement...")
    data = telecharger(params)

    if data is None:
        print(f"✘ {nom} : échec après {MAX_ESSAIS} essais.")
        echecs.append(nom)
        continue

    df = pd.DataFrame(data["daily"])
    df.insert(0, "wilaya", nom)
    df.insert(1, "code", code)
    df.to_csv(fichier, index=False)
    print(f"✔ {nom} : {len(df)} jours enregistrés")
    time.sleep(10)  # pause pour respecter les limites de l'API

print("\nTerminé.")
if echecs:
    print("Wilayas à relancer :", ", ".join(echecs))