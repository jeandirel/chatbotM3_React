# 📘 Documentation Officielle - M3 Chatbot

## 🌟 Présentation
Le **M3 Chatbot** est un assistant documentaire intelligent conçu pour faciliter l'accès à l'information technique et procédurale. Il utilise une architecture **RAG (Retrieval-Augmented Generation)** pour fournir des réponses précises basées sur vos documents PDF, tout en citant ses sources.

L'application se compose d'une interface moderne en **React** et d'un backend puissant en **Python (FastAPI)**.

---

## 🚀 Fonctionnalités Clés

### 💬 Interface de Chat
- **Conversations Intelligentes** : Posez vos questions en langage naturel.
- **Historique** : Retrouvez vos anciennes discussions classées par date (Aujourd'hui, Hier, Cette semaine...).
- **Sources Citées** : Chaque réponse est accompagnée des extraits de documents utilisés.
- **Dictée Vocale** : Posez vos questions à la voix via le microphone.

### 🔐 Authentification & Utilisateurs
- **Inscription Sécurisée** : Création de compte réservée aux emails `@cerp-rouen.fr`.
- **Gestion de Profil** : Modification de mot de passe intégrée.
- **Séparation des Données** : Chaque utilisateur possède son propre historique privé.

### 🛠️ Administration & Feedback
- **Dashboard Admin** : Interface dédiée pour les administrateurs.
- **Gestion des Feedbacks** : Visualisez les retours utilisateurs (pouce haut/bas + commentaires) pour améliorer le modèle.
- **FAQ Dynamique** : Gérez les questions fréquentes directement depuis la base de données.

---

## 🏗️ Architecture Technique

### Frontend (`/src`)
- **Framework** : React 18 + Vite
- **Style** : CSS Modules & Lucide React (Icônes)
- **Navigation** : React Router DOM
- **État** : Gestion d'état locale et Context API (`AuthContext`).

### Backend (`/PocChatbotM3`)
- **Framework** : FastAPI
- **Base de Données** : SQLite (via SQLAlchemy)
- **Architecture Modulaire** :
  - `ingestion` : Traitement des PDF.
  - `embedding` : Vectorisation des textes.
  - `retriever` : Recherche sémantique.
  - `generation` : Interaction avec le LLM (Mistral/OpenAI).
  - `auth` : Gestion JWT et sécurité.

---

## 💻 Guide d'Installation

### Prérequis
- Node.js (v16+)
- Python (v3.10+)

### 1. Installation du Backend
```bash
cd PocChatbotM3
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Installation du Frontend
```bash
# À la racine du projet
npm install
```

---

## ▶️ Démarrage

### Lancer le Backend (Port 8000)
```bash
cd PocChatbotM3
# Assurez-vous que l'environnement virtuel est activé
uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload
```

### Lancer le Frontend (Port 5173)
```bash
# Dans un nouveau terminal à la racine
npm run dev
```
Accédez ensuite à l'application via : `http://localhost:5173`

---

## 📚 Guide Utilisateur

### Créer un compte
1. Sur la page de connexion, cliquez sur **"Créer un compte"**.
2. Remplissez le formulaire (Email doit finir par `@cerp-rouen.fr`).
3. Vous serez automatiquement connecté.

### Poser une question
1. Tapez votre question dans la barre du bas ou utilisez le micro.
2. L'IA analyse les documents et vous répond.
3. Cliquez sur les sources à droite pour voir le document PDF original.

### FAQ
- Cliquez sur le panneau de droite pour voir les questions fréquentes.
- Cliquez sur "voir toutes" pour ouvrir la liste complète.

---

## 🛡️ Guide Administrateur
*Compte par défaut : `admin` / `admin123`*

### Accéder au Dashboard
1. Connectez-vous en tant qu'admin.
2. Cliquez sur l'icône **Paramètres (roue dentée)** dans le panneau de droite ou via le menu utilisateur en haut.

### Gérer la FAQ
- Vous pouvez ajouter ou supprimer des questions fréquentes via l'API.
- Les modifications sont immédiates pour tous les utilisateurs.

### Analyser les Feedbacks
- Le tableau de bord affiche toutes les interactions.
- Filtrez par date ou par retour négatif pour identifier les réponses à améliorer.
