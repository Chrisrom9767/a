import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Analyse Bancaire BOA - Turnover & Découvert",
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
    .danger-box {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #dc2626;
        margin: 1rem 0;
        box-shadow: 0 2px 6px rgba(220, 38, 38, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Définition des types ---
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

# --- Nouvelles fonctions pour l'analyse de découvert ---
def moyenne_duree_decouvert(groupe):
    """Calcule la durée moyenne des périodes de découvert consécutives"""
    a_decouvert = groupe['A_DECOUVERT'].values
    if not a_decouvert.any():
        return 0
    durees = []
    count = 0
    for val in a_decouvert:
        if val:
            count += 1
        else:
            if count > 0:
                durees.append(count)
                count = 0
    if count > 0:
        durees.append(count)
    return sum(durees) / len(durees) if durees else 0

def analyser_decouvert_et_credit_line_overdraft(df_solde, compte, date_position, seuil_utilisateur):
    """
    Analyse complète du découvert et des Credit Line Overdraft
    """
    if df_solde is None or df_solde.empty:
        return None, None, None, None
    
    # Filtrer pour le compte spécifique
    dfS2 = df_solde[df_solde['COMPTE'] == compte].copy()
    
    if dfS2.empty:
        return None, None, None, None
    
    # === Partie 1 : Durée moyenne à découvert sur les 12 mois avant le mois sélectionné ===
    start_date_decouvert = date_position - pd.DateOffset(months=12)
    end_date_decouvert = date_position - pd.offsets.MonthBegin(1)
    
    # Filtrer données pour période découvert
    dfS2_periode_decouvert = dfS2[(dfS2['DATPOS'] >= start_date_decouvert) & (dfS2['DATPOS'] <= end_date_decouvert)].copy()
    dfS2_periode_decouvert['MOIS'] = dfS2_periode_decouvert['DATPOS'].dt.to_period('M')
    
    # Calcul solde moyen mensuel
    solde_moyen_mensuel_decouvert = dfS2_periode_decouvert.groupby(['COMPTE', 'MOIS'])['SOLDE'].mean().reset_index()
    solde_moyen_mensuel_decouvert = solde_moyen_mensuel_decouvert.rename(columns={'SOLDE': 'SOLDE_MOYEN'})
    
    # Appliquer règle découvert
    solde_moyen_mensuel_decouvert['A_DECOUVERT'] = solde_moyen_mensuel_decouvert['SOLDE_MOYEN'] <= seuil_utilisateur
    
    # Trier
    solde_moyen_mensuel_decouvert = solde_moyen_mensuel_decouvert.sort_values(['COMPTE', 'MOIS'])
    
    # Calcul durée moyenne découvert
    duree_moyenne_decouvert_val = 0
    if not solde_moyen_mensuel_decouvert.empty:
        duree_moyenne_decouvert_val = moyenne_duree_decouvert(solde_moyen_mensuel_decouvert)
    
    # === Partie 2 : Analyse des "Credit Line Overdraft" sur les 12 mois incluant le mois sélectionné ===
    start_date_overdraft = date_position - pd.DateOffset(months=11)
    end_date_overdraft = date_position + pd.offsets.MonthEnd(0)
    
    # Filtrer données pour période overdraft
    dfS2_periode_overdraft = dfS2[(dfS2['DATPOS'] >= start_date_overdraft) & (dfS2['DATPOS'] <= end_date_overdraft)].copy()
    dfS2_periode_overdraft['MOIS'] = dfS2_periode_overdraft['DATPOS'].dt.to_period('M')
    
    # Calcul solde moyen mensuel
    solde_moyen_mensuel_overdraft = dfS2_periode_overdraft.groupby(['COMPTE', 'MOIS'])['SOLDE'].mean().reset_index()
    solde_moyen_mensuel_overdraft = solde_moyen_mensuel_overdraft.rename(columns={'SOLDE': 'SOLDE_MOYEN'})
    
    # Identifier le mois pic (solde moyen max) par compte
    pics = None
    solde_moyen_complet = None
    nb_credit_line_overdraft = 0
    
    if not solde_moyen_mensuel_overdraft.empty:
        pics = solde_moyen_mensuel_overdraft.loc[
            solde_moyen_mensuel_overdraft.groupby('COMPTE')['SOLDE_MOYEN'].idxmax()
        ].rename(columns={'MOIS': 'MOIS_PIC', 'SOLDE_MOYEN': 'SOLDE_MAXI'})
        
        # Jointure pour calcul écart au pic
        solde_moyen_complet = solde_moyen_mensuel_overdraft.merge(pics[['COMPTE', 'SOLDE_MAXI']], on='COMPTE', how='left')
        solde_moyen_complet['ECART_AU_PIC'] = solde_moyen_complet['SOLDE_MAXI'] - solde_moyen_complet['SOLDE_MOYEN']
        
        # Tri et calcul solde précédent
        solde_moyen_complet = solde_moyen_complet.sort_values(['COMPTE', 'MOIS'])
        solde_moyen_complet['SOLDE_PRECEDENT'] = solde_moyen_complet.groupby('COMPTE')['SOLDE_MOYEN'].shift(1)
        
        # Détection "Credit Line Overdraft" = solde moyen qui s'améliore mois à mois
        solde_moyen_complet['CREDIT_LINE_OVERDRAFT'] = (
            solde_moyen_complet['SOLDE_MOYEN'] > solde_moyen_complet['SOLDE_PRECEDENT']
        ).astype(int)
        
        # Compter le nombre de Credit Line Overdraft
        nb_credit_line_overdraft = solde_moyen_complet['CREDIT_LINE_OVERDRAFT'].sum()
    
    return duree_moyenne_decouvert_val, solde_moyen_mensuel_decouvert, solde_moyen_complet, nb_credit_line_overdraft

# --- Interface principale ---
def main():
    # En-tête BOA
    st.markdown("""
    <div class="main-header">
        <h1>🏦 BOA - Analyse Bancaire Complète</h1>
        <p>Taux d'Utilisation, Turnover, Découvert & Credit Line Overdraft</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar pour les paramètres
    st.sidebar.markdown('<div class="sidebar-header">📋 Configuration BOA</div>', unsafe_allow_html=True)
    
    # Sélection du type d'analyse
    type_analyse = st.sidebar.radio(
        "Type d'analyse:",
        ["🔄 Turnover & Utilisation", "📉 Découvert & Credit Line"],
        help="Choisissez le type d'analyse à effectuer"
    )
    
    # Upload des fichiers
    st.sidebar.subheader("📁 Chargement des fichiers")
    
    fichier_solde = st.sidebar.file_uploader(
        "Fichier des soldes journaliers",
        type=['xlsx', 'xls'],
        help="Fichier Excel contenant les soldes journaliers"
    )
    
    fichier_mvt = None
    if type_analyse == "🔄 Turnover & Utilisation":
        fichier_mvt = st.sidebar.file_uploader(
            "Fichier des mouvements (optionnel)",
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
    if df_solde is not None:
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
                    index=min(datetime.now().year - 2020, 4)
                )
            with col2:
                mois = st.selectbox(
                    "Mois:",
                    range(1, 13),
                    index=datetime.now().month - 1,
                    format_func=lambda x: f"{x:02d}"
                )
            
            # Paramètres spécifiques selon le type d'analyse
            if type_analyse == "🔄 Turnover & Utilisation":
                limite_credit = st.sidebar.number_input(
                    "Limite de crédit:",
                    min_value=0.0,
                    value=1000000.0,
                    step=10000.0,
                    format="%.2f"
                )
                seuil_decouvert = None
            else:
                limite_credit = None
                seuil_decouvert = st.sidebar.number_input(
                    "Seuil de découvert:",
                    min_value=-1000000.0,
                    max_value=0.0,
                    value=0.0,
                    step=1000.0,
                    format="%.2f",
                    help="Valeur seuil en dessous de laquelle le compte est considéré à découvert"
                )

            # Bouton d'analyse
            if st.sidebar.button("🚀 Lancer l'analyse", type="primary"):
                if type_analyse == "🔄 Turnover & Utilisation":
                    analyser_turnover_utilisation(df_solde, df_mvt, compte_selectionne, annee, mois, limite_credit)
                else:
                    analyser_decouvert_credit_line(df_solde, compte_selectionne, annee, mois, seuil_decouvert)

    else:
        # Page d'accueil BOA
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="boa-info-box">
                <h3>🏦 Bienvenue dans l'outil d'analyse BOA</h3>
                
                <h4>📊 Analyses disponibles:</h4>
                
                <strong>🔄 Turnover & Utilisation:</strong>
                <ul>
                    <li>Taux d'utilisation du crédit</li>
                    <li>Turnover routed sur 3 mois</li>
                    <li>Visualisations interactives</li>
                </ul>
                
                <strong>📉 Découvert & Credit Line:</strong>
                <ul>
                    <li>Durée moyenne à découvert (12 mois)</li>
                    <li>Analyse Credit Line Overdraft</li>
                    <li>Évolution des soldes mensuels</li>
                </ul>
                
                <hr>
                
                <h4>🚀 Pour commencer:</h4>
                <ol>
                    <li>Choisissez le type d'analyse</li>
                    <li>Chargez votre fichier Excel des soldes</li>
                    <li>Sélectionnez le compte et la période</li>
                    <li>Configurez les paramètres</li>
                    <li>Lancez l'analyse</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

def analyser_turnover_utilisation(df_solde, df_mvt, compte, annee, mois, limite_credit):
    """Fonction d'analyse du turnover et de l'utilisation"""
    
    # Filtrage des données
    df_solde_filtre, df_mvt_filtre = filtrer_par_compte_mois_annee(
        df_solde, df_mvt, compte, annee, mois
    )
    
    # En-tête des résultats
    st.header(f"📊 Analyse Turnover & Utilisation - Compte {compte}")
    st.subheader(f"📅 Période: {mois:02d}/{annee}")
    
    # Métriques générales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lignes de solde", len(df_solde_filtre))
    with col2:
        st.metric("Lignes de mouvement", len(df_mvt_filtre) if df_mvt_filtre is not None else 0)
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

            # Graphique du taux d'utilisation
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
                fig_solde = px.line(
                    df_turnover, 
                    x='DATPOS', 
                    y='SOLDE',
                    title="Évolution des Soldes (3 derniers mois)",
                    color_discrete_sequence=['#00B050']
                )
                fig_solde.update_layout(height=350, plot_bgcolor='rgba(240, 253, 244, 0.3)')
                st.plotly_chart(fig_solde, use_container_width=True)
            
            with col2:
                df_flux_positif = df_turnover[df_turnover['FLUX_CREDITEUR'] > 0]
                if not df_flux_positif.empty:
                    fig_flux = px.bar(
                        df_flux_positif, 
                        x='DATPOS', 
                        y='FLUX_CREDITEUR',
                        title="Flux Créditeurs Journaliers",
                        color_discrete_sequence=['#228B22']
                    )
                    fig_flux.update_layout(height=350, plot_bgcolor='rgba(240, 253, 244, 0.3)')
                    st.plotly_chart(fig_flux, use_container_width=True)

def analyser_decouvert_credit_line(df_solde, compte, annee, mois, seuil_decouvert):
    """Fonction d'analyse du découvert et des Credit Line Overdraft"""
    
    # Date de référence
    date_position = pd.to_datetime(f"{annee}-{mois:02d}-01")
    
    # En-tête des résultats
    st.header(f"📉 Analyse Découvert & Credit Line - Compte {compte}")
    st.subheader(f"📅 Date de référence: {mois:02d}/{annee}")
    
    # Analyse complète
    duree_moyenne, solde_decouvert, solde_complet, nb_credit_line = analyser_decouvert_et_credit_line_overdraft(
        df_solde, compte, date_position, seuil_decouvert
    )
    
    if duree_moyenne is not None or solde_complet is not None:
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Durée moyenne découvert", 
                f"{duree_moyenne:.1f} mois" if duree_moyenne is not None else "N/A",
                help="Durée moyenne des périodes consécutives de découvert sur 12 mois"
            )
        with col2:
            st.metric(
                "Credit Line Overdraft", 
                f"{nb_credit_line} fois" if nb_credit_line is not None else "N/A",
                help="Nombre de fois où le solde s'est amélioré d'un mois à l'autre"
            )
        with col3:
            st.metric("Seuil découvert", f"{seuil_decouvert:,.0f}")

        # Analyse du découvert
        if solde_decouvert is not None and not solde_decouvert.empty:
            st.subheader("📊 Analyse du Découvert (12 mois précédents)")
            
            # Graphique de l'évolution du découvert
            fig_decouvert = px.bar(
                solde_decouvert,
                x='MOIS',
                y='SOLDE_MOYEN',
                color='A_DECOUVERT',
                title="Évolution Mensuelle des Soldes - Statut Découvert",
                labels={'SOLDE_MOYEN': 'Solde Moyen', 'MOIS': 'Mois', 'A_DECOUVERT': 'À Découvert'},
                color_discrete_map={True: '#dc2626', False: '#00B050'}
            )
            fig_decouvert.add_hline(
                y=seuil_decouvert, 
                line_dash="dash", 
                line_color="#f59e0b",
                annotation_text=f"Seuil découvert ({seuil_decouvert:,.0f})"
            )
            fig_decouvert.update_layout(
                height=400,
                plot_bgcolor='rgba(240, 253, 244, 0.3)',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_decouvert, use_container_width=True)
            
            # Statistiques du découvert
            nb_mois_decouvert = solde_decouvert['A_DECOUVERT'].sum()
            nb_mois_total = len(solde_decouvert)
            pourcentage_decouvert = (nb_mois_decouvert / nb_mois_total * 100) if nb_mois_total > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mois à découvert", f"{nb_mois_decouvert}/{nb_mois_total}")
            with col2:
                st.metric("Pourcentage découvert", f"{pourcentage_decouvert:.1f}%")
            with col3:
                solde_min = solde_decouvert['SOLDE_MOYEN'].min()
                st.metric("Solde minimum", f"{solde_min:,.0f}")
            
            # Interprétation du découvert
            if duree_moyenne > 3:
                st.markdown("""
                <div class="danger-box">
                    <strong>⚠️ Découvert préoccupant</strong><br>
                    La durée moyenne de découvert dépasse 3 mois, ce qui indique des difficultés financières récurrentes.
                </div>
                """, unsafe_allow_html=True)
            elif duree_moyenne > 1:
                st.markdown("""
                <div class="warning-box">
                    <strong>⚠️ Découvert modéré</strong><br>
                    Le compte présente des périodes de découvert régulières nécessitant une surveillance.
                </div>
                """, unsafe_allow_html=True)
            elif duree_moyenne > 0:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Découvert ponctuel</strong><br>
                    Les découverts sont occasionnels et de courte durée.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Aucun découvert</strong><br>
                    Le compte n'a pas présenté de période de découvert sur la période analysée.
                </div>
                """, unsafe_allow_html=True)

        # Analyse des Credit Line Overdraft
        if solde_complet is not None and not solde_complet.empty:
            st.subheader("📈 Analyse Credit Line Overdraft (12 mois incluant période)")
            
            # Graphique des Credit Line Overdraft
            fig_credit_line = go.Figure()
            
            # Ligne des soldes moyens
            fig_credit_line.add_trace(go.Scatter(
                x=solde_complet['MOIS'].astype(str),
                y=solde_complet['SOLDE_MOYEN'],
                mode='lines+markers',
                name='Solde Moyen',
                line=dict(color='#00B050', width=3),
                marker=dict(size=8)
            ))
            
            # Marquer les Credit Line Overdraft
            credit_line_data = solde_complet[solde_complet['CREDIT_LINE_OVERDRAFT'] == 1]
            if not credit_line_data.empty:
                fig_credit_line.add_trace(go.Scatter(
                    x=credit_line_data['MOIS'].astype(str),
                    y=credit_line_data['SOLDE_MOYEN'],
                    mode='markers',
                    name='Credit Line Overdraft',
                    marker=dict(
                        symbol='triangle-up',
                        size=15,
                        color='#228B22',
                        line=dict(color='#ffffff', width=2)
                    )
                ))
            
            fig_credit_line.update_layout(
                title="Évolution des Soldes et Credit Line Overdraft",
                xaxis_title="Mois",
                yaxis_title="Solde Moyen",
                height=400,
                plot_bgcolor='rgba(240, 253, 244, 0.3)',
                paper_bgcolor='white',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_credit_line, use_container_width=True)
            
            # Détail des Credit Line Overdraft
            if not credit_line_data.empty:
                st.subheader("🔍 Détail des Credit Line Overdraft")
                
                # Tableau des améliorations
                ameliorations = credit_line_data[['MOIS', 'SOLDE_MOYEN', 'SOLDE_PRECEDENT']].copy()
                ameliorations['AMELIORATION'] = ameliorations['SOLDE_MOYEN'] - ameliorations['SOLDE_PRECEDENT']
                ameliorations['AMELIORATION_PCT'] = (ameliorations['AMELIORATION'] / abs(ameliorations['SOLDE_PRECEDENT']) * 100).round(2)
                
                st.dataframe(
                    ameliorations.rename(columns={
                        'MOIS': 'Mois',
                        'SOLDE_MOYEN': 'Solde Actuel',
                        'SOLDE_PRECEDENT': 'Solde Précédent',
                        'AMELIORATION': 'Amélioration',
                        'AMELIORATION_PCT': 'Amélioration %'
                    }),
                    use_container_width=True
                )
                
                # Métriques des améliorations
                amelioration_moyenne = ameliorations['AMELIORATION'].mean()
                amelioration_totale = ameliorations['AMELIORATION'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Amélioration moyenne", f"{amelioration_moyenne:,.0f}")
                with col2:
                    st.metric("Amélioration totale", f"{amelioration_totale:,.0f}")
                with col3:
                    st.metric("Mois d'amélioration", len(ameliorations))
            
            # Interprétation des Credit Line Overdraft
            if nb_credit_line >= 6:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Tendance positive forte</strong><br>
                    Le compte montre une amélioration constante avec de nombreux Credit Line Overdraft.
                </div>
                """, unsafe_allow_html=True)
            elif nb_credit_line >= 3:
                st.markdown("""
                <div class="success-box">
                    <strong>✅ Tendance positive</strong><br>
                    Le compte présente plusieurs améliorations mensuelles consécutives.
                </div>
                """, unsafe_allow_html=True)
            elif nb_credit_line > 0:
                st.markdown("""
                <div class="warning-box">
                    <strong>⚠️ Amélioration limitée</strong><br>
                    Quelques améliorations mensuelles mais la tendance reste fragile.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="danger-box">
                    <strong>⚠️ Aucune amélioration</strong><br>
                    Le compte ne présente aucune amélioration mensuelle sur la période.
                </div>
                """, unsafe_allow_html=True)

        # Tableau détaillé en expandeur
        if solde_complet is not None and not solde_complet.empty:
            with st.expander("📋 Données détaillées - Credit Line Overdraft"):
                st.dataframe(
                    solde_complet[['MOIS', 'SOLDE_MOYEN', 'SOLDE_PRECEDENT', 'CREDIT_LINE_OVERDRAFT']].rename(columns={
                        'MOIS': 'Mois',
                        'SOLDE_MOYEN': 'Solde Moyen',
                        'SOLDE_PRECEDENT': 'Solde Précédent',
                        'CREDIT_LINE_OVERDRAFT': 'Credit Line Overdraft'
                    }),
                    use_container_width=True
                )
        
        if solde_decouvert is not None and not solde_decouvert.empty:
            with st.expander("📋 Données détaillées - Découvert"):
                st.dataframe(
                    solde_decouvert[['MOIS', 'SOLDE_MOYEN', 'A_DECOUVERT']].rename(columns={
                        'MOIS': 'Mois',
                        'SOLDE_MOYEN': 'Solde Moyen',
                        'A_DECOUVERT': 'À Découvert'
                    }),
                    use_container_width=True
                )
    
    else:
        st.warning("⚠️ Aucune donnée disponible pour ce compte sur la période sélectionnée.")

if __name__ == "__main__":
    main()
