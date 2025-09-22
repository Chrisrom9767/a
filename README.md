# 🏦 BOA - Analyse Bancaire (Turnover & Taux d'Utilisation)

Application web développée avec Streamlit pour la Bank Of Africa (BOA), permettant l'analyse des comptes bancaires avec calcul du taux d'utilisation du crédit et du turnover routed.

## ✨ Fonctionnalités

- **📊 Calcul du Taux d'Utilisation** : Analyse journalière et mensuelle du taux d'utilisation du crédit
- **🔄 Turnover Routed** : Calcul du turnover basé sur les variations de solde sur 3 mois
- **📈 Visualisations Interactives** : Graphiques dynamiques avec Plotly
- **📋 Interface Professionnelle** : Design moderne adapté au secteur bancaire
- **📁 Support Multi-formats** : Import de fichiers Excel (.xlsx, .xls)

## 🚀 Déploiement sur Streamlit Cloud

### Étape 1 : Préparation du repository GitHub

1. Créez un nouveau repository sur GitHub
2. Clonez le repository localement :
```bash
git clone https://github.com/votre-username/votre-repo-name.git
cd votre-repo-name
```

3. Ajoutez les fichiers suivants dans votre repository :
   - `app.py` (le code principal Streamlit)
   - `requirements.txt`
   - `.streamlit/config.toml`
   - `README.md`

4. Commitez et poussez vos fichiers :
```bash
git add .
git commit -m "Initial commit - Banking Analysis App"
git push origin main
```

### Étape 2 : Déploiement sur Streamlit Cloud

1. **Connectez-vous** à [share.streamlit.io](https://share.streamlit.io)
2. **Cliquez sur "New app"**
3. **Sélectionnez votre repository GitHub**
4. **Configurez** :
   - Repository : `votre-username/votre-repo-name`
   - Branch : `main`
   - Main file path : `app.py`
5. **Cliquez sur "Deploy!"**

L'application sera disponible à l'adresse : `https://votre-app-name.streamlit.app`

## 💻 Installation Locale

Pour tester l'application en local :

```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement de l'application
streamlit run app.py
```

## 📋 Utilisation

1. **Chargement des fichiers** : 
   - Fichier des soldes journaliers (.xlsx)
   - Fichier des mouvements (.xlsx)

2. **Configuration** :
   - Sélection du compte à analyser
   - Choix de la période (mois/année)
   - Définition de la limite de crédit

3. **Analyse** :
   - Cliquez sur "🚀 Lancer l'analyse"
   - Consultez les résultats et graphiques

## 📊 Métriques Calculées

### Taux d'Utilisation
- Calcul journalier : `(Solde / Limite de crédit) × 100`
- Moyenne mensuelle
- Visualisation de l'évolution

### Turnover Routed
- Période : 3 derniers mois
- Calcul : `(Total flux créditeurs / Moyenne des soldes) × 100`
- Basé sur les variations positives de solde

## 🔧 Structure des Données

### Fichier Soldes
- `COMPTE` : Numéro de compte
- `SOLDE` : Solde du compte
- `DATPOS` : Date de position

### Fichier Mouvements
- `COMPTE` : Numéro de compte
- `MNTDEV` : Montant en devise
- `DATOPER` : Date d'opération
- `LIBELLE` : Libellé de l'opération

## 🛡️ Sécurité

- Aucune donnée n'est stockée sur les serveurs
- Traitement des fichiers en mémoire uniquement
- Interface sécurisée pour environnement bancaire

## 📞 Support

Pour toute question ou suggestion, n'hésitez pas à ouvrir une issue sur GitHub.

---

*Développé avec ❤️ pour le secteur bancaire*