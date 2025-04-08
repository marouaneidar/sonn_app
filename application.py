import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, date
import io

# -------------------------------------------
#           CONFIGURATION API EVELER
# -------------------------------------------
URL = "https://api.eveler.pro/api/client"
TOKEN = "0wGL8vvdflGDjoK1E4KiziGxDDZsgmZ__wyocNTiotY"
SECRET = "NzRC5xmEN8FSY6SXYtqjPk8AqS0sNR3KNV1n7MUpVRg"

# -------------------------------------------
#      IDENTIFIANTS AUTORISÉS (exemple)
# -------------------------------------------
VALID_USERS = {
    "OMSonnedix": "@Sonn96FR!dix", 
    "admin": "1234",          
}

# -------------------------------------------
#         AUTHENTIFICATION À L'API
# -------------------------------------------
def authentifier():
    headers = {"accept": "application/json"}
    try:
        r = requests.post(
            f"{URL}/auth/login",
            params={"token": TOKEN, "secret": SECRET},
            headers=headers
        )
        if r.status_code != 200:
            st.error(f"🚫 Erreur d'authentification (Code HTTP: {r.status_code})")
            return None
        auth_data = r.json()
        api_token = auth_data["data"]["token"]
        headers["Authorization"] = api_token
        return headers
    except Exception as e:
        st.error(f"🚫 Exception lors de l'authentification : {e}")
        return None

# -------------------------------------------
#     FONCTION POUR RÉCUPÉRER LES DONNÉES
# -------------------------------------------
def recuperer_donnees(meter_id, start_date, end_date, type_puissance, headers):
    endpoint = f"{URL}/meter/{meter_id}/data/{type_puissance}/{start_date}/{end_date}"
    try:
        response = requests.get(endpoint, headers=headers)
        if response.status_code != 200:
            st.error(f"⚠️ Erreur ({type_puissance}) - Code HTTP: {response.status_code}")
            return pd.DataFrame([])

        json_data = response.json()
        if "data" not in json_data or "values" not in json_data["data"]:
            st.error(f"⚠️ Réponse invalide pour {type_puissance}")
            return pd.DataFrame([])

        data_values = json_data["data"]["values"]
        if not data_values:
            # Aucun enregistrement
            return pd.DataFrame([])

        df = pd.DataFrame(data_values)
        # Convertit la date (et supprime le fuseau)
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.floor("D")
        # Convertit la puissance en kWh (pas de mesure = 5 minutes)
        df[f"{type_puissance}_kWh"] = df["value"] * (5/60)
        # Agrège par jour
        grouped = df.groupby("date")[f"{type_puissance}_kWh"].sum().reset_index()

        return grouped
    except Exception as e:
        st.error(f"⚠️ Erreur de connexion pour {type_puissance} : {e}")
        return pd.DataFrame([])

