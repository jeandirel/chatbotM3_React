# # pages/1_Feedback_Viewer.py
# import streamlit as st
# import pandas as pd
# import numpy as np
# import logging
# import sys
# import os
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, timedelta

# # Ajouter le dossier parent au chemin de recherche des modules Python
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# # Maintenant, nous pouvons importer les modules du dossier parent
# from utils.database import get_all_interactions

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# st.set_page_config(
#     page_title="Visionneur de Feedbacks Multi-Utilisateurs",
#     page_icon="📊",
#     layout="wide"
# )

# # =============================================================================
# # CSS PERSONNALISÉ (CONSERVÉ INTÉGRALEMENT DE L'APP PRINCIPALE)
# # =============================================================================

# custom_css = """
# <style>
# /* Couleurs générales */
# body {
#     background-color: #fff9f3;
#     color: #333333;
#     font-family: 'Segoe UI', sans-serif;
# }

# /* Header, boutons orange */
# header, .st-emotion-cache-18ni7ap, .st-emotion-cache-6qob1r {
#     background-color: #ffa94d !important;
#     color: white !important;
# }

# .stButton>button {
#     background-color: #ffa94d;
#     color: white;
#     border-radius: 8px;
#     font-weight: bold;
#     border: none;
#     padding: 6px 14px;
#     transition: background-color 0.3s ease;
# }

# .stButton>button:hover {
#     background-color: #ff922b;
#     color: white;
# }

# /* Boutons PDF spéciaux */
# .stButton>button[title*="Voir PDF"] {
#     background-color: #FF6B35;
#     color: white;
#     border: 2px solid #FF6B35;
# }

# .stButton>button[title*="Fermer PDF"] {
#     background-color: #dc3545;
#     color: white;
#     border: 2px solid #dc3545;
# }

# .stButton>button[title*="Voir PDF"]:hover {
#     background-color: #E55A2B;
#     border-color: #E55A2B;
# }

# .stButton>button[title*="Fermer PDF"]:hover {
#     background-color: #c82333;
#     border-color: #c82333;
# }

# /* Input et zone texte */
# input, textarea {
#     border-radius: 6px !important;
#     border: 1px solid #ffa94d !important;
#     padding: 6px;
# }

# /* Zone de chat input */
# .stChatInputContainer {
#     border: 2px solid #ffa94d !important;
#     border-radius: 10px !important;
#     background-color: #fff !important;
# }

# /* Expander titre */
# .stExpanderHeader {
#     background-color: #ffe8cc !important;
#     color: #ff6600 !important;
#     font-weight: bold;
#     border-radius: 5px;
# }

# /* Chat bubbles */
# .stChatMessage {
#     background-color: #fff3e0 !important;
#     border-radius: 10px;
#     padding: 10px;
#     margin-bottom: 10px;
#     border: 1px solid #ffe8cc;
# }

# /* Messages utilisateur */
# [data-testid="user-message"] {
#     background-color: #e3f2fd !important;
#     border-left: 4px solid #2196f3 !important;
# }

# /* Messages assistant */
# [data-testid="assistant-message"] {
#     background-color: #fff3e0 !important;
#     border-left: 4px solid #ffa94d !important;
# }

# /* Barre latérale */
# section[data-testid="stSidebar"] {
#     background-color: #fff3e0;
#     border-right: 2px solid #ffa94d;
# }

# .css-1d391kg {
#     background-color: #fff3e0;
# }

# /* Download button */
# [data-testid="baseButton-secondary"] {
#     border: 1px solid #ffa94d !important;
#     color: #ff6600 !important;
#     background: white;
# }

# [data-testid="baseButton-secondary"]:hover {
#     background: #ffe8cc;
# }

# /* Styles pour les containers PDF */
# .pdf-container {
#     border: 3px solid #FF6B35;
#     border-radius: 10px;
#     padding: 15px;
#     margin: 15px 0;
#     background-color: #FFF8F0;
#     box-shadow: 0 4px 6px rgba(255, 107, 53, 0.1);
# }

# .pdf-header {
#     color: #FF6B35;
#     margin-top: 0;
#     font-size: 1.2em;
#     font-weight: bold;
# }

# /* Titre principal */
# .main-title {
#     color: #ff6600;
#     text-align: center;
#     padding: 20px 0;
# }

# /* Messages d'info */
# .stInfo {
#     background-color: #e8f4fd !important;
#     border-left: 4px solid #2196f3 !important;
#     color: #0c5aa6 !important;
# }

# /* Messages de succès */
# .stSuccess {
#     background-color: #e8f5e8 !important;
#     border-left: 4px solid #4caf50 !important;
#     color: #2e7d32 !important;
# }

# /* Spinner/Loading */
# .stSpinner {
#     color: #ffa94d !important;
# }

# /* Sliders */
# .stSlider > div > div > div {
#     background-color: #ffa94d !important;
# }

# /* Select boxes */
# .stSelectbox > div > div {
#     border: 1px solid #ffa94d !important;
#     border-radius: 6px !important;
# }

# /* Métriques personnalisées */
# .metric-container {
#     background-color: #fff3e0;
#     border: 2px solid #ffa94d;
#     border-radius: 10px;
#     padding: 15px;
#     text-align: center;
# }

# .metric-value {
#     font-size: 2em;
#     font-weight: bold;
#     color: #ff6600;
# }

# .metric-label {
#     color: #666;
#     font-size: 0.9em;
# }
# </style>
# """

# st.markdown(custom_css, unsafe_allow_html=True)

# # =============================================================================
# # FONCTIONS UTILITAIRES POUR MULTI-UTILISATEURS
# # =============================================================================

# def extract_user_sessions_from_metadata(df):
#     """
#     Extrait les IDs de session utilisateur des métadonnées.
#     Retourne une liste d'IDs de session uniques.
#     """
#     user_sessions = set()
    
#     for _, row in df.iterrows():
#         metadata = row.get('metadata')
#         if metadata and isinstance(metadata, dict):
#             user_session_id = metadata.get('user_session_id')
#             if user_session_id:
#                 user_sessions.add(user_session_id)
    
#     return sorted(list(user_sessions))

# def filter_dataframe_by_user_session(df, user_session_id):
#     """
#     Filtre le DataFrame pour ne garder que les interactions d'un utilisateur spécifique.
#     """
#     if user_session_id == "Tous les utilisateurs":
#         return df
    
#     filtered_rows = []
#     for _, row in df.iterrows():
#         metadata = row.get('metadata')
#         if metadata and isinstance(metadata, dict):
#             if metadata.get('user_session_id') == user_session_id:
#                 filtered_rows.append(row)
    
#     if filtered_rows:
#         return pd.DataFrame(filtered_rows)
#     else:
#         return pd.DataFrame()

# def format_user_session_id(user_session_id):
#     """
#     Formate l'ID de session utilisateur pour l'affichage.
#     Affiche seulement les 12 premiers caractères + ... pour la lisibilité.
#     """
#     if len(user_session_id) > 12:
#         return f"{user_session_id[:12]}..."
#     return user_session_id

