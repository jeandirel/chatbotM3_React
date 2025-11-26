# evaluate.py
import pandas as pd
import logging
from modules.session import SessionService
from utils.config import COMMUNE_NAME
from datetime import datetime, timedelta

# Initialize SessionService
session_service = SessionService()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data_for_evaluation(limit: int = 500) -> pd.DataFrame:
    """Charge toutes les interactions nécessaires depuis la base de données."""
    interactions = session_service.get_all_interactions(limit=limit)
    if not interactions:
        logging.warning("Aucune interaction trouvée dans la base de données.")
        return pd.DataFrame()

    df = pd.DataFrame(interactions)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Assurer que 'metadata' est la colonne utilisée (elle contient les données RAG avancées)
    if 'query_metadata' in df.columns:
        df['metadata'] = df['query_metadata']
    
    return df

def analyze_rereading_effectiveness(df: pd.DataFrame):
    """Analyse l'efficacité de la réécriture de requête (Query Re-writing)."""
    rewritten_df = df[df['metadata'].apply(lambda x: x.get('rewrite_history_used', False))]
    
    if rewritten_df.empty:
        print("\n--- Efficacité de la Réécriture de Requête ---")
        print("Aucune requête n'a utilisé la réécriture (RAG Conversationnel).")
        return

    total_rewritten = len(rewritten_df)
    
    # Compter les feedbacks positifs/négatifs spécifiquement pour les requêtes réécrites
    positive_fb = rewritten_df[rewritten_df['feedback'] == 'positif']
    negative_fb = rewritten_df[rewritten_df['feedback'] == 'négatif']
    
    total_fb_rewritten = len(positive_fb) + len(negative_fb)

    print("\n--- Efficacité de la Réécriture de Requête (RAG Conversationnel) ---")
    print(f"Total des requêtes réécrites : {total_rewritten}")
    
    if total_fb_rewritten > 0:
        rate_success = len(positive_fb) / total_fb_rewritten * 100
        print(f"  Taux de Feedback Positif (sur requêtes réécrites) : {rate_success:.1f}%")
        print(f"  Total Feedbacks sur requêtes réécrites : {total_fb_rewritten}")
    else:
        print("  Pas assez de feedback pour évaluer la performance de la réécriture.")

def analyze_feedback_per_mode(df: pd.DataFrame):
    """Analyse les feedbacks en fonction du mode de réponse (RAG vs DIRECT)."""
    
    df['mode'] = df['metadata'].apply(lambda x: x.get('mode', 'INCONNU'))
    feedback_df = df[df['feedback'].isin(['positif', 'négatif'])]
    
    if feedback_df.empty:
        print("\n--- Performance RAG vs DIRECT ---")
        print("Aucun feedback enregistré pour cette analyse.")
        return

    mode_performance = feedback_df.groupby('mode')['feedback'].value_counts().unstack(fill_value=0)
    
    if mode_performance.empty:
        print("\n--- Performance RAG vs DIRECT ---")
        print("Aucun feedback utilisable.")
        return

    mode_performance['Total Feedback'] = mode_performance.sum(axis=1)
    
    if 'positif' in mode_performance.columns:
        mode_performance['Taux de Succès (%)'] = (mode_performance['positif'] / mode_performance['Total Feedback']) * 100
    
    print("\n--- Performance RAG vs DIRECT (Basé sur le Feedback) ---")
    print(mode_performance.to_markdown(floatfmt=".1f"))
    
    # Identifier les échecs RAG (Direct mode activé par erreur)
    rag_attempts = df[df['mode'] == 'RAG']
    rag_failures = rag_attempts[rag_attempts['feedback'] == 'négatif']
    
    if not rag_failures.empty:
        print("\n--- Echecs RAG (Requêtes ayant reçu un '👎' en mode RAG) ---")
        print(rag_failures[['query', 'response', 'feedback_comment']].head(3).to_markdown())


def analyze_general_metrics(df: pd.DataFrame):
    """Calcule et affiche les métriques de base du système."""
    
    total_interactions = len(df)
    total_feedback = len(df[df['feedback'].isin(['positif', 'négatif'])])
    
    if total_interactions == 0:
        print("Aucune interaction à analyser.")
        return

    feedback_rate = total_feedback / total_interactions * 100
    
    print("\n=======================================================")
    print(f"         Analyse de Performance du Chatbot {COMMUNE_NAME}      ")
    print("=======================================================")
    print(f"  1. Total des Interactions Analysées : {total_interactions}")
    print(f"  2. Taux de Feedback Utilisateur : {feedback_rate:.1f}%")

    if total_feedback > 0:
        positive_count = len(df[df['feedback'] == 'positif'])
        overall_success_rate = positive_count / total_feedback * 100
        print(f"  3. Taux de Succès Global (sur Feedback) : {overall_success_rate:.1f}%")
    
    print("=======================================================")


def main_evaluation():
    """Fonction principale du script d'évaluation."""
    df = load_data_for_evaluation()
    
    if df.empty:
        return

    analyze_general_metrics(df)
    analyze_rereading_effectiveness(df)
    analyze_feedback_per_mode(df)


if __name__ == "__main__":
    main_evaluation()