import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Climat des wilayas algériennes", page_icon="🌦️", layout="wide")

# ---------- Données ----------
@st.cache_data
def charger():
    chemin = Path(__file__).parent / "data" / "clean" / "meteo_clean.csv"
    return pd.read_csv(chemin, parse_dates=["date"])

df = charger()
MOIS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

# Une couleur fixe par wilaya, identique sur tous les graphiques
wilayas_all = sorted(df["wilaya"].unique())
palette = px.colors.qualitative.Dark24
COULEURS = {w: palette[i % len(palette)] for i, w in enumerate(wilayas_all)}

# ---------- Filtres (barre latérale) ----------
st.sidebar.header("Filtres")
regions = st.sidebar.multiselect("Région", sorted(df["region"].unique()),
                                 default=sorted(df["region"].unique()))
dispo = sorted(df[df["region"].isin(regions)]["wilaya"].unique())
wilayas = st.sidebar.multiselect("Wilaya(s)", dispo, default=dispo)
annee_min, annee_max = st.sidebar.slider("Période", 2005, 2020, (2005, 2020))
activite = st.sidebar.radio("Activité", ["Randonnée", "Plage"])

d = df[(df["wilaya"].isin(wilayas)) & (df["annee"].between(annee_min, annee_max))]

st.title("🌦️ Quelle wilaya est la plus exposée aux phénomènes climatiques extrêmes ?")
st.caption("Chaleur, pluie et vent, 12 wilayas, 2005-2020 | Aide à la décision pour guides de randonnée et organisateurs de sorties plage")

if d.empty:
    st.warning("Aucune donnée : sélectionnez au moins une wilaya.")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["Vue d'ensemble", "Comparaison des wilayas", "Saisonnalité", "Quand partir ?"])

# ================= PAGE 1 =================
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temp. moyenne", f"{d['temp_moy'].mean():.1f} °C")
    c2.metric("Canicule (>35 °C)", f"{d['canicule'].sum():,}".replace(",", " ") + " j")
    c3.metric("Forte pluie (>20 mm)", f"{d['forte_pluie'].sum():,}".replace(",", " ") + " j")
    c4.metric("Vent fort (>40 km/h)", f"{d['vent_fort'].sum():,}".replace(",", " ") + " j")

    annuel = d.groupby(["wilaya", "annee"], as_index=False)["temp_moy"].mean()
    fig = px.line(annuel, x="annee", y="temp_moy", color="wilaya", markers=True,
                  color_discrete_map=COULEURS,
                  title="Température moyenne annuelle par wilaya",
                  labels={"annee": "Année", "temp_moy": "Température moyenne (°C)", "wilaya": "Wilaya"})
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True)

    # Tendance : pente de la droite de régression (°C par décennie)
    lignes = []
    for w, g in annuel.groupby("wilaya"):
        if len(g) >= 3:
            pente = np.polyfit(g["annee"], g["temp_moy"], 1)[0] * 10
            lignes.append({"wilaya": w, "tendance": round(pente, 2)})
    if lignes:
        tend = pd.DataFrame(lignes).sort_values("tendance", ascending=False)
        fig = px.bar(tend, x="wilaya", y="tendance", color="wilaya", color_discrete_map=COULEURS,
                     title="Tendance de la température (°C par décennie)",
                     labels={"tendance": "°C / décennie", "wilaya": ""})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Une valeur positive indique un réchauffement sur la période sélectionnée. "
                   "Sur 15 ans, la tendance reste indicative.")