# # =============================================================================
# # TITRE ET INTERFACE PRINCIPALE
# # =============================================================================

# st.title("📊 Visionneur des Interactions et Feedbacks Multi-Utilisateurs")
# st.caption("Affiche les interactions enregistrées avec filtrage par session utilisateur.")

# # =============================================================================
# # SIDEBAR POUR LES FILTRES
# # =============================================================================

# with st.sidebar:
#     st.header("🔧 Filtres et Options")
    
#     # Bouton pour rafraîchir les données
#     if st.button("🔄 Rafraîchir les données", use_container_width=True):
#         st.cache_data.clear()  # Invalide le cache
#         st.rerun()
    
#     st.divider()
    
#     # Limiter le nombre d'interactions à charger
#     max_interactions = st.slider(
#         "Nombre maximum d'interactions à charger",
#         min_value=50,
#         max_value=1000,
#         value=200,
#         step=50
#     )
    
#     st.divider()
    
#     # Filtre par période
#     st.subheader("📅 Période")
#     period_filter = st.selectbox(
#         "Période d'analyse",
#         ["Toutes les périodes", "Dernières 24h", "Dernière semaine", "Dernier mois"]
#     )

# # =============================================================================
# # CHARGEMENT ET TRAITEMENT DES DONNÉES
# # =============================================================================

# @st.cache_data(ttl=60)
# def load_data(limit=200):
#     """
#     Charge les données depuis la base avec gestion multi-utilisateurs.
#     """
#     logging.info(f"Chargement des {limit} dernières interactions depuis la base de données...")
#     interactions_list = get_all_interactions(limit=limit)
    
#     if not interactions_list:
#         return pd.DataFrame(), pd.DataFrame()

#     # Convertir en DataFrame
#     df = pd.DataFrame(interactions_list)

#     # Traitement des données
#     df['timestamp'] = pd.to_datetime(df['timestamp'])
#     df = df.sort_values(by='timestamp', ascending=False)
    
#     # Extraire l'ID de session depuis les métadonnées pour l'affichage
#     df['user_session_display'] = df['metadata'].apply(
#         lambda x: format_user_session_id(x.get('user_session_id', 'N/A')) 
#         if isinstance(x, dict) and x.get('user_session_id') 
#         else 'N/A'
#     )
    
#     # Créer le DataFrame d'affichage
#     df_display = df[[
#         'timestamp',
#         'user_session_display',
#         'query',
#         'response',
#         'feedback',
#         'feedback_comment',
#         'id',
#         'sources',
#         'metadata'
#     ]].rename(columns={
#         'timestamp': 'Date & Heure (UTC)',
#         'user_session_display': 'ID Session',
#         'query': 'Question Utilisateur',
#         'response': 'Réponse Assistant',
#         'feedback': 'Feedback',
#         'feedback_comment': 'Commentaire',
#         'id': 'ID Interaction',
#         'metadata': 'Métadonnées'
#     })
    
#     return df_display, df

# # Charger les données
# try:
#     df_display, df_original = load_data(limit=max_interactions)

#     if df_display.empty:
#         st.warning("❌ Aucune interaction enregistrée dans la base de données pour le moment.")
#         st.stop()

#     # =============================================================================
#     # FILTRAGE PAR SESSION UTILISATEUR
#     # =============================================================================
    
#     # Extraire les sessions utilisateur
#     user_sessions = extract_user_sessions_from_metadata(df_original)
    
#     if user_sessions:
#         st.info(f"✅ {len(df_display)} interactions trouvées de {len(user_sessions)} utilisateurs différents.")
        
#         # Sélecteur de session utilisateur
#         session_options = ["Tous les utilisateurs"] + user_sessions
#         selected_session = st.selectbox(
#             "🔍 Filtrer par session utilisateur:",
#             options=session_options,
#             format_func=lambda x: f"Tous les utilisateurs ({len(user_sessions)} sessions)" if x == "Tous les utilisateurs" 
#                                   else f"Utilisateur {format_user_session_id(x)}"
#         )
        
#         # Appliquer le filtre
#         if selected_session != "Tous les utilisateurs":
#             df_filtered = filter_dataframe_by_user_session(df_original, selected_session)
#             df_display_filtered = filter_dataframe_by_user_session(df_display, selected_session)
            
#             if df_filtered.empty:
#                 st.warning(f"❌ Aucune interaction trouvée pour l'utilisateur {format_user_session_id(selected_session)}")
#                 st.stop()
#             else:
#                 st.success(f"🎯 Affichage des {len(df_filtered)} interactions de l'utilisateur {format_user_session_id(selected_session)}")
#         else:
#             df_filtered = df_original
#             df_display_filtered = df_display
            
#         # Filtrage par période
#         if period_filter != "Toutes les périodes":
#             now = datetime.now()
#             if period_filter == "Dernières 24h":
#                 start_date = now - timedelta(days=1)
#             elif period_filter == "Dernière semaine":
#                 start_date = now - timedelta(weeks=1)
#             elif period_filter == "Dernier mois":
#                 start_date = now - timedelta(days=30)
            
#             df_filtered = df_filtered[df_filtered['timestamp'] >= start_date]
#             df_display_filtered = df_display_filtered[df_display_filtered['Date & Heure (UTC)'] >= start_date]
            
#             if not df_filtered.empty:
#                 st.info(f"📅 Période sélectionnée: {period_filter} ({len(df_filtered)} interactions)")
#     else:
#         st.warning("⚠️ Aucune information de session utilisateur trouvée dans les métadonnées.")
#         df_filtered = df_original
#         df_display_filtered = df_display

#     # =============================================================================
#     # ONGLETS PRINCIPAUX
#     # =============================================================================
    
#     tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "👥 Vue par Utilisateur", "📃 Données Brutes"])

#     # =============================================================================
#     # ONGLET 1: STATISTIQUES GLOBALES
#     # =============================================================================
    
#     with tab1:
#         st.subheader("📊 Statistiques des feedbacks")

#         # Calculer les statistiques de feedback
#         if 'feedback_value' in df_filtered.columns:
#             feedback_values = df_filtered['feedback_value'].dropna()
#         else:
#             feedback_values = df_filtered['feedback'].apply(
#                 lambda x: 1 if x == "positif" else 0 if x == "négatif" else None
#             ).dropna()

#         if len(feedback_values) > 0:
#             positive_count = sum(feedback_values == 1)
#             negative_count = sum(feedback_values == 0)
#             total_feedback = len(feedback_values)
#             total_interactions = len(df_filtered)
            
#             positive_percent = (positive_count / total_feedback * 100) if total_feedback > 0 else 0
#             negative_percent = (negative_count / total_feedback * 100) if total_feedback > 0 else 0
#             feedback_rate = (total_feedback / total_interactions * 100) if total_interactions > 0 else 0

#             # Métriques principales
#             col1, col2, col3, col4 = st.columns(4)
#             with col1:
#                 st.metric("Total interactions", total_interactions)
#             with col2:
#                 st.metric("Taux de feedback", f"{feedback_rate:.1f}%", f"{total_feedback}/{total_interactions}")
#             with col3:
#                 st.metric("👍 Positifs", positive_count, f"{positive_percent:.1f}%")
#             with col4:
#                 st.metric("👎 Négatifs", negative_count, f"{negative_percent:.1f}%")

