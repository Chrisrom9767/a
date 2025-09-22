import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Analyse Bancaire - Turnover & Utilisation",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le template BOA (Vert et Blanc)
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #00B050 0%, #228B22 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0, 176, 80, 0.3);
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 3px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #00B050;
        border-top: 1px solid #e5e7eb;
    }
    .warning-box {
        background: linear-gradient(135deg, #fff7ed 0%, #fef3c7 100%);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #f59e0b;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(245, 158, 11, 0.1);
    }
    .success-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #00B050;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(0, 176, 80, 0.1);
    }
    .boa-info-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #e6ffed 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #00B050;
        margin: 1rem 0;
        box-shadow: 0 3px 10px rgba(0, 176, 80, 0.1);
    }
    .sidebar .stSelectbox {
        margin-bottom: 1rem;
    }
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #00B050;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton > button {
        background: linear-gradient(135deg, #00B050 0%, #228B22 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0, 176, 80, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 176, 80, 0.4);
    }
    .sidebar-header {
        background: linear-gradient(135deg, #00B050 0%, #228B22 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- Définition des types (repris de votre code original) ---
types_solde = {
    "COMPTE": "int64",
    "SOLDE": "int64"
}
dates_solde = ["DATPOS"]

types_mvt = {
    "COMPTE": "int64",
    "MNTDEV": "int64",
    "LIBELLE": "string",
    "CODOPSC": "string",
    "EXPL": "string",
    "NATOP": "object",
    "REFREL": "object",
    "NOOPER": "string",
    "DATHGEN": "float64",
    "NOREF": "float64",
    "DATECH": "float64",
    "XCASH": "float64"
}
dates_mvt = ["DATOPER"]

# --- Fonctions utilitaires ---
@st.cache_data
def lire_fichier_solde(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, dtype=types_solde, parse_dates=dates_solde)
        return df, None
    except Exception as e:
        return None, str(e)

@st.cache_data
def lire_fichier_mvt(uploaded_file):
    try:
        df = pd.read_excel(uploaded_file, dtype=types_mvt, parse_dates=dates_mvt)
        if 'DATVAL' in df.columns:
            df = df.drop(columns=['DATVAL'])
        return df, None
    except Exception as e:
        return None, str(e)

def obtenir_comptes_disponibles(df_solde, df_mvt):
    comptes_solde = df_solde['COMPTE'].dropna().unique() if df_solde is not None else []
    comptes_mvt = df_mvt['COMPTE'].dropna().unique() if df_mvt is not None else []
    comptes = set(comptes_solde).union(set(comptes_mvt))
    return sorted(comptes)

def filtrer_par_compte_mois_annee(df_solde, df_mvt, compte, annee, mois):
    df_solde_filtre = df_solde[
        (df_solde["COMPTE"] == compte) &
        (df_solde["DATPOS"].dt.year == annee) &
        (df_solde["DATPOS"].dt.month == mois)
    ] if df_solde is not None else pd.DataFrame()

    df_mvt_filtre = df_mvt[
        (df_mvt["COMPTE"] == compte) &
        (df_mvt["DATOPER"].dt.year == annee) &
        (df_mvt["DATOPER"].dt.month == mois)
    ] if df_mvt is not None else pd.DataFrame()

    return df_solde_filtre, df_mvt_filtre

def calculer_usage_rate_mensuel(df_solde_filtre, limite_credit):
    if df_solde_filtre.empty:
        return None, None
    
    df_result = df_solde_filtre.copy()
    df_result['TAUX_USAGE'] = (df_result['SOLDE'] / limite_credit) * 100
    moyenne_taux = df_result['TAUX_USAGE'].mean()
    
    return moyenne_taux, df_result

def calculer_turnover_routed_depuis_solde(df_solde, compte, annee, mois):
    date_ref = pd.Timestamp(year=annee, month=mois, day=1)
    debut_periode = date_ref - pd.DateOffset(months=2)
    fin_periode = date_ref + pd.DateOffset(months=1) - pd.Timedelta(days=1)

    df_filtre = df_solde[
        (df_solde['COMPTE'] == compte) &
        (df_solde['DATPOS'] >= debut_periode) &
        (df_solde['DATPOS'] <= fin_periode)
    ].sort_values(by='DATPOS').reset_index(drop=True)

    if df_filtre.empty or len(df_filtre) < 2:
        return None, None

    df_filtre['VARIATION'] = df_filtre['SOLDE'].diff()
    df_filtre['FLUX_CREDITEUR'] = df_filtre['VARIATION'].apply(lambda x: x if x > 0 else 0)
    total_flux_crediteur = df_filtre['FLUX_CREDITEUR'].sum()
    moyenne_solde = df_filtre['SOLDE'].mean()

    if moyenne_solde == 0:
        return None, None

    turnover = (total_flux_crediteur / moyenne_solde) * 100
    return turnover, df_filtre

# --- Interface principale ---
def main():
    # En-tête BOA
    st.markdown("""
    <div class="main-header">
        <h1>🏦 BOA - Analyse Bancaire</h1>
        <p>Calcul du Taux d'Utilisation et du Turnover</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar pour les paramètres
    st.sidebar.markdown('<div class="sidebar-header">📋 Configuration BOA</div>', unsafe_allow_html=True)
    
    # Upload des fichiers
    st.sidebar.subheader("📁 Chargement des fichiers")
    
    fichier_solde = st.sidebar.file_uploader(
        "Fichier des soldes journaliers",
        type=['xlsx', 'xls'],
        help="Fichier Excel contenant les soldes journaliers"
    )
    
    fichier_mvt = st.sidebar.file_uploader(
        "Fichier des mouvements",
        type=['xlsx', 'xls'],
        help="Fichier Excel contenant les mouvements"
    )

    # Variables d'état
    df_solde, df_mvt = None, None
    
    # Chargement des fichiers
    if fichier_solde is not None:
        with st.spinner("Chargement du fichier de solde..."):
            df_solde, error_solde = lire_fichier_solde(fichier_solde)
            if error_solde:
                st.sidebar.error(f"Erreur solde: {error_solde}")
            else:
                st.sidebar.success(f"✅ Solde chargé ({len(df_solde)} lignes)")

    if fichier_mvt is not None:
        with st.spinner("Chargement du fichier de mouvements..."):
            df_mvt, error_mvt = lire_fichier_mvt(fichier_mvt)
            if error_mvt:
                st.sidebar.error(f"Erreur mouvement: {error_mvt}")
            else:
                st.sidebar.success(f"✅ Mouvements chargés ({len(df_mvt)} lignes)")

    # Interface principale
    if df_solde is not None or df_mvt is not None:
        comptes = obtenir_comptes_disponibles(df_solde, df_mvt)
        
        if comptes:
            # Sélection des paramètres
            st.sidebar.subheader("⚙️ Paramètres d'analyse")
            
            compte_selectionne = st.sidebar.selectbox(
                "Compte à analyser:",
                comptes,
                format_func=lambda x: f"Compte {x}"
            )
            
            col1, col2 = st.sidebar.columns(2)
            with col1:
                annee = st.selectbox(
                    "Année:",
                    range(2020, datetime.now().year + 2),
                    index=datetime.now().year - 2020
                )
            with col2:
                mois = st.selectbox(
                    "Mois:",
                    range(1, 13),
                    index=datetime.now().month - 1,
                    format_func=lambda x: f"{x:02d}"
                )
            
            limite_credit = st.sidebar.number_input(
                "Limite de crédit:",
                min_value=0.0,
                value=1000000.0,
                step=10000.0,
                format="%.2f"
            )

            # Bouton d'analyse
            if st.sidebar.button("🚀 Lancer l'analyse", type="primary"):
                analyser_donnees(df_solde, df_mvt, compte_selectionne, annee, mois, limite_credit)

    else:
        # Page d'accueil BOA
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="boa-info-box">
                <h3 style="color: #00B050; text-align: center;">👋 Bienvenue sur l'outil BOA d'analyse bancaire</h3>
                
                <p><strong>Pour commencer votre analyse:</strong></p>
                <ol>
                    <li><strong>📁 Chargez vos fichiers</strong> Excel dans la sidebar</li>
                    <li><strong>🎯 Sélectionnez</strong> le compte et la période</li>
                    <li><strong>⚙️ Configurez</strong> la limite de crédit</li>
                    <li><strong>🚀 Lancez</strong> l'analyse</li>
                </ol>
                
                <p><strong>📊 L'outil calculera automatiquement:</strong></p>
                <ul>
                    <li>✅ Le taux d'utilisation du crédit</li>
                    <li>✅ Le turnover routed sur 3 mois</li>
                    <li>✅ Les visualisations interactives</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

def analyser_donnees(df_solde, df_mvt, compte, annee, mois, limite_credit):
    """Fonction principale d'analyse des données"""
    
    # Filtrage des données
    df_solde_filtre, df_mvt_filtre = filtrer_par_compte_mois_annee(
        df_solde, df_mvt, compte, annee, mois
    )
    
    # En-tête des résultats
    st.header(f"📊 Résultats pour le compte {compte}")
    st.subheader(f"📅 Période: {mois:02d}/{annee}")
    
    # Métriques générales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lignes de solde", len(df_solde_filtre))
    with col2:
        st.metric("Lignes de mouvement", len(df_mvt_filtre))
    with col3:
        st.metric("Limite de crédit", f"{limite_credit:,.0f}")

    # Analyse du taux d'utilisation
    if not df_solde_filtre.empty and limite_credit > 0:
        st.subheader("📈 Analyse du Taux d'Utilisation")
        
        taux_moyen, df_usage = calculer_usage_rate_mensuel(df_solde_filtre, limite_credit)
        
        if taux_moyen is not None:
            # Métriques du taux d'utilisation
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Taux moyen", f"{taux_moyen:.2f}%")
            with col2:
                taux_max = df_usage['TAUX_USAGE'].max()
                st.metric("Taux maximum", f"{taux_max:.2f}%")
            with col3:
                solde_moyen = df_usage['SOLDE'].mean()
                st.metric("Solde moyen", f"{solde_moyen:,.0f}")

            # Graphique du taux d'utilisation avec couleurs BOA
            fig_usage = px.line(
                df_usage, 
                x='DATPOS', 
                y='TAUX_USAGE',
                title="Évolution du Taux d'Utilisation",
                labels={'TAUX_USAGE': 'Taux d\'Utilisation (%)', 'DATPOS': 'Date'},
                color_discrete_sequence=['#00B050']
            )
            fig_usage.add_hline(y=100, line_dash="dash", line_color="#dc2626", 
                              annotation_text="Limite de crédit (100%)")
            fig_usage.update_layout(
                height=400,
                plot_bgcolor='rgba(240, 253, 244, 0.3)',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_usage, use_container_width=True)

            # Tableau détaillé
            with st.expander("📋 Détail journalier du taux d'utilisation"):
                st.dataframe(
                    df_usage[['DATPOS', 'SOLDE', 'TAUX_USAGE']].round(2),
                    use_container_width=True
                )

    # Analyse du Turnover
    if df_solde is not None:
        st.subheader("🔄 Analyse du Turnover Routed")
        
        turnover, df_turnover = calculer_turnover_routed_depuis_solde(
            df_solde, compte, annee, mois
        )
        
        if turnover is not None and df_turnover is not None:
            # Métriques du turnover
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Turnover Routed", f"{turnover:.2f}%")
            with col2:
                total_flux = df_turnover['FLUX_CREDITEUR'].sum()
                st.metric("Total flux créditeurs", f"{total_flux:,.0f}")
            with col3:
                moyenne_solde = df_turnover['SOLDE'].mean()
                st.metric("Moyenne solde (3 mois)", f"{moyenne_solde:,.0f}")

            # Graphiques du turnover
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique des soldes avec couleurs BOA
                fig_solde = px.line(
                    df_turnover, 
                    x='DATPOS', 
                    y='SOLDE',
                    title="Évolution des Soldes (3 derniers mois)",
                    color_discrete_sequence=['#00B050']
                )
                fig_solde.update_layout(
                    height=350,
                    plot_bgcolor='rgba(240, 253, 244, 0.3)',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig_solde, use_container_width=True)
            
            with col2:
                # Graphique des flux créditeurs avec couleurs BOA
                df_flux_positif = df_turnover[df_turnover['FLUX_CREDITEUR'] > 0]
                if not df_flux_positif.empty:
                    fig_flux = px.bar(
                        df_flux_positif, 
                        x='DATPOS', 
                        y='FLUX_CREDITEUR',
                        title="Flux Créditeurs Journaliers",
                        color_discrete_sequence=['#228B22']
                    )
                    fig_flux.update_layout(
                        height=350,
                        plot_bgcolor='rgba(240, 253, 244, 0.3)',
                        paper_bgcolor='white'
                    )
                    st.plotly_chart(fig_flux, use_container_width=True)

            # Tableau détaillé du turnover
            with st.expander("📋 Détail du calcul du turnover"):
                st.dataframe(
                    df_turnover[['DATPOS', 'SOLDE', 'VARIATION', 'FLUX_CREDITEUR']].round(2),
                    use_container_width=True
                )

            # Interprétation
            if turnover > 200:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Turnover élevé</strong><br>
                    Le compte présente une activité importante avec un turnover supérieur à 200%.
                </div>
                """, unsafe_allow_html=True)
            elif turnover > 100:
                st.markdown("""
                <div class="warning-box">
                    <strong>⚠️ Turnover modéré</strong><br>
                    Le compte présente une activité modérée avec un turnover entre 100% et 200%.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="warning-box">
                    <strong>📉 Turnover faible</strong><br>
                    Le compte présente une activité limitée avec un turnover inférieur à 100%.
                </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("⚠️ Impossible de calculer le turnover routed (données insuffisantes)")

    # Analyse des mouvements si disponible
    if not df_mvt_filtre.empty:
        st.subheader("💳 Analyse des Mouvements")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            nb_operations = len(df_mvt_filtre)
            st.metric("Nombre d'opérations", nb_operations)
        with col2:
            montant_total = df_mvt_filtre['MNTDEV'].sum()
            st.metric("Montant total", f"{montant_total:,.0f}")
        with col3:
            montant_moyen = df_mvt_filtre['MNTDEV'].mean()
            st.metric("Montant moyen", f"{montant_moyen:,.0f}")



if __name__ == "__main__":
    main()