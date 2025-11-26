# 🏗️ Documentation Technique & Architecture

Ce document détaille l'architecture interne du backend modulaire du chatbot M3. Il est destiné aux développeurs souhaitant comprendre, maintenir ou étendre le système.

---

## 🔄 Pipeline RAG (Retrieval-Augmented Generation)

Le cœur du système repose sur un pipeline RAG avancé qui transforme une question utilisateur en une réponse documentée.

### Flux de Traitement d'une Requête (`process_query_logic`)

1.  **Réception** : La requête utilisateur arrive via l'API.
2.  **Cache Check** : Le `CacheService` vérifie si cette question a déjà été posée récemment pour renvoyer une réponse immédiate.
3.  **Réécriture (Query Rewriting)** : Le `GenerationService` reformule la question en utilisant l'historique de la conversation pour la rendre autonome (ex: "C'est quoi ?" -> "Qu'est-ce que le produit X ?").
4.  **Détection Smalltalk** : Si la question est une salutation ou hors sujet, une réponse directe est générée sans recherche documentaire.
5.  **Recherche (Retrieval)** : Le `RetrieverService` interroge le `VectorStore` pour trouver les fragments de documents les plus proches sémantiquement.
6.  **Réordonnancement (Reranking)** : Le `RerankingService` analyse les documents trouvés et les re-classe par pertinence précise pour éliminer le bruit.
7.  **Génération** : Le `GenerationService` construit un prompt contenant les documents pertinents et la question, puis interroge le LLM (Mistral/OpenAI).
8.  **Logging** : L'interaction complète (question, réponse, sources, métadonnées) est sauvegardée par le `SessionService`.

---

## 🧩 Détail des Modules

### 1. Ingestion (`modules/ingestion.py`) & Preprocessing (`modules/preprocessing.py`)
*   **Rôle** : Transformer les fichiers PDF bruts en vecteurs exploitables.
*   **Logique** :
    *   Extraction du texte des PDF page par page.
    *   Nettoyage du texte (suppression des en-têtes/pieds de page répétitifs).
    *   **Chunking** : Découpage du texte en segments de taille fixe (ex: 500 tokens) avec chevauchement (overlap) pour ne pas couper le contexte.

### 2. Embedding (`modules/embedding.py`)
*   **Rôle** : Convertir le texte en vecteurs numériques.
*   **Modèle** : Utilise `sentence-transformers` (ex: `all-MiniLM-L6-v2` ou API Mistral Embeddings) pour générer des représentations sémantiques denses.
*   **Sortie** : Vecteurs de dimension 384 (ou 1024 selon le modèle).

### 3. Vector Store (`modules/vector_store.py`)
*   **Technologie** : **FAISS** (Facebook AI Similarity Search).
*   **Fonctionnement** :
    *   Stocke les vecteurs d'embeddings dans un index optimisé pour la recherche rapide.
    *   Maintient une correspondance entre l'ID du vecteur et les métadonnées du document (source, page, contenu texte).
    *   Persistance sur disque (`faiss_index.bin`).

### 4. Retriever (`modules/retriever.py`)
*   **Rôle** : Retrouver les documents candidats.
*   **Méthode** : Recherche par similarité cosinus (Cosine Similarity) ou distance L2.
*   **Stratégie** : Récupère un nombre large de candidats (ex: `k=10`) pour maximiser le rappel (Recall).

### 5. Reranking (`modules/reranking.py`)
*   **Rôle** : Affiner les résultats de la recherche.
*   **Technologie** : Utilise un **Cross-Encoder** (modèle qui prend la question ET le document en entrée pour scorer leur pertinence).
*   **Pourquoi ?** : La recherche vectorielle est rapide mais parfois imprécise. Le reranking est plus lent mais beaucoup plus précis. Il sélectionne le Top-3 ou Top-5 final.

### 6. Generation (`modules/generation.py`)
*   **Rôle** : Produire la réponse finale.
*   **LLM** : Interface avec l'API Mistral AI ou OpenAI.
*   **Prompt Engineering** : Construit un prompt système strict ("Tu es un assistant expert...", "Réponds uniquement basé sur le contexte fourni...").
*   **Gestion d'Historique** : Intègre les derniers échanges pour maintenir le fil de la conversation.

### 7. Session & Database (`modules/session.py`, `utils/database.py`)
*   **Stockage** : SQLite.
*   **Modèles** :
    *   `User` : Comptes utilisateurs.
    *   `Conversation` : Fils de discussion.
    *   `Interaction` : Paires Question/Réponse + Feedback.
    *   `FAQ` : Questions fréquentes.
*   **Fonctionnalité** : Permet de reprendre une conversation passée et de stocker les feedbacks pour l'amélioration continue.

### 8. Authentication (`modules/auth.py`)
*   **Sécurité** : OAuth2 avec Password Flow.
*   **Token** : JWT (JSON Web Tokens) avec expiration.
*   **Hachage** : Passwords hachés avec `bcrypt`.
*   **Règles** : Validation stricte du domaine email (`@cerp-rouen.fr`) à l'inscription.

### 9. Cache (`modules/cache.py`)
*   **Type** : Cache en mémoire (LRU ou Simple Dict) ou Redis (extensible).
*   **Clé** : Hash de la requête utilisateur + ID conversation.
*   **Expiration** : TTL (Time To Live) pour rafraîchir les données.

### 10. Monitoring (`modules/monitoring.py`)
*   **Rôle** : Surveiller la santé et la performance.
*   **Métriques** : Temps de réponse, taux de succès, erreurs, utilisation des tokens.
*   **Logs** : Structurés pour faciliter le débogage.

---

## 📂 Structure des Dossiers Backend

```
PocChatbotM3/
├── backend_api.py       # Point d'entrée FastAPI (Routes API)
├── modules/             # Logique métier modulaire
│   ├── auth.py          # Authentification (JWT, Password Hashing)
│   ├── cache.py         # Mise en cache des réponses (Performance)
│   ├── embedding.py     # Vectorisation du texte (Text -> Nombres)
│   ├── generation.py    # Interaction LLM (Prompting, Réécriture)
│   ├── ingestion.py     # Lecture et extraction des PDF
│   ├── monitoring.py    # Logs et métriques de santé
│   ├── preprocessing.py # Découpage (Chunking) et nettoyage
│   ├── reranking.py     # Réordonnancement précis des résultats (Cross-Encoder)
│   ├── retriever.py     # Recherche sémantique dans l'index
│   ├── session.py       # Gestion historique, conversations et feedbacks
│   └── vector_store.py  # Gestion de l'index FAISS (Stockage vecteurs)
├── utils/               # Utilitaires transverses
│   ├── config.py        # Configuration (Clés API, Chemins)
│   ├── database.py      # Modèles DB (SQLAlchemy)
├── inputs/              # Dossier des documents sources (PDF)
├── vector_db/           # Stockage de l'index FAISS
└── requirements.txt     # Dépendances Python
```
