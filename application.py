import streamlit as st #ok
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
#    MAPPING METER ID -> NOMS DES PARCS
# -------------------------------------------
PARCS = {
    "39659": "Romilly-sur-Seine", 
    "39660": "Lavansol M13 RTE", 
    "40007": "HIS",
    "40008": "HIS [conso]",
    "40009": "Blanquefort",      
    "40010": "Blanquefort [conso]",      
    "40011": "Cabasse",
    "40012": "Cabasse [conso]", 
    "40013": "Castelnau",
    "40014": "Castelnau [conso]", 
    "40015": "Chateau-neuf-val-St-Donat - M1",
    "40016": "Pleurtuit",
    "40017": "Pleurtuit [conso]",
    "40018": "Elecsol Provence",
    "40019": "Elecsol Provence [conso]",
    "40020": "Ginasservis",
    "40021": "Ginasservis [conso]",
    "40022": "Iguaçu",
    "40023": "Iguaçu [conso]",
    "40024": "Istres Auxiliaires",
    "40025": "Istres Auxiliaires [conso]",
    "40026": "Istres SM [conso]",
    "40027": "Istres SM StMartin",
    "40028": "Istres SS",
    "40029": "Istres SS [conso]",
    "40030": "M11",
    "40031": "M11 [conso]",
    "40032": "Lavansol I - M1",
    "40034": "Lavansol M13",
    "40035": "Lavansol M14 [conso]",
    "40037": "Lavansol M14",
    "40038": "Lavansol I - M23",
    "40039": "Lavansol I - M23 [conso]",
    "40040": "Lavansol I - M6 [conso]",
    "40042": "Lavansol I - M6",
    "40043": "Lavansol I - M8 A",
    "40044": "Lavansol I - M8 A [conso]",
    "40045": "Lavansol I - M8 B [conso]",
    "40046": "Lavansol I - M8 B",
    "40047": "Lavansol I - M9",
    "40048": "Lavansol I - M9 [conso]",
    "40049": "Quincieux [conso]",
    "40050": "Quincieux",
    "40051": "Revest-du-Bion",
    "40052": "Revest-du-Bion [conso]",
    "40053": "Romilly-sur-Seine [conso]", 
    "40054": "Solaire Uglas [conso]",
    "40055": "Solaire Uglas",
    "47377": "Lacs médocains Bourg d'Hourtin",
    "47378": "Lacs médocains Gartiou",
    "47379": "Lacs médocains La Redoune",
    "47380": "Lacs médocains Bourg d'Hourtin [conso]",  
    "47381": "Lacs médocains Gartiou [conso]",
    "47383": "Lacs médocains La redoune [conso]",
    "48159": "CORSOLAR",
    "48160": "Lavansol V",
    "48161": "CORSOLAR II",
    "48171": "CORSOLAR [conso]",
    "48172": "Lavansol V",
    "48173": "CORSOLAR II",
    "53179": "Servas",
    "54473": "Servas",
    "54480": "Lanas 1",
    "54481": "Lanas 1 [conso]",
    "54482": "Lanas 2",
    "54483": "Lanas 2 [conso]",
    "54484": "Lanas 3",
    "54485": "Lanas 3 [conso]",
    "54486": "Lanas 4",
    "54487": "Lanas 4 [conso]",
    "54494": "Lanas 5",
    "54495": "Lanas 5 [conso]",
    "54619": "Flins",
    "54620": "Douai",
    "54621": "Douai [conso]",
    "54622": "Flins [conso]",
    "54623": "Sandouville",
    "54624": "Sandouville [conso]",
    "54625": "Maubeuge",
    "54626": "Maubeuge [conso]",
    "54642": "Batilly",
    "54643": "Batilly [conso]",
    "54936": "St Etienne des Sorts - M8",
    "54939": "St Etienne des Sorts - M8 [conso]",
    "113849": "Lavansol M13",
    "113850": "Toul 3.1[conso]C",
    "113865": "Toul 3.2[conso]C",
    "113867": "Toul 3.1",
    "113869": "Toul 3.2",
    "130525": "GenPro325e 01",
    "131346": "GenPro325e 01",
    "131347": "GenPro325e 02",
    "131629": "Château Solar VI",
    "131630": "Lavansol M12 (injection) RTE0000517025",
    "131631": "Lavansol M16 (soutirage) RTE0000517027",
    "134528": "Lavansol V (clône) SC00009881",
    "134529": "Lavansol V [soutirage]  (clône) SC00009881C",
    "134757": "Château Solar VI (pas PRM soutirage)",
    "134850": "Lavansol M12(soutirage)",
    "134851": "Lavansol M16(injection)",
    "136169": "TALLONE",
    "136242": "TIPOS 23-04-2021",
    "136939": "Lavansol III (soutirage)",
    "136960": "Lavansol IV (soutirage)",
    "136962": "Lavansol VI (soutirage)",
    "137761": "Lavansol VI (injection)",
    "137762": "Lavansol IV (injection)",
    "137763": "Lavansol III (injection)",
    "139795": "Sandouville -",
    "139796": "Sandouville ??",
    "139800": "Batilly (copie)",
    "139828": "Batilly [conso 2]",
    "139829": "Douai [conso 2]",
    "139830": "Flins [conso 2]",
    "139831": "Maubeuge [conso 2]",
    "139832": "Sandouville [conso 2]",
    "141333": "Revest-du-Bion (copie)",
    "141334": "Revest-du-Bion [conso]  (copie)",
    "156364": "Barisol",
    "156524": "Barisol (conso)",
    "157010": "Soleol IV (injection)",
    "159084": "Soleol IV (soutirage)",
    "183723": "CORSOLAR II SC00009747 (2)  ?",
    "183745": "CORSOLAR II SC00009747 (injection)",
    "183746": "CORSOLAR II SC00009747 [soutirage]",
    "184855": "TEST espace élec AFA",
    "208011": "LAVANSOL M19 [injection]",
    "208012": "LAVANSOL M19 [soutirage]",
    "208014": "LAVANSOL M21 [injection]",
    "208015": "LAVANSOL M21 [soutirage]",
    "131629": "Château Solar VI [injection]",
    "134757": "Château Solar VI [soutirage]",
    "199360": "Auriac [injection]",
    "202015": "Auriac [soutirage]",
    "209183": "Provensol 1 [injection]",
    "209191": "Provensol 1 [soutirage]",
    "262890": "Conlorbe Est [injection]",
    "262908": "Conlorbe Est [soutirage]",
    "262900": "Cosme [injection]",
    "262909": "Cosme [soutirage]",
    "262901": "Hostens [injection]",
    "262910": "Hostens [soutirage]",
    "262904": "Labraise Nord [injection]",
    "262903": "Labraise Nord [soutirage]",
    "262906": "Las Canes [injection]",
    "262905": "Las Canes [soutirage]",
    "262899": "Lestage [injection]",
    "262912": "Lestage [soutirage]"
    
}

