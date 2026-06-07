# -*- coding: utf-8 -*-
"""
PROTOTYPE - Page RECAP tan phi (toutes les centrales)
=====================================================
A placer dans le MEME dossier que ton application.py existant.
Lancement :  streamlit run recap_tanphi.py

Ce que ca fait :
  - tu choisis un mois
  - tu cliques sur un bouton
  - l'appli boucle sur toutes les centrales, calcule pour chacune
    le cumul du mois de P-, Q-, Q+, (Q+ - Q-) et la tan phi cumulee
  - elle affiche un tableau RECAP (1 ligne par centrale) avec un statut
    OK / hors bandeau, comme l'onglet RECAP de Mickael.

On reutilise TON code existant : PARCS, authentifier(), recuperer_donnees().
Rien n'est modifie dans application.py.
"""

import streamlit as st
import pandas as pd
from datetime import date
import calendar
import io

# On reprend directement ton appli existante (aucune duplication)
from application import PARCS, authentifier, recuperer_donnees

# =====================================================================
#  BANDEAUX tan phi PAR CENTRALE   ->   A REMPLIR avec la liste de Mickael
# =====================================================================
# Cle = meter_id (en texte), valeur = (min, max) autorise.
# Tout ce qui n'est pas liste ici utilise le bandeau par defaut ci-dessous.
DEFAULT_BAND = (0.0, 0.1)

BANDEAUX = {
    # Exemples / reperes a confirmer avec Mickael :
    # "131629": (0.25, 0.35),   # Chateau Solar VI [injection]
    # "134757": (0.25, 0.35),   # Chateau Solar VI [soutirage]
    # ... ajoute ici les centrales dont le bandeau differe de 0 - 0,1
}


def bande_de(meter_id):
    """Renvoie (min, max) du bandeau tan phi pour ce meter_id."""
    return BANDEAUX.get(str(meter_id), DEFAULT_BAND)


# =====================================================================
#  OUTILS
# =====================================================================
def bornes_du_mois(annee, mois):
    """Premier et dernier jour du mois (dernier jour plafonne a aujourd'hui)."""
    debut = date(annee, mois, 1)
    dernier_jour = calendar.monthrange(annee, mois)[1]
    fin = date(annee, mois, dernier_jour)
    if fin > date.today():
        fin = date.today()
    return debut, fin


def cumul_mois(meter_id, debut, fin, type_p, headers):
    """
    Reutilise recuperer_donnees() (qui rend un df journalier) puis somme
    sur tout le mois pour obtenir le cumul. Renvoie 0.0 si pas de donnees.
    """
    df = recuperer_donnees(meter_id, debut, fin, type_p, headers)
    if df is None or df.empty:
        return 0.0
    cols = [c for c in df.columns if c != "date"]
    if not cols:
        return 0.0
    return float(df[cols[0]].sum())


def calcul_recap(centrales, debut, fin, headers, progress=None, statut=None):
    """
    Pour chaque centrale : cumul P-, Q-, Q+, (Q+ - Q-), tan phi + statut.
    Renvoie un DataFrame pret a afficher.
    """
    lignes = []
    total = len(centrales)

    for i, (nom, meter_id) in enumerate(centrales):
        if statut is not None:
            statut.text(f"Calcul {i+1}/{total} : {nom}")

        p_actif = cumul_mois(meter_id, debut, fin, "power:active", headers)
        q_moins = cumul_mois(meter_id, debut, fin, "power:reactive-", headers)
        q_plus = cumul_mois(meter_id, debut, fin, "power:reactive+", headers)

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

    return pd.DataFrame(lignes)


def colorer_statut(val):
    """Couleur de fond selon le statut."""
    if val == "OK":
        return "background-color: #d4edda; color: #155724"
    if val == "HORS BANDEAU":
        return "background-color: #f8d7da; color: #721c24; font-weight: bold"
    return "background-color: #fff3cd; color: #856404"  # pas de donnees


# =====================================================================
#  PAGE STREAMLIT
# =====================================================================
def page_recap():
    st.title("📋 RECAP tan phi - toutes les centrales")
    st.markdown(
        "Choisis un mois puis clique sur **Générer le RECAP**. "
        "L'appli calcule pour chaque centrale le cumul du mois et sa tan φ."
    )

    # --- Selecteur de mois ---
    mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                 "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    auj = date.today()

    c1, c2 = st.columns(2)
    with c1:
        mois = st.selectbox("Mois", options=list(range(1, 13)),
                            index=auj.month - 1, format_func=lambda m: mois_noms[m - 1])
    with c2:
        annee = st.selectbox("Année", options=list(range(auj.year - 3, auj.year + 1)),
                             index=3)

    # Option utile : les compteurs [conso] ne servent pas au calcul tan phi
    # (la tan phi se calcule au point d'injection/production).
    exclure_conso = st.checkbox("Exclure les compteurs [conso]", value=True)

    # Construit la liste des centrales a traiter
    centrales = sorted(
        [(nom, mid) for mid, nom in PARCS.items()
         if not (exclure_conso and "[conso]" in nom.lower())],
        key=lambda x: x[0]
    )
    st.caption(f"{len(centrales)} centrales seront calculées "
               f"(≈ {len(centrales) * 3} appels API, prévois ~{len(centrales) * 3} s).")

    if st.button("🔎 Générer le RECAP"):
        headers = authentifier()
        if not headers:
            st.stop()

        debut, fin = bornes_du_mois(annee, mois)
        st.info(f"Période : du {debut.strftime('%d/%m/%Y')} au {fin.strftime('%d/%m/%Y')}")

        barre = st.progress(0.0)
        statut = st.empty()

        df = calcul_recap(centrales, debut, fin, headers, progress=barre, statut=statut)
        statut.text("Terminé ✅")

        # Resume en haut
        nb_hors = (df["Statut"] == "HORS BANDEAU").sum()
        nb_ok = (df["Statut"] == "OK").sum()
        nb_vide = (df["Statut"] == "Pas de donnees").sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("✅ OK", nb_ok)
        m2.metric("⚠️ Hors bandeau", nb_hors)
        m3.metric("➖ Sans données", nb_vide)

        # Tableau colore
        styled = df.style.applymap(colorer_statut, subset=["Statut"])
        st.dataframe(styled, use_container_width=True, height=600)

        # Export Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="RECAP")
        st.download_button(
            "💾 Télécharger le RECAP (Excel)",
            data=buffer.getvalue(),
            file_name=f"recap_tanphi_{annee}_{mois:02d}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


if __name__ == "__main__":
    page_recap()
