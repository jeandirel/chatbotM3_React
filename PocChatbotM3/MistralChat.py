

######################################################################################### mise à jour #########################################################################################
#################################################  code generer par gemini 2.5 pro #################################################
#MistralChat.py (app.py)
import truststore
truststore.inject_into_ssl()
import streamlit as st
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

from mistralai.exceptions import MistralAPIException
import logging
import datetime
from streamlit_feedback import streamlit_feedback
import os
from pathlib import Path
from typing import Optional, Set, Dict
import re
import uuid  # Pour l'ID de session utilisateur
import base64
import html

# Importer nos modules locaux
from utils.config import (
    APP_TITLE, COMMUNE_NAME, MISTRAL_API_KEY, CHAT_MODEL, 
    SEARCH_K
)
from utils.vector_store import VectorStoreManager
# from utils.database import log_interaction, update_feedback, get_or_create_user_session # REMOVED
from modules.session import SessionService # ADDED
session_service = SessionService() # ADDED

from utils.query_classifier import QueryClassifier
from utils.conversation_history import ConversationHistory, conversation_manager
from utils.session_manager import compute_session_title, format_elapsed_time, build_preview
from components.history_sidebar import render_history_sidebar

# --- Configuration et Initialisation ---

SESSION_TIMEOUT = datetime.timedelta(minutes=30)
CURRENT_SESSION_ID: Optional[str] = None

SMALLTALK_PATTERNS = [
    r"^\s*bonjour\b",
    r"^\s*salut\b",
    r"^\s*bonsoir\b",
    r"^\s*(merci|thanks)\b",
    r"^\s*(coucou)\b",
    r"^\s*(hello)\b",
    r"\bcomment vas[- ]tu\b",
    r"\bcomment allez[- ]vous\b",
    r"\bbonne journ[eé]e\b",
    r"\bbonne soir[eé]e\b",
]

SMALLTALK_RESPONSES = [
    "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
    "Salut ! Je suis prêt à répondre à vos questions sur la documentation M3.",
    "Bonjour ! N'hésitez pas à me donner un sujet ou un besoin précis.",
    "Heureux de vous retrouver. Que souhaitez-vous explorer ?",
]


@st.cache_resource
def get_persistent_session_store() -> Dict[str, Dict[str, object]]:
    """Stocke les sessions utilisateur au-delà d'un simple rerun."""
    return {}

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration de la page Streamlit
st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide")

# Injection JS pour renommer les labels de la sidebar sans toucher aux fichiers
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

# Initialisation (avec mise en cache Streamlit)
@st.cache_resource
def get_vector_store():
    """Met en cache le VectorStoreManager pour éviter de recharger l'index."""
    logging.info("Chargement du VectorStoreManager...")
    return VectorStoreManager()

@st.cache_resource
def get_mistral_client():
    """Met en cache le client Mistral."""
    if not MISTRAL_API_KEY:
        st.error("Erreur: La clé API Mistral (MISTRAL_API_KEY) n'est pas configurée.")
        st.stop()
    logging.info("Initialisation du client Mistral...")
    return MistralClient(api_key=MISTRAL_API_KEY)

@st.cache_resource
def get_query_classifier():
    """Met en cache le QueryClassifier."""
    logging.info("Initialisation du QueryClassifier...")
    return QueryClassifier()

# Dépendances (Chargement des ressources au démarrage)
vs_manager = get_vector_store()
mistral_client = get_mistral_client()
query_classifier = get_query_classifier()

session_store = get_persistent_session_store()
query_params = st.query_params
requested_session_values = query_params.get("session")
requested_session_id = requested_session_values[-1] if requested_session_values else None
now_utc = datetime.datetime.now(datetime.timezone.utc)


def _update_query_params(session_id: str) -> None:
    st.query_params["session"] = session_id


def _create_new_session(initial_id: Optional[str] = None) -> str:
    new_id = initial_id or str(uuid.uuid4())
    session_store[new_id] = {
        "messages": [],
        "created_at": now_utc,
        "last_activity": now_utc,
        "current_interaction_id": None,
        "title": f"Discussion du {now_utc.strftime('%d/%m %H:%M')}",
        "owner": st.session_state.get("user_session_id"),
    }
    _update_query_params(new_id)
    return new_id


# Toujours essayer de réutiliser une session existante (session_state ou query params)
existing_session_id = st.session_state.get("session_id")
current_session_id: Optional[str] = None
session_data: Optional[dict] = None

for candidate_id in (existing_session_id, requested_session_id):
    if candidate_id and candidate_id in session_store:
        candidate_data = session_store[candidate_id]
        last_activity = candidate_data.get("last_activity", candidate_data.get("created_at", now_utc))
        if now_utc - last_activity > SESSION_TIMEOUT:
            # Expirée : on la supprime et on continue à chercher une autre
            del session_store[candidate_id]
            continue
        current_session_id = candidate_id
        session_data = candidate_data
        break

