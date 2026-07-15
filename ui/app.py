"""
Secure Cloud RAG Assistant — interfaccia minimale.

Sola chat. Client HTTP puro dell'API FastAPI: nessun import della pipeline.
Identita' e configurazione dei livelli difensivi sono costanti: l'identita' e'
assunta autenticata a monte (cfr. Cap. 7) e la pipeline gira nella
configurazione completa C7.
"""

from __future__ import annotations

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000/query"
TIMEOUT_S = 120

IDENTITY = {"role": "developer", "clearance": "internal"}

def ask(query: str) -> str:
    """Interroga l'API e restituisce la risposta, o un messaggio di errore."""
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "identity": IDENTITY},
            timeout=TIMEOUT_S,
        )
    except requests.exceptions.ConnectionError:
        return f"Nessuna risposta da {API_URL}. Verifica che l'API sia in esecuzione."
    except requests.exceptions.Timeout:
        return f"Timeout dopo {TIMEOUT_S} s."
    except requests.exceptions.RequestException as exc:
        return f"Errore di rete: {exc}"

    if response.status_code != 200:
        return f"HTTP {response.status_code} — {response.text[:300]}"

    try:
        payload = response.json()
    except ValueError:
        return "La risposta non è JSON valido."

    return payload.get("answer") or payload.get("response") or "_(risposta vuota)_"


def main() -> None:
    st.set_page_config(page_title="Secure Cloud RAG Assistant", page_icon="🛡️")
    st.title("Secure Cloud RAG Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Interroga l'assistente")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"), st.spinner("Interrogazione in corso"):
        answer = ask(prompt)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()