# Chatbot RAG M3 – Ultra-Avancé

Ce projet implémente un **chatbot de nouvelle génération** utilisant l'architecture **RAG (Retrieval-Augmented Generation)** pour répondre aux questions basées sur la documentation interne M3 (PDF/DOCX/CSV).
Le système s'appuie sur **Mistral AI** (embeddings & chat) et **Faiss** (indexation vectorielle) via une interface **Streamlit**.

---

## 🚀 Architecture RAG Avancée

Le pipeline RAG a été optimisé pour un **RAG conversationnel** complet :

1. **Pré-traitement de la Requête (`MistralChat.py`)**

   * Utilisation d'un LLM pour **réécrire les questions de suivi** en les contextualisant avec l’historique complet du chat.
   * Exemple : "Quel est son prix ?" devient "Quel est le prix de [produit mentionné précédemment] ?".

2. **Routage Hybride (`QueryClassifier.py`)**

   * Décision intelligente d'activer ou non la recherche RAG.
   * Basé sur des **mots-clés spécifiques** et un **seuil de similarité sémantique** pour éviter de solliciter le LLM inutilement.

3. **Recherche Améliorée (`VectorStore.py`)**

   * Récupération des **chunks pertinents** depuis l'index Faiss.
   * **Post-traitement contextuel** : inclusion des fragments voisins pour fournir un contexte plus riche et réduire les hallucinations.

---

## 🛠️ Prérequis

* Python **3.8+**
* Une **clé API Mistral AI** (`MISTRAL_API_KEY`)
* **Accès à la VM Azure** où le chatbot sera exécuté

---

## ⚙️ Installation et Configuration

### 1. Démarrage de la VM Azure

1. Connectez-vous au **[Azure Portal](https://portal.azure.com)**.
2. Sélectionnez votre **VM**.
3. Cliquez sur **Démarrer**.
4. Attendez environ **5 minutes** pour que la VM soit complètement opérationnelle.

### 2. Cloner le dépôt et créer l'environnement

```bash
git clone <URL_DU_DEPOT>
cd PocChatbotM3
python3 -m venv venv       # Windows : python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
# ou installation manuelle
pip install streamlit mistralai faiss-cpu pandas pypdf2 python-docx sqlalchemy python-dotenv langchain streamlit-feedback
```

### 4. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
MISTRAL_API_KEY="votre_clé_mistral_ici"
```

### 5. Placer la documentation

Placez tous vos fichiers (PDF, DOCX, CSV, etc.) dans le dossier défini dans `utils/config.py` (par défaut : `./inputs`).

---

## 🧱 Indexation des Documents

Avant de lancer le chatbot, construisez l'index vectoriel :

```bash
python indexer.py --input-dir inputs
```

**Description :**

* Lecture de tous les documents
* Découpage en **fragments (chunks)**
* Génération des **embeddings** via Mistral AI
* Sauvegarde de l’**index Faiss** (`vector_db/faiss_index.idx`) et des fragments (`vector_db/document_chunks.pkl`)

---

## 🖥️ Lancement du Chatbot

```bash
streamlit run MistralChat.py
```

Accédez à l’application via votre navigateur : `http://localhost:8501`

---

## 📂 Structure des Fichiers Clés

| Fichier                         | Rôle                                                           |
| ------------------------------- | -------------------------------------------------------------- |
| `MistralChat.py`                | Interface utilisateur Streamlit et moteur RAG principal        |
| `indexer.py`                    | Script de création initiale de l'index vectoriel               |
| `utils/vector_store.py`         | Gestion des embeddings, Faiss et post-traitement du contexte   |
| `utils/query_classifier.py`     | Routage hybride : décision RAG vs. Direct                      |
| `utils/conversation_history.py` | Gestion de l’historique des sessions et du RAG conversationnel |
| `utils/database.py`             | ORM SQLAlchemy pour logging et débogage avancé                 |
