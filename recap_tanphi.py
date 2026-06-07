# -*- coding: utf-8 -*-
"""
PROTOTYPE v2 - Page RECAP tan phi (toutes les centrales)
========================================================
A placer dans le MEME dossier que ton application.py.
Lancement :  streamlit run recap_tanphi.py

Corrections par rapport a la v1 :
  - fix de l'affichage colore (pandas recent : .map au lieu de .applymap)
  - les erreurs 404 (compteur sans cette donnee) ne bloquent plus et
    n'affichent plus de gros message rouge : on compte juste les manques.
  - on n'utilise plus recuperer_donnees() (qui criait a chaque 404) :
    on fait l'appel ici, en silencieux, avec le MEME calcul d'energie.
"""

import streamlit as st
import pandas as pd
from datetime import date
import calendar
import io
import requests

# On reprend la config et les utilitaires de TON appli
from application import PARCS, authentifier, URL

# =====================================================================
#  BANDEAUX tan phi PAR CENTRALE   ->   A REMPLIR avec la liste de Mickael
# =====================================================================
DEFAULT_BAND = (0.0, 0.1)

BANDEAUX = {
    # Exemples a confirmer avec Mickael :
    # "131629": (0.25, 0.35),   # Chateau Solar VI [injection]
    # "134757": (0.25, 0.35),   # Chateau Solar VI [soutirage]
}


def bande_de(meter_id):
    return BANDEAUX.get(str(meter_id), DEFAULT_BAND)


# =====================================================================
#  RECUPERATION (silencieuse) + calcul d'energie identique a ton appli
# =====================================================================
def cumul_mois(meter_id, debut, fin, type_p, headers):
    """
    Renvoie (cumul_kWh, ok) pour un compteur / un type sur la periode.
    ok = False si 404 ou erreur (on n'affiche pas d'alerte rouge).
    Calcul d'energie identique a recuperer_donnees() : intervalle reel
    entre mesures, plafonne, puis somme.
    """
    endpoint = f"{URL}/meter/{meter_id}/data/{type_p}/{debut}/{fin}"
    try:
        resp = requests.get(endpoint, headers=headers, timeout=30)
        if resp.status_code != 200:
            return 0.0, False  # 404 et autres : silencieux

        json_data = resp.json()
        data_values = json_data.get("data", {}).get("values")
        if not data_values:
            return 0.0, True  # repond OK mais aucune mesure

        df = pd.DataFrame(data_values)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        df = df.sort_values("date")
        df["next_date"] = df["date"].shift(-1)
        df["interval_hours"] = (df["next_date"] - df["date"]).dt.total_seconds() / 3600
        df["interval_hours"] = df["interval_hours"].fillna(0)
        df.loc[df["interval_hours"] > 1, "interval_hours"] = 5 / 60
        df["energy"] = df["value"] * df["interval_hours"]
        return float(df["energy"].sum()), True
    except Exception:
        return 0.0, False


def bornes_du_mois(annee, mois):
    debut = date(annee, mois, 1)
    dernier = calendar.monthrange(annee, mois)[1]
    fin = date(annee, mois, dernier)
    if fin > date.today():
        fin = date.today()
    return debut, fin