#             # Graphique en barres des feedbacks
#             feedback_data = pd.DataFrame({
#                 'Type': ['👍 Positif', '👎 Négatif'],
#                 'Nombre': [positive_count, negative_count]
#             })

#             fig = px.bar(
#                 feedback_data,
#                 x='Type',
#                 y='Nombre',
#                 color='Type',
#                 color_discrete_map={'👍 Positif': '#00CC96', '👎 Négatif': '#EF553B'},
#                 title="Répartition des feedbacks"
#             )
#             fig.update_traces(texttemplate='%{y}', textposition='outside')
#             st.plotly_chart(fig, use_container_width=True)

#             # Statistiques par mode (RAG vs Direct)
#             if 'metadata' in df_filtered.columns:
#                 mode_stats = []
#                 for _, row in df_filtered.iterrows():
#                     metadata = row.get('metadata')
#                     if metadata and isinstance(metadata, dict):
#                         mode = metadata.get('mode', 'N/A')
#                         feedback = row.get('feedback')
#                         if feedback in ['positif', 'négatif']:
#                             mode_stats.append({'mode': mode, 'feedback': feedback})
                
#                 if mode_stats:
#                     mode_df = pd.DataFrame(mode_stats)
#                     mode_summary = mode_df.groupby(['mode', 'feedback']).size().unstack(fill_value=0)
                    
#                     if not mode_summary.empty:
#                         st.subheader("📈 Performance par mode")
#                         fig_mode = px.bar(
#                             mode_summary.reset_index(),
#                             x='mode',
#                             y=['positif', 'négatif'],
#                             title="Feedbacks par mode (RAG vs Direct)",
#                             color_discrete_map={'positif': '#00CC96', 'négatif': '#EF553B'}
#                         )
#                         st.plotly_chart(fig_mode, use_container_width=True)

#             # Évolution temporelle si assez de données
#             if len(df_filtered) >= 5:
#                 st.subheader("📈 Évolution des feedbacks dans le temps")
                
#                 df_filtered_copy = df_filtered.copy()
#                 df_filtered_copy['date'] = df_filtered_copy['timestamp'].dt.date
                
#                 feedback_by_date = df_filtered_copy.groupby('date').apply(
#                     lambda x: pd.Series({
#                         'positif': sum(x['feedback'] == "positif"),
#                         'négatif': sum(x['feedback'] == "négatif"),
#                         'total': len(x)
#                     })
#                 ).reset_index()

#                 fig2 = go.Figure()
#                 fig2.add_trace(go.Scatter(
#                     x=feedback_by_date['date'],
#                     y=feedback_by_date['positif'],
#                     mode='lines+markers',
#                     name='👍 Positifs',
#                     line=dict(color='#00CC96', width=2),
#                     marker=dict(size=8)
#                 ))
#                 fig2.add_trace(go.Scatter(
#                     x=feedback_by_date['date'],
#                     y=feedback_by_date['négatif'],
#                     mode='lines+markers',
#                     name='👎 Négatifs',
#                     line=dict(color='#EF553B', width=2),
#                     marker=dict(size=8)
#                 ))
#                 fig2.update_layout(
#                     title="Évolution des feedbacks par jour",
#                     xaxis_title="Date",
#                     yaxis_title="Nombre de feedbacks"
#                 )
#                 st.plotly_chart(fig2, use_container_width=True)
#         else:
#             st.info("ℹ️ Aucun feedback n'a encore été donné pour la sélection actuelle.")

#     # =============================================================================
#     # ONGLET 2: VUE PAR UTILISATEUR
#     # =============================================================================
    
#     with tab2:
#         st.subheader("👥 Statistiques par utilisateur")
        
#         if user_sessions and len(user_sessions) > 1:
#             user_stats = []
            
#             for user_session in user_sessions:
#                 user_data = filter_dataframe_by_user_session(df_original, user_session)
                
#                 if not user_data.empty:
#                     total_interactions = len(user_data)
                    
#                     # Compter les feedbacks
#                     positive_feedback = sum(user_data['feedback'] == "positif")
#                     negative_feedback = sum(user_data['feedback'] == "négatif")
#                     total_feedback = positive_feedback + negative_feedback
                    
#                     # Calculer les modes utilisés
#                     modes_used = []
#                     for _, row in user_data.iterrows():
#                         metadata = row.get('metadata')
#                         if metadata and isinstance(metadata, dict):
#                             mode = metadata.get('mode', 'N/A')
#                             modes_used.append(mode)
                    
#                     rag_count = modes_used.count('RAG')
#                     direct_count = modes_used.count('DIRECT')
                    
#                     user_stats.append({
#                         'Session': format_user_session_id(user_session),
#                         'Session_ID': user_session,
#                         'Interactions': total_interactions,
#                         'Feedbacks': total_feedback,
#                         '👍 Positifs': positive_feedback,
#                         '👎 Négatifs': negative_feedback,
#                         'Taux feedback (%)': (total_feedback/total_interactions*100) if total_interactions > 0 else 0,
#                         'Mode RAG': rag_count,
#                         'Mode Direct': direct_count,
#                         'Dernière activité': user_data['timestamp'].max().strftime('%Y-%m-%d %H:%M')
#                     })
            
#             if user_stats:
#                 stats_df = pd.DataFrame(user_stats)
#                 stats_df = stats_df.sort_values('Interactions', ascending=False)
                
#                 st.dataframe(
#                     stats_df.drop('Session_ID', axis=1),  # Cacher l'ID complet
#                     use_container_width=True,
#                     column_config={
#                         "Session": st.column_config.TextColumn("ID Session", width="medium"),
#                         "Interactions": st.column_config.NumberColumn("Total", width="small"),
#                         "Taux feedback (%)": st.column_config.NumberColumn("Taux (%)", width="small", format="%.1f"),
#                         "Dernière activité": st.column_config.TextColumn("Dernière activité", width="medium")
#                     }
#                 )
                
#                 # Graphique des interactions par utilisateur
#                 if len(stats_df) > 1:
#                     fig_users = px.bar(
#                         stats_df.head(10),  # Top 10 utilisateurs
#                         x='Session',
#                         y='Interactions',
#                         title="Top 10 des utilisateurs les plus actifs",
#                         color='Interactions',
#                         color_continuous_scale='Blues'
#                     )
#                     fig_users.update_xaxes(tickangle=45)
#                     st.plotly_chart(fig_users, use_container_width=True)
#         else:
#             st.info("ℹ️ Pas assez de sessions utilisateur pour afficher les statistiques comparatives.")

#     # =============================================================================
#     # ONGLET 3: DONNÉES BRUTES
#     # =============================================================================
    
#     with tab3:
#         st.subheader("📃 Données brutes")
        