# ================= PAGE 2 =================
with tab2:
    nb_ans = annee_max - annee_min + 1
    comp = d.groupby("wilaya").agg(
        canicule=("canicule", "sum"), forte_pluie=("forte_pluie", "sum"),
        vent_fort=("vent_fort", "sum"), temp_moy=("temp_moy", "mean"),
        pluie_moy=("pluie_mm", "mean"), vent_moy=("vent_kmh", "mean"),
        score=("jour_extreme", "mean")).reset_index()
    comp["score"] = comp["score"] * 100
    for col in ["canicule", "forte_pluie", "vent_fort"]:
        comp[col + "_an"] = comp[col] / nb_ans

    # Score d'exposition (réponse à la question centrale)
    comp = comp.sort_values("score", ascending=False)
    fig = px.bar(comp, x="wilaya", y="score", color="wilaya", color_discrete_map=COULEURS,
                 title="Score d'exposition : % de jours extrêmes (canicule, forte pluie ou vent fort)",
                 labels={"score": "% de jours extrêmes", "wilaya": ""})
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"Wilaya la plus exposée : **{comp.iloc[0]['wilaya']}** ({comp.iloc[0]['score']:.1f} % de jours extrêmes). "
               f"La moins exposée : **{comp.iloc[-1]['wilaya']}** ({comp.iloc[-1]['score']:.1f} %).")

    long = comp.melt(id_vars="wilaya", value_vars=["canicule_an", "forte_pluie_an", "vent_fort_an"],
                     var_name="phénomène", value_name="jours_par_an")
    long["phénomène"] = long["phénomène"].map({"canicule_an": "Canicule", "forte_pluie_an": "Forte pluie",
                                               "vent_fort_an": "Vent fort"})
    fig = px.bar(long, x="wilaya", y="jours_par_an", color="phénomène", barmode="group",
                 title="Nombre moyen de jours extrêmes par an",
                 labels={"jours_par_an": "Jours / an", "wilaya": ""})
    st.plotly_chart(fig, use_container_width=True)

    g1, g2, g3 = st.columns(3)
    g1.markdown("**🔥 Les plus chaudes**")
    g1.dataframe(comp.nlargest(3, "temp_moy")[["wilaya", "temp_moy"]].round(1),
                 hide_index=True, use_container_width=True)
    g2.markdown("**🌧️ Les plus pluvieuses**")
    g2.dataframe(comp.nlargest(3, "pluie_moy")[["wilaya", "pluie_moy"]].round(2),
                 hide_index=True, use_container_width=True)
    g3.markdown("**💨 Les plus venteuses**")
    g3.dataframe(comp.nlargest(3, "vent_moy")[["wilaya", "vent_moy"]].round(1),
                 hide_index=True, use_container_width=True)

# ================= PAGE 3 =================
with tab3:
    mensuel_t = d.groupby(["wilaya", "mois"], as_index=False)["temp_moy"].mean()
    fig = px.line(mensuel_t, x="mois", y="temp_moy", color="wilaya", markers=True,
                  color_discrete_map=COULEURS, title="Température moyenne par mois",
                  labels={"mois": "Mois", "temp_moy": "°C", "wilaya": "Wilaya"})
    fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MOIS)
    st.plotly_chart(fig, use_container_width=True)

    pluie = (d.groupby(["wilaya", "annee", "mois"])["pluie_mm"].sum()
              .groupby(["wilaya", "mois"]).mean().reset_index())
    fig = px.bar(pluie, x="mois", y="pluie_mm", color="wilaya", barmode="group",
                 color_discrete_map=COULEURS, title="Précipitations moyennes par mois (mm)",
                 labels={"mois": "Mois", "pluie_mm": "mm", "wilaya": "Wilaya"})
    fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MOIS)
    st.plotly_chart(fig, use_container_width=True)

    heat = mensuel_t.pivot(index="wilaya", columns="mois", values="temp_moy")
    heat.columns = MOIS
    fig = px.imshow(heat, color_continuous_scale="RdYlBu_r", aspect="auto", text_auto=".0f",
                    title="Carte de chaleur : température moyenne (°C) par wilaya et par mois")
    st.plotly_chart(fig, use_container_width=True)

# ================= PAGE 4 =================
with tab4:
    if activite == "Plage":
        col = "ideal_plage"
        dd = d[d["region"] == "Côte"]   # option A : plage = wilayas côtières uniquement
        st.info("Pour la plage, seules les wilayas côtières sont analysées. "
                "Critères d'une journée idéale : 25 à 33 °C, pas de pluie, vent < 25 km/h.")
    else:
        col = "ideal_rando"
        dd = d
        st.info("Critères d'une journée idéale de randonnée : 15 à 28 °C, pas de pluie, vent < 30 km/h.")

    if dd.empty:
        st.warning("Aucune wilaya côtière sélectionnée : ajoutez la région « Côte » dans les filtres.")
    else:
        pct = (dd.groupby(["wilaya", "mois"])[col].mean() * 100).reset_index()
        heat = pct.pivot(index="wilaya", columns="mois", values=col)
        heat.columns = [MOIS[m - 1] for m in heat.columns]
        fig = px.imshow(heat, color_continuous_scale="Greens", aspect="auto", text_auto=".0f",
                        title=f"% de jours idéaux ({activite.lower()}) par mois et par wilaya",
                        labels={"color": "% de jours"})
        st.plotly_chart(fig, use_container_width=True)

        lignes = []
        for w, g in pct.groupby("wilaya"):
            top = g.nlargest(3, col)
            lignes.append({"Wilaya": w,
                           "Meilleurs mois": " > ".join(f"{MOIS[m - 1]} ({v:.0f} %)"
                                                         for m, v in zip(top["mois"], top[col]))})
        st.subheader("Top 3 des meilleurs mois par wilaya")
        st.dataframe(pd.DataFrame(lignes), hide_index=True, use_container_width=True)

st.divider()
st.caption("Source : Open-Meteo Historical API (données de réanalyse modélisées, pas des stations) | 2005-2020")