# Création d'une liste de tuples pour le selectbox (tri alphabétique)
LISTE_PARCS = sorted(
    [(nom, meter_id) for meter_id, nom in PARCS.items()], 
    key=lambda x: x[0]
)

# -------------------------------------------
#      IDENTIFIANTS AUTORISÉS (exemple)
# -------------------------------------------
VALID_USERS = {
    "OMSonnedix": "@Sonn96FR!dix", 
    "adminSonnOM": "Ap9888FR!Sonn",          
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
    """
    Récupère les données du compteur et calcule l'énergie (kWh) avec l'intervalle réel entre mesures.
    """
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
            return pd.DataFrame([])

        # Conversion en DataFrame
        df = pd.DataFrame(data_values)
        
        # Conversion des dates en datetime sans timezone
        df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
        
        # Méthode améliorée pour calculer l'énergie
        # 1. Trier par date
        df = df.sort_values("date")
        
        # 2. Calculer l'intervalle entre chaque point de mesure
        df["next_date"] = df["date"].shift(-1)
        df["interval_hours"] = (df["next_date"] - df["date"]).dt.total_seconds() / 3600
        
        # 3. Gérer le dernier point et limiter les intervalles trop grands
        df["interval_hours"] = df["interval_hours"].fillna(0)  # Dernier point
        df.loc[df["interval_hours"] > 1, "interval_hours"] = 5/60  # Max 1 heure, défaut 5 minutes
        
        # 4. Calculer l'énergie (puissance × temps)
        df["energy"] = df["value"] * df["interval_hours"]
        
        # 5. Ajouter une colonne pour le jour (pour regroupement)
        df["jour"] = df["date"].dt.floor("D")
        
        # 6. Somme par jour
        grouped = df.groupby("jour")["energy"].sum().reset_index()
        grouped.columns = ["date", f"{type_puissance}_kWh"]
        
        return grouped
    except Exception as e:
        st.error(f"⚠️ Erreur de connexion pour {type_puissance} : {e}")
        return pd.DataFrame([])

# -------------------------------------------
#    FONCTION : PAGE DE LOGIN STREAMLIT
# -------------------------------------------
def login_page():
    st.title("🔒 Accès réservé")
    st.write("Veuillez vous authentifier pour accéder à l'application.")

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username in VALID_USERS and VALID_USERS[username] == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Identifiants invalides")

# -------------------------------------------
#  FONCTION : CONTENU PRINCIPAL DE L'APP
# -------------------------------------------
def app_content():
    st.title("🌞 Appli Eveler - Suivi de Production ⚡")
    st.markdown(
        "Bienvenue dans l'interface de suivi des productions solaires 🏭. "
        "Veuillez sélectionner un parc dans la liste déroulante."
    )

    if st.button("Se déconnecter"):
        st.session_state["authenticated"] = False
        st.rerun()

    with st.form(key="form_recherche"):
        # Sélection du parc avec menu déroulant
        selected_parc = st.selectbox(
            "🏷️ Sélectionnez le parc",
            options=LISTE_PARCS,
            format_func=lambda x: x[0],
            help="Sélectionnez un parc dans la liste déroulante"
        )
        
        # Récupération des informations   
        nom_parc, meter_id = selected_parc
        st.markdown(f"**Meter ID associé :** `{meter_id}`")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("📅 Date de début", value=date.today() - timedelta(days=7))
        with col2:
            end_date = st.date_input("📅 Date de fin", value=date.today())

        submit_button = st.form_submit_button("🔎 Rechercher")

        st.radio(
            "Mode de calcul",
            ["Puissances instantanées (recommandé)"],  # Une seule option, donc pas de choix
            key="mode_calcul_forcé"       # Clé unique pour remplacer le widget existant
)  
  
    if submit_button:
        headers = authentifier()
        if not headers:
            st.stop()

        active_df = recuperer_donnees(meter_id, start_date, end_date, "power:active", headers)
        qplus_df = recuperer_donnees(meter_id, start_date, end_date, "power:reactive+", headers)
        qminus_df = recuperer_donnees(meter_id, start_date, end_date, "power:reactive-", headers)

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

        if final_df.empty:
            st.warning("😕 Aucune donnée trouvée sur cette période.")
            st.stop()

        st.success(f"✅ Résultats pour : **{nom_parc}**")
        st.info("📊 Méthode de calcul: Conversion des puissances en tenant compte de l'intervalle entre mesures")
        
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
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_page()
    else:
        app_content()

if __name__ == "__main__":
    main()