if not current_session_id:
    # Aucune session réutilisable : on en crée une nouvelle
    candidate = existing_session_id or requested_session_id
    current_session_id = _create_new_session(candidate)
    session_data = session_store[current_session_id]

# Harmoniser l'URL avec la session courante
_update_query_params(current_session_id)

session_data["last_activity"] = now_utc
CURRENT_SESSION_ID = current_session_id
st.session_state["session_id"] = current_session_id
st.session_state["messages"] = list(session_data.get("messages", []))
st.session_state["current_interaction_id"] = session_data.get("current_interaction_id")


def persist_session_state(update_activity: bool = True) -> None:
    """Synchronise la conversation courante avec le store persistant."""
    session_data["messages"] = list(st.session_state.get("messages", []))
    session_data["current_interaction_id"] = st.session_state.get("current_interaction_id")
    session_data["title"] = compute_session_title(
        session_data["messages"],
        session_data.get("title", f"Discussion du {session_data.get('created_at', now_utc).strftime('%d/%m %H:%M')}")
    )
    if update_activity:
        session_data["last_activity"] = datetime.datetime.now(datetime.timezone.utc)


def start_new_conversation(toast: bool = True) -> None:
    """Crée une nouvelle session de conversation et rafraîchit l'interface."""
    global CURRENT_SESSION_ID, session_data

    new_session_id = _create_new_session()
    CURRENT_SESSION_ID = new_session_id
    session_data = session_store[new_session_id]
    session_data["messages"] = []
    session_data["last_activity"] = datetime.datetime.now(datetime.timezone.utc)
    session_data["current_interaction_id"] = None
    session_data["title"] = "Nouvelle discussion"
    session_data["owner"] = st.session_state.get("user_session_id")

    st.session_state["messages"] = []
    st.session_state["session_id"] = new_session_id
    st.session_state["current_interaction_id"] = None

    keys_to_clear = [
        "_pdf_inline_style_injected",
    ]
    prefixes_to_clear = (
        "pdf_modal_",
        "history_pdf_modal_",
        "source_select_",
        "feedback_submitted_",
    )
    for key in list(st.session_state.keys()):
        if key in keys_to_clear or key.startswith(prefixes_to_clear):
            del st.session_state[key]

    if toast:
        st.toast("Nouvelle discussion créée.", icon="🆕")
    st.rerun()


def switch_to_session(session_id: str) -> None:
    """Bascule vers une session existante sans modifier le contenu."""
    global CURRENT_SESSION_ID, session_data

    if session_id not in session_store:
        st.warning("Conversation introuvable.")
        return

    CURRENT_SESSION_ID = session_id
    session_data = session_store[session_id]
    if session_data.get("owner") not in (None, st.session_state.get("user_session_id")):
        st.warning("Conversation appartenant à un autre utilisateur.")
        return
    session_data["last_activity"] = datetime.datetime.now(datetime.timezone.utc)
    _update_query_params(session_id)

    st.session_state["session_id"] = session_id
    st.session_state["messages"] = list(session_data.get("messages", []))
    st.session_state["current_interaction_id"] = session_data.get("current_interaction_id")

    st.rerun()


def is_smalltalk(query: str) -> bool:
    if not query:
        return False
    lowered = query.lower()
    return any(re.search(pattern, lowered) for pattern in SMALLTALK_PATTERNS)


def pick_smalltalk_response() -> str:
    idx = hash(datetime.datetime.now().isoformat()) % len(SMALLTALK_RESPONSES)
    return SMALLTALK_RESPONSES[idx]


# --- Utilitaires PDF ---

PDF_SEARCH_DIRECTORIES = [
    Path.cwd(),
    Path.cwd() / "inputs",
    Path.cwd() / "database",
    Path.cwd() / "pages",
    Path.cwd() / "vector_db",
]


def _sanitize_pdf_hint(value: Optional[str]) -> Optional[str]:
    """Nettoie un indice de PDF en retirant fragments et paramètres superflus."""
    if not value or not isinstance(value, str):
        return None

    cleaned = value.strip()
    for separator in ("::", "#", "?"):
        if separator in cleaned:
            cleaned = cleaned.split(separator)[0]

    if not cleaned:
        return None

    lowered = cleaned.lower()
    if ".pdf" in lowered and not lowered.endswith(".pdf"):
        cleaned = cleaned[: lowered.index(".pdf") + 4]
    elif not lowered.endswith(".pdf"):
        return None

    return cleaned.strip()


