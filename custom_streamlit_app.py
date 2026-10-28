import hashlib
import json
import os
import uuid
from datetime import datetime

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

DEFAULT_SYSTEM = "You are a helpful assistant."
USER_AVATAR = ":material/person:"
BOT_AVATAR = ":material/auto_awesome:"

st.set_page_config(
    page_title="Custom ChatGPT", page_icon=":material/chat_bubble:", layout="wide"
)

# ---------- Theme: soft lavender / peach, clean and minimal ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp, button, input, textarea {
        font-family: 'Inter', sans-serif !important;
    }

    /* hide only Deploy / menu, keep the sidebar open-close button */
    [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
    [data-testid="stDecoration"], footer { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; }

    .stApp {
        background: linear-gradient(180deg, #e0d9ff 0%, #f1ecff 50%, #fde8e0 100%);
        background-attachment: fixed;
        color: #1f1b2e;
    }

    /* sidebar open / close buttons */
    [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {
        display: flex !important; visibility: visible !important; opacity: 1 !important;
    }
    [data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapseButton"] *,
    [data-testid="collapsedControl"] *, [data-testid="stSidebarCollapsedControl"] * {
        color: #7c4dff !important;
    }

    /* centered column */
    .block-container { max-width: 760px; padding-top: 2rem; padding-bottom: 6rem; }
    [data-testid="stBottom"], [data-testid="stBottom"] > div { background: transparent !important; }
    [data-testid="stBottomBlockContainer"] { max-width: 760px; margin: 0 auto; }

    /* ---------- sidebar ---------- */
    [data-testid="stSidebar"] {
        background: rgba(255,255,255,0.72);
        backdrop-filter: blur(10px);
        border-right: 1px solid #e6e0f7;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        justify-content: flex-start;
        text-align: left;
        background: transparent;
        border: none;
        color: #3a3550;
        border-radius: 10px;
        padding: 0.4rem 0.65rem;
        font-size: 0.9rem;
        font-weight: 500;
        box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton > button p {
        overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #f0eaff; color: #5b34d6;
    }
    .st-key-active_chat_btn button {
        background: #ebe3ff !important; color: #5b34d6 !important; font-weight: 600 !important;
    }
    [class*="st-key-del_"] button {
        justify-content: center !important; opacity: 0.35; padding: 0.4rem 0 !important;
    }
    [class*="st-key-del_"] button:hover { opacity: 1; color: #d33 !important; background: #fdecec !important; }
    .st-key-new_chat_btn button {
        background: #1f1b2e !important; color: #fff !important; font-weight: 600 !important;
        justify-content: center !important; border-radius: 12px !important; padding: 0.55rem !important;
    }
    .st-key-new_chat_btn button:hover { background: #7c4dff !important; }
    .st-key-logout_btn button { color: #8a849c !important; }

    .sb-brand { display: flex; align-items: center; gap: 0.6rem; margin: 0.2rem 0 1rem 0.2rem; }
    .sb-logo {
        width: 28px; height: 28px; border-radius: 9px;
        background: linear-gradient(135deg, #7c4dff, #b79cff);
        box-shadow: 0 4px 10px rgba(124,77,255,0.35);
    }
    .sb-name { font-size: 1.05rem; font-weight: 700; color: #1f1b2e; letter-spacing: -0.01em; }
    .sb-label {
        color: #9a94b0; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em;
        text-transform: uppercase; margin: 1.2rem 0 0.35rem 0.5rem;
    }
    [data-testid="stSidebar"] [data-testid="stTextInput"] input {
        border-radius: 10px; font-size: 0.9rem;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid #e6e0f7; border-radius: 12px; background: rgba(255,255,255,0.6);
    }

    /* ---------- greeting ---------- */
    .greeting {
        text-align: center; margin: 17vh 0 1.8rem 0;
    }
    .greeting h1 {
        font-size: 2.2rem; font-weight: 600; letter-spacing: -0.02em;
        color: #1f1b2e; margin: 0; padding: 0;
    }
    .greeting h1 span { color: #7c4dff; }
    .greeting p { color: #8a849c; font-size: 1rem; margin: 0.5rem 0 0 0; }

    /* ---------- messages ---------- */
    [data-testid="stChatMessage"] {
        background: transparent; border: none; box-shadow: none;
        padding: 0.35rem 0; color: #1f1b2e;
    }
    /* assistant: clean text with a small avatar */
    [data-testid="stChatMessageAvatarAssistant"] {
        background: #ffffff !important; color: #7c4dff !important;
        border-radius: 50% !important;
        box-shadow: 0 2px 8px rgba(124,77,255,0.18);
    }
    [data-testid="stChatMessageAvatarAssistant"] * { color: #7c4dff !important; }
    /* user: right-aligned purple bubble, no avatar */
    [data-testid="stChatMessageAvatarUser"] { display: none !important; }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        margin-left: auto;
        width: fit-content;
        max-width: 80%;
        background: linear-gradient(135deg, #7c4dff, #9a73ff);
        border-radius: 20px 20px 6px 20px;
        padding: 0.65rem 1.05rem;
        box-shadow: 0 6px 16px rgba(124,77,255,0.25);
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) * {
        color: #ffffff !important;
    }

    /* ---------- input ---------- */
    [data-testid="stChatInput"] {
        border-radius: 26px;
        border: 1px solid #ddd3fb;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(124,77,255,0.14);
    }
    [data-testid="stChatInput"] textarea { color: #1f1b2e; font-size: 0.97rem; }
    [data-testid="stChatInputSubmitButton"] {
        background: #7c4dff !important; color: #fff !important; border-radius: 50% !important;
    }
    [data-testid="stChatInputSubmitButton"]:hover { background: #5b34d6 !important; }

    /* ---------- login ---------- */
    .login-title { text-align: center; font-size: 2rem; font-weight: 700; letter-spacing: -0.02em; color: #1f1b2e; }
    .login-title span { color: #7c4dff; }
    .login-sub { text-align: center; color: #8a849c; margin-bottom: 1.2rem; }
    [data-testid="stForm"] {
        background: #ffffff; border: 1px solid #e6e0f7; border-radius: 20px;
        box-shadow: 0 12px 34px rgba(124,77,255,0.14); padding: 1.5rem;
    }
    .stFormSubmitButton button {
        background: #1f1b2e !important; color: #fff !important; border: none !important;
        border-radius: 12px !important; font-weight: 600; padding: 0.55rem !important;
    }
    .stFormSubmitButton button:hover { background: #7c4dff !important; }

    /* ---------- force light colors (works even if config.toml is missing) ---------- */
    html, body, .stApp { color-scheme: light !important; }
    .stApp, .stApp label, .stApp .stMarkdown, .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stWidgetLabel"] p, .stApp [data-testid="stCaptionContainer"] {
        color: #1f1b2e;
    }
    [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
        background: #ffffff !important;
        color: #1f1b2e !important;
        -webkit-text-fill-color: #1f1b2e !important;
    }
    [data-baseweb="input"] { border: 1px solid #ddd3fb !important; border-radius: 10px !important; }
    input::placeholder, textarea::placeholder {
        color: #9a94b0 !important; -webkit-text-fill-color: #9a94b0 !important;
    }
    [data-testid="stChatInput"], [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #1f1b2e !important;
        -webkit-text-fill-color: #1f1b2e !important;
    }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {
        color: #1f1b2e !important;
    }
    [data-testid="stExpander"] details { background: transparent !important; }

    /* ---------- colour fixes (do not depend on config.toml) ---------- */
    /* button labels keep the button's own colour */
    button [data-testid="stMarkdownContainer"], button [data-testid="stMarkdownContainer"] p {
        color: inherit !important;
    }
    .st-key-new_chat_btn button, .st-key-new_chat_btn button *,
    [data-testid="stSidebar"] .st-key-new_chat_btn button p,
    [data-testid="stSidebar"] .st-key-new_chat_btn button span,
    [data-testid="stSidebar"] .st-key-new_chat_btn [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stFormSubmitButton button, .stFormSubmitButton button * { color: #ffffff !important; }
    .st-key-active_chat_btn button, .st-key-active_chat_btn button * { color: #5b34d6 !important; }

    /* purple focus instead of Streamlit's default red / black */
    [data-baseweb="input"], [data-baseweb="base-input"] { outline: none !important; box-shadow: none !important; }
    [data-baseweb="input"]:focus-within {
        border-color: #7c4dff !important;
        box-shadow: 0 0 0 3px rgba(124,77,255,0.18) !important;
    }
    [data-baseweb="base-input"] { border: none !important; }
    [data-testid="stChatInput"] > div, [data-testid="stChatInput"]:focus-within > div {
        border: none !important; box-shadow: none !important; outline: none !important;
        border-radius: 26px !important;
    }

    /* greeting colours */
    .greeting h1 { color: #1f1b2e !important; }
    .greeting h1 span { color: #7c4dff !important; }

    /* ---------- animations ---------- */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: none; }
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes bgShift {
        0%   { background-position: 50% 0%; }
        100% { background-position: 50% 100%; }
    }
    @keyframes floaty {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-2px); }
    }
    @keyframes glow {
        0%, 100% { box-shadow: 0 4px 10px rgba(124,77,255,0.30); }
        50%      { box-shadow: 0 4px 18px rgba(124,77,255,0.55); }
    }
    @keyframes dotBounce {
        0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
        40%           { transform: translateY(-5px); opacity: 1; }
    }

    .stApp { background-size: 100% 220%; animation: bgShift 22s ease-in-out infinite alternate; }

    /* entrances */
    [data-testid="stChatMessage"] { animation: fadeUp 0.32s ease both; }
    .greeting h1 { animation: fadeUp 0.6s ease both; }
    .greeting p  { animation: fadeUp 0.6s ease 0.15s both; }
    .login-title, .login-sub { animation: fadeUp 0.6s ease both; }
    [data-testid="stForm"] { animation: fadeUp 0.7s ease 0.1s both; }
    [data-testid="stSidebar"] .stButton { animation: fadeIn 0.4s ease both; }

    /* logo */
    .sb-logo { animation: floaty 3.5s ease-in-out infinite, glow 3.5s ease-in-out infinite; }

    /* smooth hovers */
    [data-testid="stSidebar"] .stButton > button,
    .stFormSubmitButton button,
    [data-testid="stChatInput"],
    [data-testid="stChatInputSubmitButton"] {
        transition: all 0.22s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover { transform: translateX(3px); }
    .st-key-new_chat_btn button:hover { transform: translateY(-1px) !important; box-shadow: 0 8px 18px rgba(124,77,255,0.35); }
    .stFormSubmitButton button:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(124,77,255,0.35); }
    [data-testid="stChatInput"]:focus-within {
        border-color: #b79cff;
        box-shadow: 0 14px 38px rgba(124,77,255,0.28);
        transform: translateY(-2px);
    }
    [data-testid="stChatInputSubmitButton"]:hover { transform: scale(1.1); }

    /* typing indicator */
    .typing { display: flex; gap: 6px; padding: 0.55rem 0.2rem; }
    .typing span {
        width: 8px; height: 8px; border-radius: 50%; background: #7c4dff;
        animation: dotBounce 1.2s infinite ease-in-out;
    }
    .typing span:nth-child(2) { animation-delay: 0.15s; }
    .typing span:nth-child(3) { animation-delay: 0.3s; }

    @media (prefers-reduced-motion: reduce) {
        * { animation: none !important; transition: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Storage (chats survive server restart) ----------
def db_path():
    # each API key gets its own chat file, so users never see each other's chats
    digest = hashlib.sha256(st.session_state.api_key.encode()).hexdigest()[:16]
    return f"chats_{digest}.json"


def load_chats():
    path = db_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_chats():
    with open(db_path(), "w", encoding="utf-8") as f:
        json.dump(st.session_state.chats, f, ensure_ascii=False, indent=2)


def new_chat():
    cid = str(uuid.uuid4())
    st.session_state.chats[cid] = {
        "title": "New chat",
        "system": DEFAULT_SYSTEM,
        "messages": [],
        "updated": datetime.now().isoformat(),
    }
    st.session_state.active = cid
    save_chats()
    return cid


def sorted_chat_ids():
    chats = st.session_state.chats
    return sorted(chats, key=lambda c: chats[c].get("updated", ""), reverse=True)


# ---------- Session state ----------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "active" not in st.session_state:
    st.session_state.active = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ---------- Login gate: no access without an API key ----------
if not st.session_state.api_key:
    st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='login-title'>Custom <span>ChatGPT</span></div>"
        "<div class='login-sub'>Enter your OpenAI API key to continue</div>",
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        name_in = st.text_input("Your name (optional)", placeholder="e.g. Fatima")
        key_in = st.text_input("OpenAI API key", type="password", placeholder="sk-...")
        enter = st.form_submit_button("Enter", use_container_width=True)
    if enter:
        key_in = key_in.strip()
        if not key_in:
            st.error("API key is empty.")
        else:
            try:
                from openai import OpenAI

                with st.spinner("Checking your key..."):
                    OpenAI(api_key=key_in).models.list()
                st.session_state.api_key = key_in
                st.session_state.user_name = name_in.strip()
                st.session_state.chats = load_chats()
                ids = sorted_chat_ids()
                st.session_state.active = ids[0] if ids else None
                st.rerun()
            except Exception:
                st.error("This API key doesn't look valid. Please check it and try again.")
    st.caption("Your key is kept only for this session and is never saved to a file.")
    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown(
        "<div class='sb-brand'><div class='sb-logo'></div>"
        "<div class='sb-name'>Custom ChatGPT</div></div>",
        unsafe_allow_html=True,
    )

    if st.button("New chat", key="new_chat_btn", icon=":material/add:"):
        new_chat()
        st.rerun()

    search = st.text_input(
        "Search", placeholder="Search chats", label_visibility="collapsed"
    ).strip().lower()

    st.markdown("<div class='sb-label'>Recents</div>", unsafe_allow_html=True)
    shown = 0
    for cid in sorted_chat_ids():
        chat = st.session_state.chats[cid]
        if search and search not in chat["title"].lower():
            continue
        shown += 1
        is_active = cid == st.session_state.active
        c1, c2 = st.columns([6, 1])
        with c1:
            key = "active_chat_btn" if is_active else f"sel_{cid}"
            if st.button(chat["title"][:30], key=key):
                st.session_state.active = cid
                st.rerun()
        with c2:
            if st.button("", key=f"del_{cid}", icon=":material/close:"):
                del st.session_state.chats[cid]
                ids = sorted_chat_ids()
                st.session_state.active = ids[0] if ids else None
                save_chats()
                st.rerun()
    if shown == 0:
        st.caption("No chats found.")

    st.markdown("<div class='sb-label'>Settings</div>", unsafe_allow_html=True)
    with st.expander("Model & system role"):
        model_name = st.text_input("Model", value="gpt-5.2")
        active_id = st.session_state.active
        if active_id and active_id in st.session_state.chats:
            sys_val = st.text_area(
                "System role",
                value=st.session_state.chats[active_id]["system"],
                key=f"sys_{active_id}",
                height=110,
            )
            if sys_val != st.session_state.chats[active_id]["system"]:
                st.session_state.chats[active_id]["system"] = sys_val
                save_chats()
        else:
            st.caption("Start a chat first, then you can set the system role.")

    if st.button("Logout", key="logout_btn", icon=":material/logout:"):
        st.session_state.api_key = ""
        st.session_state.user_name = ""
        st.session_state.chats = {}
        st.session_state.active = None
        st.rerun()

# ---------- Main area ----------
active_id = st.session_state.active
chat = st.session_state.chats.get(active_id) if active_id else None
has_messages = bool(chat and chat["messages"])

prompt = None
holder = st.empty()

if has_messages:
    with holder.container():
        for m in chat["messages"]:
            avatar = USER_AVATAR if m["role"] == "user" else BOT_AVATAR
            with st.chat_message(m["role"], avatar=avatar):
                st.markdown(m["content"])
    prompt = st.chat_input("Reply...", key="input_bottom")
else:
    name = st.session_state.user_name
    title = f"Hello, <span>{name}</span>" if name else "How can I <span>help</span> you today?"
    with holder.container():
        st.markdown(
            f"<div class='greeting'><h1>{title}</h1>"
            "<p>Ask anything. I'm here to help.</p></div>",
            unsafe_allow_html=True,
        )
        prompt = st.chat_input("Message Custom ChatGPT...", key="input_center")

if prompt:
    if not chat:
        active_id = new_chat()
        chat = st.session_state.chats[active_id]

    if not has_messages:
        holder.empty()  # remove the greeting

    chat["messages"].append({"role": "user", "content": prompt})
    if chat["title"] == "New chat":
        chat["title"] = prompt.strip().replace("\n", " ")[:40]

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    history = [SystemMessage(content=chat["system"] or DEFAULT_SYSTEM)]
    for m in chat["messages"]:
        if m["role"] == "user":
            history.append(HumanMessage(content=m["content"]))
        else:
            history.append(AIMessage(content=m["content"]))

    try:
        llm = ChatOpenAI(model=model_name, api_key=st.session_state.api_key)
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            typing = st.empty()
            typing.markdown(
                "<div class='typing'><span></span><span></span><span></span></div>",
                unsafe_allow_html=True,
            )

            def token_stream():
                first = True
                for c in llm.stream(history):
                    if c.content:
                        if first:
                            typing.empty()  # remove the dots on the first token
                            first = False
                        yield c.content

            reply = st.write_stream(token_stream())
            typing.empty()
        chat["messages"].append({"role": "assistant", "content": reply})
        chat["updated"] = datetime.now().isoformat()
        save_chats()
        st.rerun()  # refresh sidebar (title / order)
    except Exception as e:
        chat["messages"].pop()
        save_chats()
        st.error(f"Error: {e}")