#         # Ajouter des informations sur le filtrage actuel
#         if selected_session != "Tous les utilisateurs":
#             st.info(f"🔍 Données filtrées pour l'utilisateur: {format_user_session_id(selected_session)}")
        
#         if period_filter != "Toutes les périodes":
#             st.info(f"📅 Période: {period_filter}")
        
#         # Affichage du tableau
#         st.dataframe(
#             df_display_filtered,
#             use_container_width=True,
#             column_config={
#                 "Date & Heure (UTC)": st.column_config.DatetimeColumn(
#                     format="YYYY-MM-DD HH:mm:ss",
#                     width="small"
#                 ),
#                 "ID Session": st.column_config.TextColumn(
#                     width="small",
#                     help="Identifiant de la session utilisateur"
#                 ),
#                 "Question Utilisateur": st.column_config.TextColumn(width="medium"),
#                 "Réponse Assistant": st.column_config.TextColumn(width="large"),
#                 "Feedback": st.column_config.TextColumn(width="small"),
#                 "Commentaire": st.column_config.TextColumn(width="medium"),
#                 "ID Interaction": st.column_config.NumberColumn(width="small"),
#                 "Métadonnées": st.column_config.JsonColumn(width="medium")
#             },
#             hide_index=True
#         )

#         # Examiner une interaction spécifique
#         st.subheader("🔍 Examiner une interaction spécifique")
        
#         if not df_filtered.empty:
#             selected_id = st.selectbox(
#                 "Sélectionnez l'ID de l'interaction:",
#                 options=df_filtered['id'].tolist(),
#                 format_func=lambda x: f"ID {x} - {df_filtered[df_filtered['id']==x].iloc[0]['query'][:50]}..."
#             )

#             if selected_id:
#                 selected_interaction = df_filtered[df_filtered['id'] == selected_id].iloc[0]
                
#                 # Informations sur l'utilisateur
#                 metadata = selected_interaction['metadata']
#                 if metadata and isinstance(metadata, dict):
#                     user_session_id = metadata.get('user_session_id', 'N/A')
#                     st.info(f"👤 Session utilisateur: {format_user_session_id(user_session_id)}")
                
#                 st.write(f"**❓ Question:** {selected_interaction['query']}")
#                 st.write(f"**🤖 Réponse:** {selected_interaction['response']}")
                
#                 feedback = selected_interaction['feedback']
#                 feedback_comment = selected_interaction['feedback_comment']
#                 if feedback:
#                     emoji = "👍" if feedback == "positif" else "👎" if feedback == "négatif" else "❓"
#                     st.write(f"**{emoji} Feedback:** {feedback}")
#                     if feedback_comment:
#                         st.write(f"**💬 Commentaire:** {feedback_comment}")

#                 # Métadonnées détaillées
#                 if metadata and isinstance(metadata, dict):
#                     mode = metadata.get('mode', 'N/A')
#                     confidence = metadata.get('confidence', 0.0)
#                     reason = metadata.get('reason', 'N/A')
#                     st.write(f"**🔧 Mode:** {mode} (confiance: {confidence:.2f})")
#                     st.write(f"**📋 Raison:** {reason}")

#                 # Sources utilisées
#                 st.write("**📚 Sources utilisées lors de la génération:**")
#                 sources = selected_interaction['sources']
#                 if sources and isinstance(sources, list):
#                     for i, src in enumerate(sources):
#                         meta = src.get("metadata", {})
#                         with st.expander(f"Source {i+1}: `{meta.get('source', 'N/A')}` (Score: {src.get('score', 0.0):.4f})"):
#                             st.text(src.get('text', 'N/A')[:1000] + "..." if len(src.get('text', '')) > 1000 else src.get('text', 'N/A'))
#                 elif sources:
#                     st.json(sources)
#                 else:
#                     st.write("Aucune source enregistrée pour cette interaction.")

# except Exception as e:
#     logging.error(f"Erreur lors du chargement ou de l'affichage des données: {e}", exc_info=True)
#     st.error(f"❌ Une erreur est survenue lors de l'affichage des feedbacks: {e}")
#     st.write("**Détails de l'erreur:**")
#     st.code(str(e))