@st.cache_data(show_spinner=False)
def resolve_pdf_path(pdf_hint: str) -> Optional[str]:
    """Tente de retrouver sur le disque un PDF à partir d'un indice."""
    sanitized = _sanitize_pdf_hint(pdf_hint)
    if not sanitized:
        return None

    candidate = Path(sanitized)
    considered: Set[Path] = set()

    def _register(path_candidate: Path) -> Optional[str]:
        if path_candidate in considered:
            return None
        considered.add(path_candidate)
        if path_candidate.is_file():
            return str(path_candidate)
        return None

    direct_match = _register(candidate)
    if direct_match:
        return direct_match

    possible_names = [candidate]
    if candidate.name:
        possible_names.append(Path(candidate.name))

    for base_dir in PDF_SEARCH_DIRECTORIES:
        if not base_dir.exists():
            continue
        for name in possible_names:
            path_candidate = name if name.is_absolute() else base_dir / name
            match = _register(path_candidate)
            if match:
                return match

    target_name = candidate.name
    if target_name:
        for base_dir in PDF_SEARCH_DIRECTORIES:
            if not base_dir.exists():
                continue
            try:
                found = next(base_dir.rglob(target_name))
                match = _register(found)
                if match:
                    return match
            except StopIteration:
                continue

    return None


@st.cache_data(show_spinner=False)
def encode_pdf_to_base64(pdf_path: str) -> Optional[str]:
    """Charge un PDF et retourne sa représentation base64."""
    path = Path(pdf_path)
    if not path.is_file():
        return None
    with path.open("rb") as pdf_file:
        return base64.b64encode(pdf_file.read()).decode("utf-8")


def extract_pdf_hint_from_source(source: dict) -> Optional[str]:
    """Récupère un indice de PDF à partir des métadonnées de la source."""
    if not isinstance(source, dict):
        return None

    metadata = source.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    candidates = [
        metadata.get("document_path"),
        metadata.get("file_path"),
        metadata.get("source_path"),
        metadata.get("path"),
        metadata.get("source"),
        source.get("source"),
        source.get("path"),
    ]

    for candidate in candidates:
        sanitized = _sanitize_pdf_hint(candidate) if isinstance(candidate, str) else None
        if sanitized:
            return sanitized

    return None


