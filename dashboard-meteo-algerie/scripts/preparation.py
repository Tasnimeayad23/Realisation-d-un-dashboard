import pandas as pd
from pathlib import Path

# ---------- 1. Fusion des 12 fichiers ----------
fichiers = sorted(Path("data/raw").glob("*.csv"))
df = pd.concat([pd.read_csv(f) for f in fichiers], ignore_index=True)

# ---------- 2. Renommer les colonnes (plus simples) ----------
df = df.rename(columns={
    "time": "date",
    "temperature_2m_mean": "temp_moy",
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "precipitation_sum": "pluie_mm",
    "wind_speed_10m_max": "vent_kmh",
})

# ---------- 3. Types et colonnes de date ----------
df["date"] = pd.to_datetime(df["date"])
df["annee"] = df["date"].dt.year
df["mois"] = df["date"].dt.month

noms_mois = {1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai",
             6: "Juin", 7: "Juillet", 8: "Août", 9: "Septembre",
             10: "Octobre", 11: "Novembre", 12: "Décembre"}
df["mois_nom"] = df["mois"].map(noms_mois)

# ---------- 4. Type de région ----------
region = {
    "Alger": "Côte", "Oran": "Côte", "Annaba": "Côte",
    "Skikda": "Côte", "Jijel": "Côte",
    "Setif": "Hauts Plateaux", "Batna": "Hauts Plateaux", "Djelfa": "Hauts Plateaux",
    "Biskra": "Sahara", "Ouargla": "Sahara", "Adrar": "Sahara", "Tamanrasset": "Sahara",
}
df["region"] = df["wilaya"].map(region)

# ---------- 5. Jours extrêmes (0 ou 1) ----------
df["canicule"] = (df["temp_max"] > 35).astype(int)
df["forte_pluie"] = (df["pluie_mm"] > 20).astype(int)
df["vent_fort"] = (df["vent_kmh"] > 40).astype(int)
df["jour_extreme"] = ((df["canicule"] + df["forte_pluie"] + df["vent_fort"]) > 0).astype(int)

# ---------- 6. Jours idéaux (0 ou 1) ----------
df["ideal_plage"] = (
    df["temp_moy"].between(25, 33)
    & (df["pluie_mm"] == 0)
    & (df["vent_kmh"] < 25)
).astype(int)

df["ideal_rando"] = (
    df["temp_moy"].between(15, 28)
    & (df["pluie_mm"] == 0)
    & (df["vent_kmh"] < 30)
).astype(int)

# ---------- 7. Vérifications ----------
print("Doublons :", df.duplicated(subset=["wilaya", "date"]).sum())
print("Valeurs manquantes :", df.isna().sum().sum())
print("Dimensions :", df.shape)

# ---------- 8. Sauvegarde ----------
Path("data/clean").mkdir(parents=True, exist_ok=True)
df.to_csv("data/clean/meteo_clean.csv", index=False)
print("✔ Fichier créé : data/clean/meteo_clean.csv")

# ---------- 9. Aperçu des résultats par wilaya ----------
resume = df.groupby("wilaya").agg(
    temp_moy=("temp_moy", "mean"),
    jours_canicule=("canicule", "sum"),
    jours_forte_pluie=("forte_pluie", "sum"),
    jours_vent_fort=("vent_fort", "sum"),
    jours_ideal_plage=("ideal_plage", "sum"),
    jours_ideal_rando=("ideal_rando", "sum"),
).round(1)
print(resume)