# -------------------------------------------
#    FONCTION : PAGE DE LOGIN STREAMLIT
# -------------------------------------------
def login_page():
    st.title("🔒 Accès réservé")
    st.write("Veuillez vous authentifier pour accéder à l’application.")

    username = st.text_input("Nom d’utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        # Vérification des identifiants
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state["authenticated"] = True
            st.rerun()  # Recharge la page pour afficher l'app
        else:
            st.error("Identifiants invalides")

# -------------------------------------------
#  FONCTION : CONTENU PRINCIPAL DE L'APP
# -------------------------------------------
def app_content():
    # TITRE & HEADER
    st.title("🌞 Appli Eveler - Suivi de Production ⚡")
    st.markdown(
        "Bienvenue dans l'interface de suivi des productions solaires 🏭. "
        "Veuillez renseigner les champs ci-dessous pour obtenir vos données."
    )

    # Bouton déconnexion 
    if st.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

    # FORMULAIRE D'ENTRÉE
    with st.form(key="form_recherche"):
        meter_id = st.text_input("🏷️ ID de la centrale", value="")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("📅 Date de début", value=date.today() - timedelta(days=7))
        with col2:
            end_date = st.date_input("📅 Date de fin", value=date.today())

        submit_button = st.form_submit_button("🔎 Rechercher")

    if submit_button:
        # 1) Authentification
        headers = authentifier()
        if not headers:
            st.stop()

        # 2) Récupération des 3 types de données
        active_df = recuperer_donnees(meter_id, start_date, end_date, "power:active", headers)
        qplus_df = recuperer_donnees(meter_id, start_date, end_date, "power:reactive+", headers)
        qminus_df = recuperer_donnees(meter_id, start_date, end_date, "power:reactive-", headers)

        # 3) Fusion
        final_df = (
            active_df
            .merge(qplus_df, on="date", how="outer")
            .merge(qminus_df, on="date", how="outer")
            .fillna(0)
        )
        final_df.columns = [
            "Date",
            "Active (kWh)",
            "Reactive Q+ (kVArh)",
            "Reactive Q- (kVArh)"
        ]

        # 4) Vérification
        if final_df.empty:
            st.warning("😕 Aucune donnée trouvée sur cette période.")
            st.stop()

        # 5) Affichage du tableau
        st.success(f"✅ Résultats pour la centrale : **{meter_id}**")
        # On crée une copie pour l'affichage (dates formatées)
        df_affiche = final_df.copy()
        df_affiche["Date"] = pd.to_datetime(df_affiche["Date"]).dt.strftime("%d/%m/%Y")

        st.dataframe(df_affiche)

        # 6) Calcul et affichage des statistiques
        st.markdown("---")
        st.subheader("📊 Statistiques")

        df_stats = final_df.copy()  # Pour conserver les dates au format datetime
        stats_labels = {
            "Active (kWh)": "Puissance Active (kWh)",
            "Reactive Q+ (kVArh)": "Puissance Réactive Q+ (kVArh)",
            "Reactive Q- (kVArh)": "Puissance Réactive Q- (kVArh)",
        }

        for col, label in stats_labels.items():
            total = df_stats[col].sum()
            moyenne = df_stats[col].mean()
            maximum = df_stats[col].max()

            idx_max = df_stats[col].idxmax()
            date_max = df_stats.loc[idx_max, "Date"].strftime("%d/%m/%Y")

            # Présentation en ligne dans 4 colonnes
            st.markdown(f"#### {label}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total période", f"{total:.2f}")
            c2.metric("Moyenne journalière", f"{moyenne:.2f}")
            c3.metric("Maximum journalier", f"{maximum:.2f}")
            c4.write(f"**Date max**: {date_max}")

        # 7) Téléchargement Excel
                # 7) Téléchargement Excel
        st.markdown("---")
        st.markdown("### 📥 Export des données")
        
        try:
            # Vérification de l'installation de xlsxwriter
            import xlsxwriter
    
            # Création du fichier Excel en mémoire
            buffer_excel = io.BytesIO()
            
            with pd.ExcelWriter(buffer_excel, engine="xlsxwriter") as writer:
                df_affiche.to_excel(
                    writer,
                    index=False,
                    sheet_name="Données",
                    engine="xlsxwriter"
                )
                
            # Configuration du bouton de téléchargement
            st.download_button(
                label="💾 Télécharger le fichier Excel",
                data=buffer_excel.getvalue(),
                file_name=f"centrale_{meter_id}_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Export complet au format XLSX"
            )
            
        except ImportError:
            st.error("""
                ⚠️ Module manquant : 
                L'export Excel nécessite le module 'xlsxwriter'.
                Contactez l'administrateur pour l'installation.
            """)
            
        except Exception as e:
            st.error(f"""
                ⚠️ Erreur d'export : 
                Une erreur est survenue lors de la génération du fichier.
                Détails techniques : {str(e)}
            """)
# -------------------------------------------
#        FONCTION PRINCIPALE STREAMLIT
# -------------------------------------------
def main():
    # Initialiser la clé "authenticated" dans session_state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Si l'utilisateur n'est pas encore authentifié, afficher la page de login
    if not st.session_state["authenticated"]:
        login_page()
    else:
        # Sinon, afficher le contenu principal
        app_content()

# -------------------------------------------
#    LANCEMENT DE L'APP (streamlit run ...)
# -------------------------------------------
if __name__ == "__main__":
    main()