def show_pdf_modal_if_needed(state_key: str, pdf_label: str, pdf_path: Path) -> None:
    """Affiche un PDF dans la zone courante si l'état associé est actif."""
    if not st.session_state.get(state_key):
        return

    if not st.session_state.get("_pdf_inline_style_injected", False):
        st.markdown(
            """
            <style>
            .pdf-inline-viewer {
                border: 1px solid #ffa94d;
                border-radius: 12px;
                padding: 1rem;
                background: #fff9f2;
                box-shadow: 0 12px 32px rgba(255, 169, 77, 0.12);
                margin-top: 0.75rem;
            }
            .pdf-inline-viewer h4 {
                margin-top: 0;
                margin-bottom: 0.75rem;
                color: #ff6b35;
                font-size: 1.1rem;
                font-weight: 600;
            }
            .pdf-inline-viewer iframe {
                width: 100%;
                min-height: 560px;
                border: none;
                border-radius: 10px;
                background: #f7f7f7;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state["_pdf_inline_style_injected"] = True

    encoded_pdf = encode_pdf_to_base64(str(pdf_path))
    title_html = html.escape(f"📄 {pdf_label}")
    filename_html = html.escape(pdf_path.name)

    if not encoded_pdf:
        st.warning("Impossible de charger le document PDF associé. Vérifiez que le fichier est accessible.")
    else:
        st.caption("Déplacez-vous dans le document grâce à l’ascenseur intégré.")
        st.markdown(
            f"""
            <div class="pdf-inline-viewer">
                <h4>{title_html}</h4>
                <iframe src="data:application/pdf;base64,{encoded_pdf}"></iframe>
                <div style="margin-top: 0.5rem; font-size: 0.85rem; color: #777;">
                    Fichier : {filename_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.button("Fermer le document", key=f"close_{state_key}"):
        st.session_state[state_key] = False
        persist_session_state()
        st.rerun()

def render_source_selector(
    sources: list,
    block_key: str,
    default_expanded: bool = False,
) -> None:
    """Affiche les sources sous forme de liste sélectionnable."""
    if not sources:
        return

    option_labels = []
    for idx, src in enumerate(sources):
        meta = src.get("metadata", {}) or {}
        source_label = meta.get("source", "N/A")
        score = src.get("score", 0.0)
        context_type = meta.get("context_type", "principal").upper()
        option_labels.append(
            f"Source {idx + 1}: {source_label} (Score: {score:.4f}, Type: {context_type})"
        )

    with st.expander("📚 Sources utilisées", expanded=default_expanded):
        st.caption("Sélectionnez une source pour afficher le contexte et, si disponible, le document.")
        selected_label = st.selectbox(
            "Sources disponibles",
            option_labels,
            index=0,
            label_visibility="collapsed",
            key=f"source_select_{block_key}",
        )
        selected_index = option_labels.index(selected_label)
        selected_source = sources[selected_index]
        meta = selected_source.get("metadata", {}) or {}

        st.markdown(f"**Chemin** · `{meta.get('source', 'N/A')}`")
        st.markdown(
            f"**Score** · {selected_source.get('score', 0.0):.4f}  &nbsp;&nbsp; **Type** · {meta.get('context_type', 'principal').upper()}"
        )
        with st.container():
            st.markdown("**Extrait :**")
            st.write(selected_source.get("text", "N/A")[:500] + "…")

        pdf_hint = extract_pdf_hint_from_source(selected_source)
        pdf_path_str = resolve_pdf_path(pdf_hint) if pdf_hint else None
        pdf_path = Path(pdf_path_str) if pdf_path_str else None

        if pdf_hint and not pdf_path:
            st.caption(
                f"⚠️ PDF introuvable pour `{pdf_hint}`",
                help="Le document référencé n'a pas été trouvé sur le disque.",
            )

        if pdf_path:
            state_key = f"pdf_modal_{block_key}_{selected_index}"
            path_key = f"{state_key}_path"
            if state_key not in st.session_state:
                st.session_state[state_key] = False
            st.session_state[path_key] = str(pdf_path)

            if st.button("👁️ Voir PDF", key=f"btn_pdf_{block_key}_{selected_index}"):
                st.session_state[state_key] = True

            stored_path = Path(st.session_state.get(path_key, str(pdf_path)))
            show_pdf_modal_if_needed(
                state_key=state_key,
                pdf_label=f"Source {selected_index + 1}",
                pdf_path=stored_path,
            )

# --- Fonctions liées à l'identification utilisateur ---

def trigger_rerun() -> None:
    """Déclenche un rerun Streamlit, compatible avec différentes versions."""
    rerun_callable = getattr(st, "rerun", None)
    if callable(rerun_callable):
        rerun_callable()
    else:
        from streamlit.runtime.scriptrunner import RerunException, RerunData  # type: ignore
        raise RerunException(RerunData(None))


def require_username() -> str:
    """Affiche une fenêtre modale (ou un fallback) pour récupérer un identifiant utilisateur."""
    existing = st.session_state.get("username")
    if existing:
        return existing

    st.session_state.setdefault("auth_modal_open", True)
    st.session_state.setdefault("auth_error_message", "")

    def render_auth_form() -> None:
        st.write("Veuillez saisir un identifiant pour accéder au chatbot.")
        username_input = st.text_input(
            "Identifiant utilisateur (ex: initiales)",
            key="auth_username_input",
        )
        st.caption("Cet identifiant permet de lier vos conversations et feedbacks.")

        if st.button("Continuer", type="primary", key="auth_modal_submit"):
            candidate = username_input.strip()
            if candidate:
                st.session_state["username"] = candidate
                st.session_state["auth_modal_open"] = False
                st.session_state.pop("auth_error_message", None)
                st.session_state.pop("auth_username_input", None)
                trigger_rerun()
                return
            st.session_state["auth_error_message"] = "Merci de saisir un identifiant valide."

        error_message = st.session_state.get("auth_error_message")
        if error_message:
            st.error(error_message)

    def render_fallback_modal() -> None:
        st.markdown(
            """
            <style>
                .auth-fallback-wrapper {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 85vh;
                }
                .auth-fallback-card {
                    background: var(--background-color);
                    padding: 2rem 2.5rem;
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
            st.markdown('<div class="auth-fallback-wrapper">', unsafe_allow_html=True)
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_center:
                st.markdown('<div class="auth-fallback-card">', unsafe_allow_html=True)
                st.markdown("### Identification requise")
                render_auth_form()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("auth_modal_open", True):
        dialog_fn = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
        if dialog_fn:
            modal_obj = dialog_fn("Identification requise")
            if hasattr(modal_obj, "__enter__") and hasattr(modal_obj, "__exit__"):
                with modal_obj:
                    render_auth_form()
                if st.session_state.get("auth_modal_open", True):
                    st.stop()
                return st.session_state["username"]
            if callable(modal_obj):

                @modal_obj
                def _auth_dialog():
                    render_auth_form()

                _auth_dialog()
                if st.session_state.get("auth_modal_open", True):
                    st.stop()
                return st.session_state["username"]

        if st.session_state.get("auth_modal_open", True):
            render_fallback_modal()
            st.stop()

    # Si on arrive ici sans username, on force la réouverture et on stoppe pour éviter un KeyError
    if "username" not in st.session_state:
        st.session_state["auth_modal_open"] = True
        st.stop()
    return st.session_state["username"]


def ensure_user_identity() -> tuple[str, str]:
    """Garantit que l'utilisateur est identifié et retourne (username, session_id)."""
    username = require_username()
    normalized = username.strip().lower()

    cached_owner = st.session_state.get("user_session_owner")
    cached_session_id = st.session_state.get("user_session_id")

    if cached_owner != normalized or not cached_session_id:
        # Changement d'utilisateur : on réinitialise l'état courant pour éviter le mélange des conversations
        if cached_owner is not None and cached_owner != normalized:
            for key in ("session_id", "messages", "current_interaction_id"):
                st.session_state.pop(key, None)
            try:
                del st.query_params["session"]
            except Exception:  # pragma: no cover
                pass
        try:
            session_identifier = session_service.get_or_create_user_session(normalized)
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("Impossible d'initialiser la session utilisateur '%s': %s", normalized, exc)
            st.error("❌ Erreur lors de l'initialisation de votre session utilisateur. Veuillez réessayer plus tard.")
            st.stop()

        st.session_state["user_session_id"] = session_identifier
        st.session_state["user_session_owner"] = normalized

    return username, st.session_state["user_session_id"]


# --- Fonctions de l'Application ---

def logout_user() -> None:
    """Déconnecte l'utilisateur et réinitialise l'état courant."""
    global CURRENT_SESSION_ID, session_data

    CURRENT_SESSION_ID = None
    session_data = None

    for key in [
        "username",
        "user_session_owner",
        "user_session_id",
        "session_id",
        "messages",
        "current_interaction_id",
        "auth_username_input",
        "auth_error_message",
    ]:
        st.session_state.pop(key, None)

    # Forcer la réouverture de la modale d'authentification
    st.session_state["auth_modal_open"] = True

    try:
        del st.query_params["session"]
    except Exception:  # pragma: no cover
        pass

    st.rerun()


def delete_conversation(session_id: str) -> None:
    """Supprime une session si elle appartient à l'utilisateur courant."""
    owner = session_store.get(session_id, {}).get("owner")
    if owner and owner != st.session_state.get("user_session_id"):
        st.warning("Impossible de supprimer une discussion qui ne vous appartient pas.")
        return
    # Si on supprime la session courante, on repart sur une nouvelle
    is_current = session_id == CURRENT_SESSION_ID
    if session_id in session_store:
        del session_store[session_id]
    if is_current:
        start_new_conversation(toast=False)
    else:
        st.rerun()


def get_session_id():
    """Génère un ID de session unique par utilisateur Streamlit."""
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = CURRENT_SESSION_ID or str(uuid.uuid4())
    elif CURRENT_SESSION_ID and st.session_state['session_id'] != CURRENT_SESSION_ID:
        st.session_state['session_id'] = CURRENT_SESSION_ID
    return st.session_state['session_id']

def get_conversation_key(user_id: str, current_time: datetime.datetime) -> str:
    """Clé de session pour le fil de conversation en cours."""
    # CORRECTION de l'AttributeError
    return conversation_manager.get_current_conversation_key(user_id, current_time)

def get_contextual_query(user_query: str, history_messages: list) -> tuple[str, list, bool]:
    """
    Réécrit la requête de l'utilisateur en incluant le contexte de l'historique de conversation.
    """
    if not history_messages:
        return user_query, [], False
    
    # Prompt système pour la réécriture
    system_prompt = """
Tu es un expert en réécriture de requêtes. Ton rôle est de réécrire la dernière question de l'utilisateur
pour qu'elle soit contextuellement complète et compréhensible par un système de recherche (RAG),
en utilisant l'historique de conversation fourni.

Si la dernière question est déjà autonome ou n'a pas besoin de contexte (par exemple, "Merci", "Bonjour", "Quelle est la procédure X"), retourne la question originale telle quelle.

Réponds UNIQUEMENT avec la requête réécrite et rien d'autre.
    """.strip()
    
    messages = [ChatMessage(role="system", content=system_prompt)]
    
    # Limiter l'historique à la dernière paire (User/Assistant)
    history_for_rewrite = history_messages[-4:] 
    
    for role, content in history_for_rewrite:
        if role in ('user', 'assistant'):
            messages.append(ChatMessage(role=role, content=content))
    
    # Ajouter la dernière question de l'utilisateur
    messages.append(ChatMessage(role="user", content=f"Dernière question : {user_query}"))

    try:
        response = mistral_client.chat(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.0,
            max_tokens=150
        )
        
        rewritten_query = response.choices[0].message.content.strip()

        # Heuristique de vérification
        is_rewritten = (rewritten_query.lower().strip() != user_query.lower().strip())
        
        if is_rewritten:
            logging.info(f"Requête réécrite: {user_query} -> {rewritten_query}")
        
        return rewritten_query, history_for_rewrite, is_rewritten

    except (MistralAPIException, Exception) as e:
        logging.error(f"Erreur lors de la réécriture de requête: {e}")
        return user_query, [], False


def process_query(user_query: str, user_id: str, username: str, conversation_messages: list, current_conversation_id: str):
    """
    Fonction principale pour traiter la requête, effectuer le RAG et générer la réponse.
    """
    
    # 1. Réécriture de la Requête (RAG Conversationnel)
    rewritten_query, history_for_rewrite, is_rewritten = get_contextual_query(
        user_query, 
        conversation_messages
    )
    
    # 2. Classification de la Requête (Routage Hybride)
    needs_rag, confidence, reason = query_classifier.needs_rag(rewritten_query)
    
    user_label = username or user_id[:8]
    logging.info(f"[{user_label}] Classification: RAG={needs_rag} (Confiance: {confidence:.2f}, Raison: {reason})")
    
    retrieved_docs = []
    sources_for_log = []
    
    # 3. Récupération des Documents (Retrieval)
    if needs_rag and vs_manager.index is not None:
        try:
            # Recherche RAG Avancée (avec post-traitement de contexte dans vs_manager.search)
            retrieved_docs = vs_manager.search(
                query_text=rewritten_query, 
                k=SEARCH_K
            )
        except Exception as e:
            logging.error(f"Erreur lors de la recherche vectorielle: {e}")
            needs_rag = False  # Revert to direct mode if retrieval fails
            reason = f"Échec de la recherche vectorielle: {e}"
    
    
    # 4. Préparation du Contexte et du Prompt LLM (FIX du SyntaxError)
    
    # Préparer l'historique pour le LLM (limitée à 8 messages)
    llm_history = [ChatMessage(role=role, content=content) 
                   for role, content in conversation_messages[-8:] 
                   if role in ('user', 'assistant')]
        
    llm_history.append(ChatMessage(role="user", content=user_query))

    if is_smalltalk(user_query):
        friendly = pick_smalltalk_response()
        metadata = {
            "mode": "DIRECT",
            "confidence": 1.0,
            "reason": "Petite conversation detectee",
            "conversation_id": current_conversation_id,
            "user_session_id": user_id,
            "username": username,
        }
        interaction_id = session_service.log_interaction(
            query=user_query,
            response=friendly,
            sources=[],
            metadata=metadata
        )
        return friendly, [], metadata, interaction_id

    
    # --- Mode RAG (Documents trouvés) ---
    if needs_rag and retrieved_docs:
        logging.info(f"[{user_id[:8]}] RAG Actif : {len(retrieved_docs)} documents récupérés.")
        
        # Construire la chaîne de contexte pour l'injection
        context_str = "\n\n---\n\n".join(
            [
                f"Source: {doc['metadata'].get('source', 'Inconnue')} (Score: {doc['score']:.4f}, Type: {doc['metadata'].get('context_type', 'principal')})\nContenu: {doc['text']}"
                for doc in retrieved_docs
            ]
        )
        
        # Préparer les sources pour le log et l'affichage
        sources_for_log = [ 
            {
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": doc["score"],
                "raw_score": doc.get("raw_score", 0.0)
            }
            for doc in retrieved_docs
        ]

        # FIX: Utiliser format() sur le modèle de prompt pour éviter SyntaxError
        system_prompt_template = """
Vous êtes un assistant virtuel pour {commune_name}.
Répondez à la question de l'utilisateur en vous basant **UNIQUEMENT** sur la documentation fournie dans le contexte ci-dessous.
Synthétisez toujours l'information avec vos propres mots et évitez le copier-coller.
Si l'information n'est **PAS** dans le contexte, dites poliment que vous ne savez pas ou que l'information n'est pas disponible dans votre base de connaissances.
Adoptez un ton cordial et professionnel, et **citez vos sources** (nom de fichier ou catégorie).

Contexte fourni pour la recherche:
---
{context_str}
---
"""
        
        system_prompt = system_prompt_template.format(
            commune_name=COMMUNE_NAME,
            context_str=context_str
        ).strip()
        
    # --- Mode RAG (Échec de récupération) ---
    elif needs_rag and not retrieved_docs:
        logging.warning(f"[{user_id[:8]}] RAG Échoué : Aucun document pertinent trouvé malgré la classification RAG.")
        sources_for_log = []
        
        # FIX: Utiliser format() sur le modèle de prompt
        system_prompt_template = """
Vous êtes un assistant virtuel pour {commune_name}.
L'utilisateur a posé une question qui semble concerner des informations spécifiques à la documentation, mais aucune information pertinente n'a été trouvée dans notre base de connaissances.
Indiquez poliment que vous n'avez pas cette information spécifique et proposez-lui de reformuler la question ou de contacter directement le service desk ou le pôle IA (Myriana).
N'inventez pas d'informations sur {commune_name} et gardez un ton empathique.
"""
        system_prompt = system_prompt_template.format(
            commune_name=COMMUNE_NAME
        ).strip()
        
    # --- Mode Direct (Classification non-RAG) ---
    else:
        sources_for_log = []
        
        # FIX: Utiliser format() sur le modèle de prompt
        system_prompt_template = """
Vous êtes un assistant virtuel pour {commune_name}.
Répondez à la question de l'utilisateur en utilisant vos connaissances générales avec un ton chaleureux.
Soyez concis, précis, utile et reformulez avec vos propres mots.
Si la question concerne des informations spécifiques à {commune_name} que vous ne connaissez pas, indiquez clairement que vous n'avez pas cette information spécifique.
N'inventez pas d'informations sur {commune_name}.
"""
        system_prompt = system_prompt_template.format(
            commune_name=COMMUNE_NAME
        ).strip()
        
    # 5. Appel au Modèle
    final_messages = [ChatMessage(role="system", content=system_prompt)] + llm_history
    
    try:
        response = mistral_client.chat(
            model=CHAT_MODEL,
            messages=final_messages,
            temperature=0.2,
            max_tokens=2048
        )
        llm_response = response.choices[0].message.content
        
    except (MistralAPIException, Exception) as e:
        llm_response = f"❌ Erreur de l'API Mistral : Veuillez réessayer plus tard. Détails: {e}"
        logging.error(f"Erreur API Mistral/inattendue: {e}")
    
    # 6. Enregistrement de l'Interaction
    
    # Métadonnées pour le log/base de données
    metadata = {
        "user_session_id": user_id,
        "username": username,
        "conversation_id": current_conversation_id,
        "mode": "RAG" if needs_rag else "DIRECT",
        "confidence": confidence,
        "reason": reason,
        "rewritten_query": rewritten_query,
        "rewrite_history_used": is_rewritten,
        "llm_model": CHAT_MODEL
    }
    
    interaction_id = session_service.log_interaction(
        query=user_query,
        response=llm_response,
        sources=sources_for_log,
        metadata=metadata
    )
    
    return llm_response, sources_for_log, metadata, interaction_id

# --- Streamlit UI / Logique d'Affichage (nettoyée) ---

# Initialisation de la session et de l'état
username, user_session_id = ensure_user_identity()

# Sécuriser la session courante pour l'utilisateur actuel (évite de voir l'historique d'un autre)
if session_data.get("owner") not in (None, user_session_id):
    start_new_conversation(toast=False)
else:
    session_data["owner"] = user_session_id

_ = get_session_id()

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "current_interaction_id" not in st.session_state:
    st.session_state["current_interaction_id"] = None


st.title(f"🤖 {APP_TITLE}")
st.subheader(f"Assistant Contextuel pour la {COMMUNE_NAME}")

with st.sidebar:
    render_history_sidebar(
        session_store=session_store,
        current_session_id=CURRENT_SESSION_ID,
        user_session_id=user_session_id,
        now_utc=now_utc,
        start_new_conversation=start_new_conversation,
        logout_user=logout_user,
        delete_conversation=delete_conversation,
        display_username=username,
    )
# Affichage des messages précédents
for msg_index, message in enumerate(st.session_state["messages"]):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            stored_sources = message.get("sources") or []
            if stored_sources:
                render_source_selector(
                    sources=stored_sources,
                    block_key=f"history_{msg_index}",
                    default_expanded=False,
                )
            else:
                st.info("Aucune source associée à cette réponse.")

# Entrée utilisateur
if prompt := st.chat_input("Posez votre question..."):
    
    current_time = datetime.datetime.now(datetime.timezone.utc)
    current_conversation_id = get_conversation_key(user_session_id, current_time)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
    st.session_state["messages"].append({"role": "user", "content": prompt, "metadata": {}})
    
    conversation_messages = [
        (m["role"], m["content"]) 
        for m in st.session_state["messages"] 
        if m["role"] in ["user", "assistant"]
    ]

    # Traitement principal
    with st.chat_message("assistant"):
        with st.spinner("🧠 Réflexion en cours..."):
            
            response, sources, metadata, interaction_id = process_query(
                prompt, user_session_id, username, conversation_messages[:-1], current_conversation_id
            )
            
            st.markdown(response)
            
            with st.expander("🔬 Débogage RAG Avancé"):
                mode_label = metadata.get("mode", "DIRECT")
                confidence = metadata.get("confidence")
                reason_label = metadata.get("reason", "N/A")
                if confidence is not None:
                    st.write(f"**Mode de réponse :** **`{mode_label}`** (Confiance: {confidence:.2f})")
                else:
                    st.write(f"**Mode de réponse :** **`{mode_label}`**")
                st.write(f"**Raison de la classification :** `{reason_label}`")
                
                rewritten_query = metadata.get("rewritten_query", prompt)
                if metadata.get("rewrite_history_used"):
                    st.success(f"**Requête Réécrite (RAG Conversationnel) :** `{rewritten_query}`")
                else:
                    st.info(f"**Requête Utilisée :** `{rewritten_query}`")
                
                st.write(f"**ID Interaction :** `{interaction_id}`")
                
            if sources:
                st.markdown("---")
                render_source_selector(
                    sources=sources,
                    block_key=f"live_{interaction_id or current_conversation_id}",
                    default_expanded=False,
                )
            else:
                st.caption("Aucune source documentaire n'a été nécessaire pour cette réponse.")


    st.session_state["messages"].append({
        "role": "assistant", 
        "content": response, 
        "metadata": metadata,
        "sources": sources
    })
    
    st.session_state["current_interaction_id"] = interaction_id
    st.session_state[f"feedback_submitted_{interaction_id}"] = False

    persist_session_state()
    
    st.rerun() 

# --- Gestion du Feedback Utilisateur ---

def handle_user_feedback():
    """Gère l'affichage et la soumission du feedback utilisateur."""
    current_interaction_id = st.session_state.get("current_interaction_id")
    
    if current_interaction_id is not None:
        
        feedback_submitted_key = f"feedback_submitted_{current_interaction_id}"
        
        if not st.session_state.get(feedback_submitted_key, False):
            st.markdown("---")
            
            feedback = streamlit_feedback(
                feedback_type="thumbs",
                optional_text_label="Avez-vous un commentaire à ajouter?",
                key=f"feedback_{current_interaction_id}",
            )

            if feedback:
                raw_score = feedback.get("score")
                normalized_score = None

                if isinstance(raw_score, str):
                    stripped_score = raw_score.strip()
                    score_lower = stripped_score.lower()
                    score_map = {
                        "positive": "positive",
                        "thumbs_up": "positive",
                        "thumbsup": "positive",
                        "up": "positive",
                        "1": "positive",
                        "+1": "positive",
                        "true": "positive",
                        "negative": "negative",
                        "thumbs_down": "negative",
                        "thumbsdown": "negative",
                        "down": "negative",
                        "-1": "negative",
                        "false": "negative",
                        "0": "negative",
                    }
                    normalized_score = score_map.get(score_lower)
                    if normalized_score is None:
                        emoji_map = {"👍": "positive", "👎": "negative"}
                        normalized_score = emoji_map.get(stripped_score)
                elif isinstance(raw_score, bool):
                    normalized_score = "positive" if raw_score else "negative"
                elif isinstance(raw_score, (int, float)):
                    if raw_score > 0:
                        normalized_score = "positive"
                    elif raw_score < 0:
                        normalized_score = "negative"

                if normalized_score is None and raw_score is not None:
                    logging.warning("Feedback score non reconnu: %r", raw_score)

                feedback_value = 1 if normalized_score == "positive" else 0 if normalized_score == "negative" else None
                feedback_text = ("positif" if normalized_score == "positive" else "négatif" if normalized_score == "negative" else "N/A")

                feedback_emoji = ("👍" if normalized_score == "positive" else "👎" if normalized_score == "negative" else "N/A")
                comment = feedback.get("text", None)

                success = session_service.update_feedback(
                    current_interaction_id, feedback_text, comment, feedback_value
                )
                if success:
                    st.toast(f"✅ Merci pour votre retour ({feedback_emoji}) ! Votre feedback aide à améliorer le RAG.", icon="✅")
                    st.session_state[feedback_submitted_key] = True
                    persist_session_state()
                    st.rerun()
                else:
                    st.toast("❌ Erreur lors de l'enregistrement de votre retour.", icon="❌")
        else:
            st.success("✅ Merci ! Votre feedback a été pris en compte.")
    else:
        st.info("💬 Posez une question pour pouvoir donner votre avis sur la réponse.")

handle_user_feedback()
persist_session_state(update_activity=False)
# Assurez-vous d'avoir le code CSS complet au début du fichier (pour Streamlit)