################################## mise à jours ###################################²from typing import Optional
############################################# code generé par gemini 2.5 pro ###############################
# pages/1_Feedback_Viewer.py
import streamlit as st
import pandas as pd
import numpy as np
import logging
import sys
import os
import base64
from pathlib import Path
from typing import Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Mot de passe administrateur (peut être surchargé via la variable d'environnement)
ADMIN_PASSWORD = os.environ.get("FEEDBACK_ADMIN_PASSWORD", "Admin1728")

# Ajouter le dossier parent au chemin de recherche des modules Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Maintenant, nous pouvons importer les modules du dossier parent
# from utils.database import get_all_interactions, update_feedback # REMOVED
from modules.session import SessionService # ADDED
session_service = SessionService() # ADDED

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.set_page_config(
    page_title="Admin",
    page_icon="📊",
    layout="wide"
)

# Injection JS (via components) pour renommer les labels de la sidebar
def _inject_sidebar_labels() -> None:
    urls = st.components.v1  # type: ignore[attr-defined]
    if not hasattr(urls, "html"):
        return
    urls.html(
        """
        <script>
        (function() {
          const renameMap = {"MistralChat": "Chat", "Feedback Viewer": "Admin"};
          const applyRename = () => {
            const sidebar = window.parent.document.querySelector('section[data-testid="stSidebar"]');
            if (!sidebar) return false;
            const labels = sidebar.querySelectorAll('a p');
            let changed = false;
            labels.forEach((p) => {
              const current = (p.innerText || "").trim();
              if (renameMap[current]) {
                p.innerText = renameMap[current];
                changed = true;
              }
            });
            return changed;
          };
          let attempts = 0;
          const iv = setInterval(() => {
            if (applyRename() || attempts > 30) clearInterval(iv);
            attempts += 1;
          }, 150);
        })();
        </script>
        """,
        height=0,
    )

_inject_sidebar_labels()

# =============================================================================
# CSS PERSONNALISÉ (Omis pour la concision - utiliser votre version complète)
# =============================================================================

custom_css = """
<style>
/* ... Votre CSS Complet ici ... */

/* Titre principal */
.main-title {
    color: #ff6600;
    text-align: center;
    padding: 20px 0;
}

/* Métriques personnalisées */
.metric-container {
    background-color: #fff3e0;
    border: 2px solid #ffa94d;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
}

/* ... (Reste de votre CSS) ... */

</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)


def _trigger_rerun() -> None:
    """Déclenche un rerun Streamlit compatible avec différentes versions."""
    rerun_callable = getattr(st, "rerun", None)
    if callable(rerun_callable):
        rerun_callable()
        return
    try:
        from streamlit.runtime.scriptrunner import RerunException, RerunData  # type: ignore
        raise RerunException(RerunData(None))  # type: ignore[call-arg]
    except Exception:
        pass


def require_admin_password() -> None:
    """Affiche un popup (ou fallback) pour sécuriser l'accès aux feedbacks."""
    if st.session_state.get("feedback_admin_authenticated"):
        return

    st.session_state.setdefault("feedback_admin_modal_open", True)
    st.session_state.setdefault("feedback_admin_error", "")

    def render_form() -> None:
        st.write("🔒 Cette section est réservée aux administrateurs.")
        st.write("Merci d'entrer le mot de passe pour accéder aux feedbacks.")

        password_input = st.text_input(
            "Mot de passe administrateur",
            type="password",
            key="feedback_admin_password_input",
        )

        if st.button("Valider", type="primary", key="feedback_admin_submit"):
            if password_input == ADMIN_PASSWORD:
                st.session_state["feedback_admin_authenticated"] = True
                st.session_state["feedback_admin_modal_open"] = False
                st.session_state.pop("feedback_admin_error", None)
                st.session_state.pop("feedback_admin_password_input", None)
                _trigger_rerun()
                return

            st.session_state["feedback_admin_error"] = "Mot de passe incorrect."

        error_message = st.session_state.get("feedback_admin_error")
        if error_message:
            st.error(error_message)

    def render_fallback() -> None:
        st.markdown(
            """
            <style>
                .admin-lock-wrapper {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 85vh;
                }
                .admin-lock-card {
                    background: var(--background-color);
                    padding: 2.5rem;
                    border-radius: 1rem;
                    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.25);
                    width: min(420px, 92%);
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        wrapper = st.container()
        with wrapper:
            st.markdown('<div class="admin-lock-wrapper">', unsafe_allow_html=True)
            left, center, right = st.columns([1, 2, 1])
            with center:
                st.markdown('<div class="admin-lock-card">', unsafe_allow_html=True)
                st.markdown("### Accès administrateur requis")
                render_form()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("feedback_admin_modal_open", True):
        dialog_fn = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
        if dialog_fn:
            modal_obj = dialog_fn("Accès administrateur requis")
            if hasattr(modal_obj, "__enter__") and hasattr(modal_obj, "__exit__"):
                with modal_obj:
                    render_form()
                if st.session_state.get("feedback_admin_modal_open", True):
                    st.stop()
                return
            if callable(modal_obj):

                @modal_obj
                def _admin_dialog():
                    render_form()

                _admin_dialog()
                if st.session_state.get("feedback_admin_modal_open", True):
                    st.stop()
                return

        render_fallback()
        st.stop()


require_admin_password()

# =============================================================================
# OUTILS PDF
# =============================================================================

DEFAULT_PDF_DIRECTORIES = [
    Path.cwd(),
    Path.cwd() / "inputs",
    Path.cwd() / "pages",
    Path.cwd() / "database"
]


def _sanitize_pdf_hint(raw_hint: str) -> Optional[str]:
    """Nettoie l'indication brute d'un PDF (suppression des fragments, paramètres, etc.)."""
    if not raw_hint:
        return None
    cleaned = raw_hint.split("::")[0].split("#")[0].split("?")[0].strip()
    return cleaned if cleaned.lower().endswith(".pdf") else None


def resolve_pdf_path(pdf_hint: Optional[str]) -> Optional[Path]:
    """Essaie de retrouver un fichier PDF à partir d'un indice."""
    if not pdf_hint:
        return None

    candidate = Path(pdf_hint)
    if candidate.is_file():
        return candidate

    pdf_name = candidate.name if candidate.name else None
    checked_paths = set()

    relative_candidates = []
    if not candidate.is_absolute():
        relative_candidates.append(Path.cwd() / candidate)

    for base_dir in DEFAULT_PDF_DIRECTORIES:
        relative_candidates.append(base_dir / candidate)
        if pdf_name:
            relative_candidates.append(base_dir / pdf_name)

    for path_candidate in relative_candidates:
        if path_candidate in checked_paths:
            continue
        checked_paths.add(path_candidate)
        if path_candidate.is_file():
            return path_candidate

    if pdf_name:
        for base_dir in DEFAULT_PDF_DIRECTORIES:
            if not base_dir.is_dir():
                continue
            try:
                found = next(base_dir.rglob(pdf_name))
                return found
            except StopIteration:
                continue

    return None


@st.cache_data(show_spinner=False)
def encode_pdf_to_base64(pdf_path: str) -> Optional[str]:
    """Charge un PDF et retourne sa version encodée en base64."""
    path = Path(pdf_path)
    with path.open("rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode("utf-8")


def extract_pdf_hint_from_source(source: dict) -> Optional[str]:
    """Récupère un indice de chemin vers un PDF à partir des métadonnées d'une source."""
    if not isinstance(source, dict):
        return None

    metadata = source.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    candidates = [
        metadata.get("source"),
        metadata.get("document_path"),
        metadata.get("file_path"),
        metadata.get("path"),
        metadata.get("file"),
        source.get("source"),
        source.get("path")
    ]

    for candidate in candidates:
        if isinstance(candidate, str):
            sanitized = _sanitize_pdf_hint(candidate)
            if sanitized:
                return sanitized

    return None


def show_pdf_modal_if_needed(state_key: str, pdf_path: Path, title: str) -> None:
    """Affiche un modal Streamlit contenant un PDF si l'état le demande."""
    if not st.session_state.get(state_key):
        return

    modal_title = f"📄 {title}"
    with st.modal(modal_title, key=f"modal_{state_key}"):
        try:
            pdf_b64 = encode_pdf_to_base64(str(pdf_path))
            st.markdown(
                f"""
                <div style="border: 1px solid #ffa94d; border-radius: 10px; overflow: hidden;">
                    <iframe src="data:application/pdf;base64,{pdf_b64}"
                            width="100%"
                            height="600"
                            style="border: none;">
                    </iframe>
                </div>
                """,
                unsafe_allow_html=True
            )
        except Exception as exc:
            logging.error(f"Erreur lors de l'ouverture du PDF '{pdf_path}': {exc}")
            st.error("Impossible d'afficher le PDF sélectionné. Vérifiez que le fichier est bien présent.")

        if st.button("Fermer", key=f"close_{state_key}"):
            st.session_state[state_key] = False
            st.experimental_rerun()

# =============================================================================
# FONCTIONS UTILITAIRES POUR MULTI-UTILISATEURS
# =============================================================================

def extract_user_sessions_from_metadata(df):
    """
    Extrait les IDs de session utilisateur des métadonnées.
    Retourne une liste d'IDs de session uniques.
    """
    user_sessions = set()
    
    # Utiliser 'query_metadata' si disponible, sinon 'metadata'
    metadata_col = 'query_metadata' if 'query_metadata' in df.columns else 'metadata'
    
    for _, row in df.iterrows():
        metadata = row.get(metadata_col)
        if metadata and isinstance(metadata, dict):
            user_session_id = metadata.get('user_session_id')
            if user_session_id:
                user_sessions.add(user_session_id)
    
    return sorted(list(user_sessions))

def filter_dataframe_by_user_session(df, user_session_id):
    """
    Filtre le DataFrame pour ne garder que les interactions d'un utilisateur spécifique.
    """
    if user_session_id == "Tous les utilisateurs":
        return df
    
    if 'query_metadata' in df.columns:
        metadata_col = 'query_metadata'
    elif 'metadata' in df.columns:
        metadata_col = 'metadata'
    elif 'Métadonnées' in df.columns:
        metadata_col = 'Métadonnées'
    else:
        metadata_col = None
    
    if metadata_col is None:
        return df
    
    filtered_rows = []
    for _, row in df.iterrows():
        metadata = row.get(metadata_col)
        if metadata and isinstance(metadata, dict):
            if metadata.get('user_session_id') == user_session_id:
                filtered_rows.append(row)
    
    if filtered_rows:
        return pd.DataFrame(filtered_rows)
    else:
        return pd.DataFrame()

def format_user_session_id(user_session_id):
    """
    Formate l'ID de session utilisateur pour l'affichage.
    Affiche seulement les 12 premiers caractères + ... pour la lisibilité.
    """
    if len(user_session_id) > 12:
        return f"{user_session_id[:12]}..."
    return user_session_id

# =============================================================================
# TITRE ET INTERFACE PRINCIPALE
# =============================================================================

st.title("📊 Visionneur des Interactions et Feedbacks Multi-Utilisateurs")
st.caption("Affiche les interactions enregistrées avec filtrage par session utilisateur.")

# =============================================================================
# SIDEBAR POUR LES FILTRES
# =============================================================================

with st.sidebar:
    st.header("🔧 Filtres et Options")
    
    if st.button("🔄 Rafraîchir les données", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    max_interactions = st.slider(
        "Nombre maximum d'interactions à charger",
        min_value=50,
        max_value=1000,
        value=200,
        step=50
    )
    
    st.divider()
    
    st.subheader("📅 Période")
    period_filter = st.selectbox(
        "Période d'analyse",
        ["Toutes les périodes", "Dernières 24h", "Dernière semaine", "Dernier mois"]
    )

# =============================================================================
# CHARGEMENT ET TRAITEMENT DES DONNÉES
# =============================================================================

@st.cache_data(ttl=60)
def load_data(limit=200):
    """
    Charge les données depuis la base avec gestion multi-utilisateurs.
    """
    logging.info(f"Chargement des {limit} dernières interactions depuis la base de données...")
    interactions_list = session_service.get_all_interactions(limit=limit)
    
    if not interactions_list:
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(interactions_list)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp', ascending=False)
    
    # Assurer que 'metadata' (ou 'query_metadata') est la source pour l'ID de session
    metadata_col = 'query_metadata' if 'query_metadata' in df.columns else 'metadata'
    
    df['user_session_display'] = df[metadata_col].apply(
        lambda x: format_user_session_id(x.get('user_session_id', 'N/A')) 
        if isinstance(x, dict) and x.get('user_session_id') 
        else 'N/A'
    )
    
    if 'username' in df.columns:
        df['username_display'] = df['username'].fillna('N/A').astype(str).apply(lambda v: v if v.strip() else 'N/A')
    else:
        df['username_display'] = 'N/A'
    
    df_display = df[[
        'timestamp',
        'user_session_display',
        'username_display',
        'query',
        'response',
        'feedback',
        'feedback_value',
        'feedback_comment',
        'id',
        'sources',
        metadata_col # Utiliser la colonne correcte
    ]].rename(columns={
        'timestamp': 'Date & Heure (UTC)',
        'user_session_display': 'ID Session',
        'username_display': 'Utilisateur',
        'query': 'Question Utilisateur',
        'response': 'Réponse Assistant',
        'feedback': 'Feedback',
        'feedback_value': 'Valeur Feedback',
        'feedback_comment': 'Commentaire',
        'id': 'ID Interaction',
        metadata_col: 'Métadonnées'
    })
    
    return df_display, df

# Charger les données
try:
    df_display, df_original = load_data(limit=max_interactions)

    if df_display.empty:
        st.warning("❌ Aucune interaction enregistrée dans la base de données pour le moment.")
        st.stop()

    # =============================================================================
    # FILTRAGE PAR SESSION UTILISATEUR
    # =============================================================================
    
    user_sessions = extract_user_sessions_from_metadata(df_original)
    
    if user_sessions:
        st.info(f"✅ {len(df_display)} interactions trouvées de {len(user_sessions)} utilisateurs différents.")
        
        session_options = ["Tous les utilisateurs"] + user_sessions
        selected_session = st.selectbox(
            "🔍 Filtrer par session utilisateur:",
            options=session_options,
            format_func=lambda x: f"Tous les utilisateurs ({len(user_sessions)} sessions)" if x == "Tous les utilisateurs" 
                                  else f"Utilisateur {format_user_session_id(x)}"
        )
        
        if selected_session != "Tous les utilisateurs":
            df_filtered = filter_dataframe_by_user_session(df_original, selected_session)
            df_display_filtered = filter_dataframe_by_user_session(df_display, selected_session)
            
            if df_filtered.empty:
                st.warning(f"❌ Aucune interaction trouvée pour l'utilisateur {format_user_session_id(selected_session)}")
                st.stop()
            else:
                st.success(f"🎯 Affichage des {len(df_filtered)} interactions de l'utilisateur {format_user_session_id(selected_session)}")
        else:
            df_filtered = df_original
            df_display_filtered = df_display
            
        # Filtrage par période
        if period_filter != "Toutes les périodes":
            now = datetime.now()
            if period_filter == "Dernières 24h":
                start_date = now - timedelta(days=1)
            elif period_filter == "Dernière semaine":
                start_date = now - timedelta(weeks=1)
            elif period_filter == "Dernier mois":
                start_date = now - timedelta(days=30)
            
            df_filtered = df_filtered[df_filtered['timestamp'] >= start_date]
            df_display_filtered = df_display_filtered[df_display_filtered['Date & Heure (UTC)'] >= start_date]
            
            if not df_filtered.empty:
                st.info(f"📅 Période sélectionnée: {period_filter} ({len(df_filtered)} interactions)")
    else:
        st.warning("⚠️ Aucune information de session utilisateur trouvée dans les métadonnées.")
        df_filtered = df_original
        df_display_filtered = df_display

    # =============================================================================
    # ONGLETS PRINCIPAUX
    # =============================================================================
    
    tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "👥 Vue par Utilisateur", "📃 Données Brutes"])

    # =============================================================================
    # ONGLET 1: STATISTIQUES GLOBALES
    # =============================================================================
    
    with tab1:
        st.subheader("📊 Statistiques des feedbacks")

        if 'feedback_value' in df_filtered.columns:
            feedback_values = df_filtered['feedback_value'].dropna()
        else:
            def _feedback_to_numeric(value):
                if not isinstance(value, str):
                    return None
                normalized = value.strip().lower()
                if normalized.startswith("posit"):
                    return 1
                if normalized.startswith("n"):
                    return 0
                return None

            feedback_values = df_filtered['feedback'].apply(_feedback_to_numeric).dropna()

        total_interactions = len(df_filtered)
        total_feedback = len(feedback_values)
        missing_feedback = max(total_interactions - total_feedback, 0)

        if total_feedback > 0:
            positive_count = int((feedback_values == 1).sum())
            negative_count = int((feedback_values == 0).sum())

            positive_percent = (positive_count / total_feedback * 100) if total_feedback > 0 else 0
            negative_percent = (negative_count / total_feedback * 100) if total_feedback > 0 else 0
            feedback_rate = (total_feedback / total_interactions * 100) if total_interactions > 0 else 0

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total interactions", total_interactions)
            with col2:
                st.metric("Taux de feedback", f"{feedback_rate:.1f}%", f"{total_feedback}/{total_interactions}")
            with col3:
                st.metric("👍 Positifs", positive_count, f"{positive_percent:.1f}%")
            with col4:
                st.metric("👎 Négatifs", negative_count, f"{negative_percent:.1f}%")

            if missing_feedback > 0:
                st.caption(f"ℹ️ {missing_feedback} interactions n'ont pas encore de feedback.")

            feedback_data = pd.DataFrame({
                'Type': ['👍 Positif', '👎 Négatif'],
                'Nombre': [positive_count, negative_count]
            })

            fig = px.bar(
                feedback_data,
                x='Type',
                y='Nombre',
                color='Type',
                color_discrete_map={'👍 Positif': '#00CC96', '👎 Négatif': '#EF553B'},
                title="Répartition des feedbacks"
            )
            fig.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

            metadata_col = 'query_metadata' if 'query_metadata' in df_filtered.columns else 'metadata'
            if metadata_col in df_filtered.columns:
                mode_stats = []
                for _, row in df_filtered.iterrows():
                    metadata = row.get(metadata_col)
                    if metadata and isinstance(metadata, dict):
                        mode = metadata.get('mode', 'N/A')
                        feedback = row.get('feedback')
                        if isinstance(feedback, str):
                            label = feedback.strip().lower()
                            if label.startswith('posit'):
                                mode_stats.append({'mode': mode, 'feedback': 'positif'})
                            elif label.startswith('n'):
                                mode_stats.append({'mode': mode, 'feedback': 'négatif'})

                if mode_stats:
                    mode_df = pd.DataFrame(mode_stats)
                    mode_summary = mode_df.groupby(['mode', 'feedback']).size().unstack(fill_value=0)
                    for col in ['positif', 'négatif']:
                        if col not in mode_summary.columns:
                            mode_summary[col] = 0
                    mode_summary = mode_summary[['positif', 'négatif']]

                    if not mode_summary.empty:
                        st.subheader("📈 Performance par mode")
                        fig_mode = px.bar(
                            mode_summary.reset_index(),
                            x='mode',
                            y=['positif', 'négatif'],
                            title="Feedbacks par mode (RAG vs Direct)",
                            color_discrete_map={'positif': '#00CC96', 'négatif': '#EF553B'}
                        )
                        st.plotly_chart(fig_mode, use_container_width=True)

            if len(df_filtered) >= 5:
                st.subheader("📈 Évolution des feedbacks dans le temps")

                df_filtered_copy = df_filtered.copy()
                df_filtered_copy['date'] = df_filtered_copy['timestamp'].dt.date

                feedback_by_date = df_filtered_copy.groupby('date').agg(
                    positif=('feedback', lambda x: (x == 'positif').sum()),
                    négatif=('feedback', lambda x: (x == 'négatif').sum()),
                    total=('feedback', 'count')
                ).reset_index()

                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=feedback_by_date['date'],
                    y=feedback_by_date['positif'],
                    mode='lines+markers',
                    name='👍 Positifs',
                    line=dict(color='#00CC96', width=2),
                    marker=dict(size=8)
                ))
                fig2.add_trace(go.Scatter(
                    x=feedback_by_date['date'],
                    y=feedback_by_date['négatif'],
                    mode='lines+markers',
                    name='👎 Négatifs',
                    line=dict(color='#EF553B', width=2),
                    marker=dict(size=8)
                ))
                fig2.update_layout(
                    title="Évolution des feedbacks par jour",
                    xaxis_title="Date",
                    yaxis_title="Nombre de feedbacks"
                )
                st.plotly_chart(fig2, use_container_width=True)
        if missing_feedback > 0 and not df_display_filtered.empty:
            display_missing_mask = df_display_filtered['Feedback'].isna() | (df_display_filtered['Feedback'] == "")
            missing_subset = df_display_filtered[display_missing_mask][[
                'Date & Heure (UTC)',
                'ID Session',
                'Question Utilisateur',
                'ID Interaction'
            ]]
            with st.expander("Voir les interactions sans feedback"):
                st.dataframe(missing_subset, use_container_width=True)


        else:
            st.info("ℹ️ Aucun feedback n'a encore été donné pour la sélection actuelle.")

    # =============================================================================
    # ONGLET 2: VUE PAR UTILISATEUR (Logique conservée)
    # =============================================================================
    
    with tab2:
        st.subheader("👥 Statistiques par utilisateur")
        
        if user_sessions and len(user_sessions) > 1:
            user_stats = []
            
            metadata_col = 'query_metadata' if 'query_metadata' in df_original.columns else 'metadata'
            
            for user_session in user_sessions:
                user_data = filter_dataframe_by_user_session(df_original, user_session)
                
                if not user_data.empty:
                    total_interactions = len(user_data)
                    
                    positive_feedback = sum(user_data['feedback'] == "positif")
                    negative_feedback = sum(user_data['feedback'] == "négatif")
                    total_feedback = positive_feedback + negative_feedback
                    
                    modes_used = []
                    for _, row in user_data.iterrows():
                        metadata = row.get(metadata_col)
                        if metadata and isinstance(metadata, dict):
                            mode = metadata.get('mode', 'N/A')
                            modes_used.append(mode)
                    
                    rag_count = modes_used.count('RAG')
                    direct_count = modes_used.count('DIRECT')
                    
                    user_stats.append({
                        'Session': format_user_session_id(user_session),
                        'Session_ID': user_session,
                        'Interactions': total_interactions,
                        'Feedbacks': total_feedback,
                        '👍 Positifs': positive_feedback,
                        '👎 Négatifs': negative_feedback,
                        'Taux feedback (%)': (total_feedback/total_interactions*100) if total_interactions > 0 else 0,
                        'Mode RAG': rag_count,
                        'Mode Direct': direct_count,
                        'Dernière activité': user_data['timestamp'].max().strftime('%Y-%m-%d %H:%M')
                    })
            
            if user_stats:
                stats_df = pd.DataFrame(user_stats)
                stats_df = stats_df.sort_values('Interactions', ascending=False)
                
                st.dataframe(
                    stats_df.drop('Session_ID', axis=1),
                    use_container_width=True,
                    column_config={
                        "Session": st.column_config.TextColumn("ID Session", width="medium"),
                        "Interactions": st.column_config.NumberColumn("Total", width="small"),
                        "Taux feedback (%)": st.column_config.NumberColumn("Taux (%)", width="small", format="%.1f"),
                        "Dernière activité": st.column_config.TextColumn("Dernière activité", width="medium")
                    }
                )
                
                if len(stats_df) > 1:
                    fig_users = px.bar(
                        stats_df.head(10),
                        x='Session',
                        y='Interactions',
                        title="Top 10 des utilisateurs les plus actifs",
                        color='Interactions',
                        color_continuous_scale='Blues'
                    )
                    fig_users.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_users, use_container_width=True)
        else:
            st.info("ℹ️ Pas assez de sessions utilisateur pour afficher les statistiques comparatives.")

    # =============================================================================
    # ONGLET 3: DONNÉES BRUTES (Logique conservée)
    # =============================================================================
    
    with tab3:
        st.subheader("📃 Données brutes")
        
        if selected_session != "Tous les utilisateurs":
            st.info(f"🔍 Données filtrées pour l'utilisateur: {format_user_session_id(selected_session)}")
        
        if period_filter != "Toutes les périodes":
            st.info(f"📅 Période: {period_filter}")
        
        st.dataframe(
            df_display_filtered,
            use_container_width=True,
            column_config={
                "Date & Heure (UTC)": st.column_config.DatetimeColumn(
                    format="YYYY-MM-DD HH:mm:ss",
                    width="small"
                ),
                "ID Session": st.column_config.TextColumn(
                    width="small",
                    help="Identifiant de la session utilisateur"
                ),
                "Utilisateur": st.column_config.TextColumn(
                    width="small",
                    help="Nom saisi par l'utilisateur lors de la connexion"
                ),
                "Question Utilisateur": st.column_config.TextColumn(width="medium"),
                "Réponse Assistant": st.column_config.TextColumn(width="large"),
                "Feedback": st.column_config.TextColumn(width="small"),
                "Commentaire": st.column_config.TextColumn(width="medium"),
                "ID Interaction": st.column_config.NumberColumn(width="small"),
                "Métadonnées": st.column_config.JsonColumn(width="medium")
            },
            hide_index=True
        )

        csv_data = df_display_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Telecharger les interactions (CSV)",
            csv_data,
            file_name="interactions_filtrees.csv",
            mime="text/csv"
        )

        json_data = df_filtered.to_json(orient="records", date_format="iso").encode("utf-8")
        st.download_button(
            "Telecharger les interactions (JSON)",
            json_data,
            file_name="interactions_filtrees.json",
            mime="application/json"
        )

        st.subheader("🔍 Examiner une interaction spécifique")
        
        if not df_filtered.empty:
            selected_id = st.selectbox(
                "Sélectionnez l'ID de l'interaction:",
                options=df_filtered['id'].tolist(),
                format_func=lambda x: f"ID {x} - {df_filtered[df_filtered['id']==x].iloc[0]['query'][:50]}..."
            )

            if selected_id:
                selected_interaction = df_filtered[df_filtered['id'] == selected_id].iloc[0]
                
                metadata_col = 'query_metadata' if 'query_metadata' in df_filtered.columns else 'metadata'
                metadata = selected_interaction[metadata_col]
                
                if metadata and isinstance(metadata, dict):
                    user_session_id = metadata.get('user_session_id', 'N/A')
                    st.info(f"👤 Session utilisateur: {format_user_session_id(user_session_id)}")
                
                st.write(f"**❓ Question:** {selected_interaction['query']}")
                st.write(f"**🤖 Réponse:** {selected_interaction['response']}")
                
                feedback = selected_interaction['feedback']
                feedback_comment = selected_interaction['feedback_comment']
                if feedback:
                    emoji = "👍" if feedback == "positif" else "👎" if feedback == "négatif" else "❓"
                    st.write(f"**{emoji} Feedback:** {feedback}")
                    if feedback_comment:
                        st.write(f"**💬 Commentaire:** {feedback_comment}")

                if metadata and isinstance(metadata, dict):
                    mode = metadata.get('mode', 'N/A')
                    confidence = metadata.get('confidence', 0.0)
                    reason = metadata.get('reason', 'N/A')
                    st.write(f"**🔧 Mode:** {mode} (confiance: {confidence:.2f})")
                    st.write(f"**📋 Raison:** {reason}")
                    
                    # Affichage des métadonnées RAG Avancées
                    rewritten_query = metadata.get('rewritten_query')
                    if rewritten_query:
                        st.write(f"**📝 Requête Réécrite:** {rewritten_query}")

                st.write("**📚 Sources utilisées lors de la génération:**")
                sources = selected_interaction['sources']
                if sources and isinstance(sources, list):
                    for i, src in enumerate(sources):
                        meta = src.get("metadata", {})
                        with st.expander(f"Source {i+1}: `{meta.get('source', 'N/A')}` (Score: {src.get('score', 0.0):.4f})"):
                            st.text(src.get('text', 'N/A')[:1000] + "..." if len(src.get('text', '')) > 1000 else src.get('text', 'N/A'))
                elif sources:
                    st.json(sources)
                else:
                    st.write("Aucune source enregistrée pour cette interaction.")

                st.markdown("---")
                st.subheader("Gestion du feedback")

                current_feedback = selected_interaction.get('feedback')
                current_value = selected_interaction.get('feedback_value')
                current_comment_value = selected_interaction.get('feedback_comment')
                if isinstance(current_comment_value, str):
                    current_comment = current_comment_value
                elif pd.notna(current_comment_value):
                    current_comment = str(current_comment_value)
                else:
                    current_comment = ""

                feedback_choices = ["Aucun", "Positif", "Negatif"]
                default_choice = "Aucun"

                if isinstance(current_feedback, str):
                    normalized_feedback = current_feedback.strip().lower()
                    if normalized_feedback.startswith("posit"):
                        default_choice = "Positif"
                    elif normalized_feedback.startswith("n"):
                        default_choice = "Negatif"
                elif pd.notna(current_value):
                    default_choice = "Positif" if int(current_value) == 1 else "Negatif"

                with st.form(key=f"feedback_form_{selected_id}"):
                    selected_choice = st.radio(
                        "Selectionnez le type de feedback",
                        feedback_choices,
                        index=feedback_choices.index(default_choice),
                        horizontal=True
                    )
                    comment_input = st.text_area(
                        "Commentaire (optionnel)",
                        value=current_comment,
                        placeholder="Ajoutez un commentaire pour contextualiser le retour.",
                        height=120
                    )
                    submit_feedback = st.form_submit_button("Enregistrer le feedback")

                if submit_feedback:
                    if selected_choice == "Positif":
                        feedback_text = "positif"
                        feedback_value = 1
                    elif selected_choice == "Negatif":
                        feedback_text = "négatif"
                        feedback_value = 0
                    else:
                        feedback_text = None
                        feedback_value = None

                    comment_to_save = comment_input.strip() or None

                    if session_service.update_feedback(selected_id, feedback_text, comment_to_save, feedback_value):
                        st.success("Feedback enregistre avec succes.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Impossible d'enregistrer le feedback. Veuillez reessayer.")

except Exception as e:
    logging.error(f"Erreur lors du chargement ou de l'affichage des données: {e}", exc_info=True)
    st.error(f"❌ Une erreur est survenue lors de l'affichage des feedbacks: {e}")
    st.write("**Détails de l'erreur:**")
    st.code(str(e))
