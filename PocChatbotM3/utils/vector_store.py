

# utils/vector_store.py
import os
import pickle
import faiss
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from mistralai.client import MistralClient
from mistralai.exceptions import MistralAPIException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .config import (
    MISTRAL_API_KEY, EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE,
    FAISS_INDEX_FILE, DOCUMENT_CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VectorStoreManager:
    """Gère la création, le chargement et la recherche dans un index Faiss, avec post-traitement et diversification."""

    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.document_chunks: List[Dict[str, any]] = []
        self.mistral_client = MistralClient(api_key=MISTRAL_API_KEY) if MISTRAL_API_KEY else None
        
        # Mappage pour la récupération rapide des voisins (essentiel pour le RAG avancé)
        self._chunk_map_by_source: Dict[str, List[Dict]] = {} 
        
        self._load_index_and_chunks()
        self._build_chunk_map() 

    def _load_index_and_chunks(self):
        """Charge l'index Faiss et les chunks si les fichiers existent."""
        if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE):
            try:
                logging.info(f"Chargement de l'index Faiss depuis {FAISS_INDEX_FILE}...")
                self.index = faiss.read_index(FAISS_INDEX_FILE)
                logging.info(f"Chargement des chunks depuis {DOCUMENT_CHUNKS_FILE}...")
                with open(DOCUMENT_CHUNKS_FILE, 'rb') as f:
                    self.document_chunks = pickle.load(f)
                logging.info(f"Index ({self.index.ntotal} vecteurs) et {len(self.document_chunks)} chunks chargés.")
            except Exception as e:
                logging.error(f"Erreur lors du chargement de l'index/chunks: {e}")
                self.index = None
                self.document_chunks = []
        else:
            logging.warning("Fichiers d'index Faiss ou de chunks non trouvés. L'index est vide.")

    def _build_chunk_map(self):
        """
        Construit un mappage des chunks par source (document) et par ID dans le document.
        Ceci est essentiel pour la récupération des voisins.
        """
        self._chunk_map_by_source = {}
        for i, chunk in enumerate(self.document_chunks):
            source = chunk["metadata"].get("source")
            chunk_id_in_doc = chunk["metadata"].get("chunk_id_in_doc")
            
            if source and chunk_id_in_doc is not None:
                if source not in self._chunk_map_by_source:
                    self._chunk_map_by_source[source] = []
                
                # Stocke l'index global (i) et l'index local (chunk_id_in_doc)
                self._chunk_map_by_source[source].append({
                    "global_index": i,
                    "local_id": chunk_id_in_doc,
                    "chunk": chunk # Référence au chunk complet
                })
        
        # Trier chaque liste par l'ID local pour s'assurer que les voisins sont adjacents
        for source in self._chunk_map_by_source:
            self._chunk_map_by_source[source].sort(key=lambda x: x["local_id"])
        
        if self.document_chunks:
             logging.info(f"Mappage créé pour {len(self.document_chunks)} chunks dans {len(self._chunk_map_by_source)} documents.")

    def _split_documents_to_chunks(self, documents: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Découpe les documents en chunks avec métadonnées."""
        logging.info(f"Découpage de {len(documents)} documents en chunks (taille={CHUNK_SIZE}, chevauchement={CHUNK_OVERLAP})...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            add_start_index=True,
        )

        all_chunks = []
        doc_counter = 0
        for doc in documents:
            langchain_doc = Document(page_content=doc["page_content"], metadata=doc["metadata"])
            chunks = text_splitter.split_documents([langchain_doc])
            logging.info(f"  Document '{doc['metadata'].get('filename', 'N/A')}' découpé en {len(chunks)} chunks.")

            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "id": f"{doc_counter}_{i}",
                    "text": chunk.page_content,
                    "metadata": {
                        **chunk.metadata,
                        "chunk_id_in_doc": i, # Position du chunk dans son document d'origine
                        "start_index": chunk.metadata.get("start_index", -1)
                    }
                }
                all_chunks.append(chunk_dict)
            doc_counter += 1

        logging.info(f"Total de {len(all_chunks)} chunks créés.")
        return all_chunks

    def _generate_embeddings(self, chunks: List[Dict[str, any]]) -> Optional[np.ndarray]:
        """Génère les embeddings pour une liste de chunks via l'API Mistral."""
        if not self.mistral_client:
            logging.error("Impossible de générer les embeddings: MISTRAL_API_KEY manquante.")
            return None
        if not chunks:
            logging.warning("Aucun chunk fourni pour générer les embeddings.")
            return None

        logging.info(f"Génération des embeddings pour {len(chunks)} chunks (modèle: {EMBEDDING_MODEL})...")
        all_embeddings = []
        total_batches = (len(chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

        for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
            batch_chunks = chunks[i:i + EMBEDDING_BATCH_SIZE]
            texts_to_embed = [chunk["text"] for chunk in batch_chunks]

            logging.info(f"  Traitement du lot {batch_num}/{total_batches} ({len(texts_to_embed)} chunks)")
            try:
                response = self.mistral_client.embeddings(
                    model=EMBEDDING_MODEL,
                    input=texts_to_embed
                )
                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)
            except MistralAPIException as e:
                logging.error(f"Erreur API Mistral lors de la génération d'embeddings (lot {batch_num}): {e}")
                dim = len(all_embeddings[0]) if all_embeddings else 1024
                num_failed = len(texts_to_embed)
                logging.warning(f"Ajout de {num_failed} vecteurs nuls de dimension {dim} pour le lot échoué.")
                all_embeddings.extend([np.zeros(dim, dtype='float32')] * num_failed)
            except Exception as e:
                logging.error(f"Erreur inattendue lors de la génération d'embeddings (lot {batch_num}): {e}")
                dim = len(all_embeddings[0]) if all_embeddings else 1024
                num_failed = len(texts_to_embed)
                logging.warning(f"Ajout de {num_failed} vecteurs nuls de dimension {dim} pour le lot échoué.")
                all_embeddings.extend([np.zeros(dim, dtype='float32')] * num_failed)


        if not all_embeddings:
             logging.error("Aucun embedding n'a pu être généré.")
             return None

        embeddings_array = np.array(all_embeddings).astype('float32')
        logging.info(f"Embeddings générés avec succès. Shape: {embeddings_array.shape}")
        return embeddings_array

    def build_index(self, documents: List[Dict[str, any]]):
        """Construit l'index Faiss à partir des documents."""
        if not documents:
            logging.warning("Aucun document fourni pour construire l'index.")
            return

        # 1. Découper en chunks
        self.document_chunks = self._split_documents_to_chunks(documents)
        if not self.document_chunks:
            logging.error("Le découpage n'a produit aucun chunk. Impossible de construire l'index.")
            return

        # 2. Générer les embeddings
        embeddings = self._generate_embeddings(self.document_chunks)
        if embeddings is None or embeddings.shape[0] != len(self.document_chunks):
            logging.error("Problème de génération d'embeddings. Nettoyage.")
            self.document_chunks = []
            self.index = None
            if os.path.exists(FAISS_INDEX_FILE): os.remove(FAISS_INDEX_FILE)
            if os.path.exists(DOCUMENT_CHUNKS_FILE): os.remove(DOCUMENT_CHUNKS_FILE)
            return

        # 3. Créer l'index Faiss
        dimension = embeddings.shape[1]
        logging.info(f"Création de l'index Faiss dimension {dimension}...")
        faiss.normalize_L2(embeddings)
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        logging.info(f"Index Faiss créé avec {self.index.ntotal} vecteurs.")

        # 4. Sauvegarder l'index et les chunks
        self._save_index_and_chunks()
        
        # 5. Reconstruire le mappage pour la recherche de voisins
        self._build_chunk_map()


    def _save_index_and_chunks(self):
        """Sauvegarde l'index Faiss et la liste des chunks."""
        if self.index is None or not self.document_chunks:
            logging.warning("Tentative de sauvegarde d'un index ou de chunks vides.")
            return

        os.makedirs(os.path.dirname(FAISS_INDEX_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(DOCUMENT_CHUNKS_FILE), exist_ok=True)

        try:
            faiss.write_index(self.index, FAISS_INDEX_FILE)
            with open(DOCUMENT_CHUNKS_FILE, 'wb') as f:
                pickle.dump(self.document_chunks, f)
            logging.info("Index et chunks sauvegardés avec succès.")
        except Exception as e:
            logging.error(f"Erreur lors de la sauvegarde de l'index/chunks: {e}")

    def _get_adjacent_chunks(self, source_path: str, local_id: int, num_neighbors: int = 1) -> List[Dict[str, any]]:
        """
        Récupère les chunks adjacents au chunk principal pour étendre le contexte (Post-traitement du Contexte).
        """
        if source_path not in self._chunk_map_by_source:
            return []

        document_chunks_meta = self._chunk_map_by_source[source_path]
        
        main_index_in_list = -1
        for i, meta in enumerate(document_chunks_meta):
            if meta["local_id"] == local_id:
                main_index_in_list = i
                break
        
        if main_index_in_list == -1:
            return []

        adjacent_chunks = []
        
        start_index = max(0, main_index_in_list - num_neighbors)
        end_index = min(len(document_chunks_meta), main_index_in_list + num_neighbors + 1)

        for i in range(start_index, end_index):
            if i != main_index_in_list:
                adjacent_chunks.append(document_chunks_meta[i]["chunk"])
                
        return adjacent_chunks

    def search(self, query_text: str, k: int = 5, min_score: float = None) -> List[Dict[str, any]]:
        """
        Recherche les k chunks les plus pertinents, enrichit le contexte avec les voisins,
        et applique une diversification des sources (Re-Ranking heuristique).

        Args:
            query_text: Texte de la requête (potentiellement réécrit)
            k: Nombre final de résultats à retourner
            min_score: Score minimum (entre 0 et 1) pour inclure un résultat
        
        Returns:
            Liste des chunks pertinents et enrichis avec leurs scores
        """
        if self.index is None or not self.document_chunks or not self.mistral_client:
            logging.warning("Recherche impossible: Index vide ou clé API manquante.")
            return []

        # 1. Générer l'embedding de la requête
        try:
            response = self.mistral_client.embeddings(
                model=EMBEDDING_MODEL,
                input=[query_text]
            )
            query_embedding = np.array([response.data[0].embedding]).astype('float32')
            faiss.normalize_L2(query_embedding)
        except Exception as e:
            logging.error(f"Erreur API Mistral lors de l'embedding de la requête: {e}")
            return []

        # 2. Rechercher un nombre très large de documents (20 candidats pour le re-ranking)
        search_k = 20
        scores, indices = self.index.search(query_embedding, search_k)

        # 3. Traiter et enrichir les résultats (Post-traitement du Contexte)
        
        final_results_map: Dict[str, Dict[str, any]] = {} 
        seen_chunk_ids = set() 
        min_score_percent = (min_score or 0) * 100

        if indices.size > 0:
            for i, idx in enumerate(indices[0]):
                
                # Limite de sécurité pour éviter trop de chunks avant le Re-Ranking final
                if len(final_results_map) >= search_k: 
                    break
                
                if 0 <= idx < len(self.document_chunks):
                    chunk = self.document_chunks[idx]
                    chunk_id = chunk["id"]
                    raw_score = float(scores[0][i])
                    similarity = raw_score * 100
                    
                    if similarity >= min_score_percent and chunk_id not in seen_chunk_ids:
                        
                        source_path = chunk["metadata"].get("source")
                        local_id = chunk["metadata"].get("chunk_id_in_doc")

                        # --- AJOUTER LE CHUNK PRINCIPAL ---
                        result_chunk = {
                            "score": similarity,
                            "raw_score": raw_score,
                            "text": chunk["text"],
                            "metadata": chunk["metadata"]
                        }
                        final_results_map[chunk_id] = result_chunk
                        seen_chunk_ids.add(chunk_id)
                        
                        # 3.2. Récupérer et ajouter les chunks voisins (Post-Processing)
                        if source_path and local_id is not None:
                            adjacent_chunks = self._get_adjacent_chunks(source_path, local_id, num_neighbors=1)
                            for adj_chunk in adjacent_chunks:
                                adj_chunk_id = adj_chunk["id"]
                                
                                if adj_chunk_id not in seen_chunk_ids:
                                    adj_result = {
                                        "score": similarity * 0.9, # Score ajusté pour prioriser le chunk principal
                                        "raw_score": raw_score * 0.9,
                                        "text": adj_chunk["text"],
                                        "metadata": {
                                            **adj_chunk["metadata"],
                                            "context_type": "neighbor" 
                                        }
                                    }
                                    final_results_map[adj_chunk_id] = adj_result
                                    seen_chunk_ids.add(adj_chunk_id)

        # 4. Finaliser les résultats avec diversification (Re-Ranking heuristique)
        
        results = list(final_results_map.values())
        results.sort(key=lambda x: x["score"], reverse=True)

        final_k_results = []
        seen_sources = set()

        for result in results:
            if len(final_k_results) >= k:
                break

            source_key = result['metadata'].get('source')
            is_neighbor = result['metadata'].get('context_type') == 'neighbor'

            # Logique de Re-Ranking Heuristique: Prioriser les chunks provenant de nouvelles sources (diversité)
            # Nous ajoutons un voisin même si sa source est la même, car il enrichit le contexte du chunk principal.
            if source_key not in seen_sources or is_neighbor:
                final_k_results.append(result)
                # Marquer la source comme vue si c'est le chunk principal (le plus pertinent)
                if not is_neighbor:
                     seen_sources.add(source_key)
            
        logging.info(f"{len(final_k_results)} chunks finaux trouvés (k={k}) après post-traitement et diversification.")

        return final_k_results