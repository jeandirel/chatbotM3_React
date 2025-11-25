import datetime
import html
import streamlit as st
from typing import Callable, Optional, Dict

from utils.session_manager import build_preview, format_elapsed_time


def render_history_sidebar(
    *,
    session_store: Dict[str, dict],
    current_session_id: str,
    user_session_id: str,
    now_utc: datetime.datetime,
    start_new_conversation: Callable[[], None],
    logout_user: Callable[[], None],
    delete_conversation: Callable[[str], None],
    display_username: str,
) -> None:
    """Affiche la sidebar d'historique avec recherche, grouping et actions."""
    st.markdown(
        """
        <style>
        .hist-wrapper { padding: 6px 2px 12px 2px; }
        .hist-header { font-weight: 700; font-size: 1rem; margin-bottom: 6px; color: #b35c00; display:flex; align-items:center; gap:6px; }
        .hist-search input { background: #fff7ef; border-color: #f2c59c; }
        .hist-section-title { color: #d47b1f; font-weight: 700; font-size: 0.9rem; margin: 12px 0 6px; display:flex; align-items:center; gap:6px; }
        .hist-card { border: 1px solid #f1d2b7; background: white; border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); cursor: pointer; transition: transform 0.05s ease, box-shadow 0.1s ease; }
        .hist-card:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,0.10); }
        .hist-card-title { font-weight: 700; color: #2e2e2e; margin-bottom: 4px; }
        .hist-card-preview { color: #6b6b6b; font-size: 0.92rem; }
        .hist-card-meta { color: #d47b1f; font-size: 0.85rem; margin-top: 6px; }
        .hist-buttons { margin-top: 12px; display: grid; gap: 6px; }
        /* Forcer la couleur du bouton "Nouvelle conversation" */
        section[data-testid="stSidebar"] button[data-testid="baseButton-primary"],
        section[data-testid="stSidebar"] div.stButton > button {
            background: #f97316 !important;
            border: 1px solid #f97316 !important;
            color: #fff !important;
            font-weight: 700;
            border-radius: 10px;
            padding: 0.75rem 0.8rem;
        }
        section[data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover,
        section[data-testid="stSidebar"] div.stButton > button:hover {
            background: #e56712 !important;
            border-color: #e56712 !important;
        }
        section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
            background: #e84141 !important;
            border: 1px solid #e84141 !important;
            color: #fff !important;
            font-weight: 700;
            border-radius: 10px;
            padding: 0.75rem 0.8rem;
        }
        section[data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
            background: #d73737 !important;
            border-color: #d73737 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="hist-wrapper">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:1.05rem; font-weight:700; display:flex; align-items:center; gap:6px;">📚 Documentation M3</div>', unsafe_allow_html=True)
    st.caption("Assistant virtuel ASTERA")
    st.markdown(
        f"<div style='margin:6px 0 10px 0;'>👤 <strong>Utilisateur :</strong> "
        f"`{html.escape(display_username)}`</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="hist-header">🗂️ Historique</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    search_query = st.text_input(
        "Rechercher dans l'historique",
        key="history_search",
        placeholder="Rechercher dans l'historique...",
        label_visibility="collapsed",
    )

    sessions_sorted = sorted(
        session_store.items(),
        key=lambda item: item[1].get("last_activity", item[1].get("created_at", now_utc)),
        reverse=True,
    )

    def categorize_session(dt: Optional[datetime.datetime]) -> str:
        if not dt:
            return "plus_ancien"
        now = datetime.datetime.now(datetime.timezone.utc)
        delta = now.date() - dt.date()
        if delta.days == 0:
            return "aujourdhui"
        if delta.days == 1:
            return "hier"
        if delta.days < 7:
            return "cette_semaine"
        return "plus_ancien"

    filtered = []
    for sid, data in sessions_sorted:
        owner = data.get("owner")
        if owner and owner != user_session_id:
            continue
        if owner is None and sid != current_session_id:
            continue
        messages = data.get("messages", [])
        title = data.get("title") or f"Discussion {sid[:8]}"
        preview = build_preview(messages)
        last_seen = data.get("last_activity") or data.get("created_at")
        elapsed = format_elapsed_time(last_seen)
        if search_query:
            q = search_query.lower()
            if q not in title.lower() and q not in preview.lower():
                continue
        filtered.append(
            {
                "sid": sid,
                "title": title,
                "preview": preview,
                "elapsed": elapsed,
                "category": categorize_session(last_seen),
            }
        )

    section_labels = [
        ("aujourdhui", "📅 Aujourd'hui"),
        ("hier", "📅 Hier"),
        ("cette_semaine", "📅 Cette semaine"),
        ("plus_ancien", "📅 Plus ancien"),
    ]

    any_card = False
    for key_cat, label in section_labels:
        items = [c for c in filtered if c["category"] == key_cat]
        if not items:
            continue
        any_card = True
        st.markdown(
            f'<div class="hist-section-title">{label}</div>', unsafe_allow_html=True
        )
        for c in items:
            col_card, col_del = st.columns([10, 1])
            with col_card:
                card_html = f"""
                    <div class="hist-card" onclick="window.location.href='?session={c['sid']}';">
                        <div class="hist-card-title">{html.escape(c['title'])}</div>
                        <div class="hist-card-preview">{html.escape(c['preview'])}</div>
                        <div class="hist-card-meta">{html.escape(c['elapsed'])}</div>
                    </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
            with col_del:
                if st.button("✕", key=f"del_{c['sid']}", help="Supprimer cette discussion"):
                    delete_conversation(c["sid"])

    if not any_card:
        st.caption("Aucune discussion enregistrée.")

    st.markdown('<div class="hist-buttons">', unsafe_allow_html=True)
    if st.button("🆕 Nouvelle conversation", use_container_width=True, type="primary", key="btn_new_disc_streamlit"):
        start_new_conversation()
    if st.button("🚪 Déconnexion", use_container_width=True, type="secondary", key="btn_logout_streamlit"):
        logout_user()
    st.markdown("</div>", unsafe_allow_html=True)