def calcul_recap(centrales, debut, fin, headers, progress=None, statut=None):
    lignes = []
    nb_manques = 0
    total = len(centrales)

    for i, (nom, meter_id) in enumerate(centrales):
        if statut is not None:
            statut.text(f"Calcul {i+1}/{total} : {nom}")

        p_actif, ok1 = cumul_mois(meter_id, debut, fin, "power:active", headers)
        q_moins, ok2 = cumul_mois(meter_id, debut, fin, "power:reactive-", headers)
        q_plus, ok3 = cumul_mois(meter_id, debut, fin, "power:reactive+", headers)
        if not (ok1 and ok2 and ok3):
            nb_manques += 1

        diff = q_plus - q_moins
        tan_phi = (diff / p_actif) if p_actif else None

        bmin, bmax = bande_de(meter_id)
        if tan_phi is None:
            etat = "Pas de donnees"
        elif bmin <= tan_phi <= bmax:
            etat = "OK"
        else:
            etat = "HORS BANDEAU"

        lignes.append({
            "Centrale": nom,
            "Meter ID": meter_id,
            "P- (kWh)": round(p_actif, 0),
            "Q- (kVArh)": round(q_moins, 0),
            "Q+ (kVArh)": round(q_plus, 0),
            "Q+ - Q-": round(diff, 0),
            "Tan phi": round(tan_phi, 3) if tan_phi is not None else None,
            "Bandeau": f"{bmin} - {bmax}",
            "Statut": etat,
        })

        if progress is not None:
            progress.progress((i + 1) / total)

    return pd.DataFrame(lignes), nb_manques


def colorer_statut(val):
    if val == "OK":
        return "background-color: #d4edda; color: #155724"
    if val == "HORS BANDEAU":
        return "background-color: #f8d7da; color: #721c24; font-weight: bold"
    return "background-color: #fff3cd; color: #856404"


def appliquer_couleur(df):
    """Compatible pandas recent (.map) ET ancien (.applymap)."""
    styler = df.style
    try:
        return styler.map(colorer_statut, subset=["Statut"])
    except AttributeError:
        return styler.applymap(colorer_statut, subset=["Statut"])


# =====================================================================
#  PAGE STREAMLIT
# =====================================================================
def page_recap():
    st.title("RECAP tan phi - toutes les centrales")
    st.markdown(
        "Choisis un mois puis clique sur **Generer le RECAP**. "
        "L'appli calcule pour chaque centrale le cumul du mois et sa tan phi."
    )

    mois_noms = ["Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"]
    auj = date.today()

    c1, c2 = st.columns(2)
    with c1:
        mois = st.selectbox("Mois", options=list(range(1, 13)),
                            index=auj.month - 1, format_func=lambda m: mois_noms[m - 1])
    with c2:
        annee = st.selectbox("Annee", options=list(range(auj.year - 3, auj.year + 1)),
                             index=3)

    exclure_conso = st.checkbox("Exclure les compteurs [conso]", value=True)

    centrales = sorted(
        [(nom, mid) for mid, nom in PARCS.items()
         if not (exclure_conso and "[conso]" in nom.lower())],
        key=lambda x: x[0]
    )
    st.caption(f"{len(centrales)} centrales seront calculees "
               f"(~ {len(centrales) * 3} appels API).")

    if st.button("Generer le RECAP"):
        headers = authentifier()
        if not headers:
            st.stop()

        debut, fin = bornes_du_mois(annee, mois)
        st.info(f"Periode : du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}")

        barre = st.progress(0.0)
        statut = st.empty()

        df, nb_manques = calcul_recap(centrales, debut, fin, headers,
                                      progress=barre, statut=statut)
        statut.text("Termine")

        nb_hors = int((df["Statut"] == "HORS BANDEAU").sum())
        nb_ok = int((df["Statut"] == "OK").sum())
        nb_vide = int((df["Statut"] == "Pas de donnees").sum())

        m1, m2, m3 = st.columns(3)
        m1.metric("OK", nb_ok)
        m2.metric("Hors bandeau", nb_hors)
        m3.metric("Sans donnees", nb_vide)

        if nb_manques:
            st.caption(f"{nb_manques} centrale(s) sans toutes les donnees "
                       f"(compteur sans reactif, meter_id obsolete...). C'est normal.")

        st.dataframe(appliquer_couleur(df), use_container_width=True, height=600)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="RECAP")
        st.download_button(
            "Telecharger le RECAP (Excel)",
            data=buffer.getvalue(),
            file_name=f"recap_tanphi_{annee}_{mois:02d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    page_recap()

