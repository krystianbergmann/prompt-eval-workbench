"""
Streamlit chat: solo OpenAI chat + two-model dialogues with Langfuse logging.
"""

import os
import uuid

from dotenv import load_dotenv

load_dotenv()

import langfuse.openai  # noqa: F401

from langfuse import get_client, propagate_attributes
from openai import OpenAI
import streamlit as st

from chat_logic import MODELS, format_transcript

st.set_page_config(page_title="Chat (Langfuse)", page_icon="💬")


def init_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "duel_transcript" not in st.session_state:
        st.session_state.duel_transcript = []
    if "duel_next_speaker" not in st.session_state:
        st.session_state.duel_next_speaker = "A"


init_session()


def run_model_turn(
    client: OpenAI,
    *,
    speaker: str,
    system: str,
    model: str,
    topic: str,
    transcript_rows: list[dict],
    session_id: str,
    tag: str,
) -> str:
    transcript = format_transcript(transcript_rows)
    if not transcript_rows:
        user_msg = (
            f"Topic for the dialogue:\n{topic}\n\n"
            f"You are Model {speaker}. Start the conversation with one short message."
        )
    else:
        user_msg = (
            f"Original topic:\n{topic}\n\n"
            f"Conversation so far:\n{transcript}\n\n"
            f"You are Model {speaker}. Reply with one short message only."
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]

    with propagate_attributes(
        session_id=session_id,
        tags=["streamlit-chat", tag],
        metadata={"model_label": f"speaker_{speaker}"},
    ):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

    return (response.choices[0].message.content or "").strip()


client = OpenAI()

st.title("Chat Lab")
st.caption("OpenAI + Langfuse. Solo chat or two models talking to each other.")

with st.sidebar:
    st.subheader("Solo chat")
    model_solo = st.selectbox("Model (solo)", MODELS, index=0, key="solo_model")
    system_solo = st.text_area(
        "Instructions (solo)",
        value="You are a helpful assistant.",
        height=80,
        key="solo_system",
    )

    st.divider()
    st.subheader("Two-model dialogue")
    duel_topic = st.text_area(
        "Topic / scenario",
        value="Two friends debate whether cats or dogs make better pets.",
        height=70,
        key="duel_topic",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        model_a = st.selectbox("Model A", MODELS, index=0, key="m_a")
    with col_b:
        model_b = st.selectbox("Model B", MODELS, index=min(1, len(MODELS) - 1), key="m_b")
    system_a = st.text_area(
        "Persona / instructions — A",
        value="You are Model A: enthusiastic and brief.",
        height=70,
        key="sys_a",
    )
    system_b = st.text_area(
        "Persona / instructions — B",
        value="You are Model B: skeptical but fair, keep replies short.",
        height=70,
        key="sys_b",
    )

    if st.button("New solo conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    if st.button("Reset two-model dialogue"):
        st.session_state.duel_transcript = []
        st.session_state.duel_next_speaker = "A"
        st.rerun()

    pk = os.environ.get("LANGFUSE_PUBLIC_KEY")
    st.caption(
        "Langfuse: **on**"
        if pk
        else "Langfuse: **off** (set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in `.env`)"
    )

tab_solo, tab_manual, tab_auto = st.tabs(
    ["Solo chat", "Two models (manual)", "Automated dialogue"]
)

with tab_solo:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Message", key="solo_input"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Waiting for reply..."):
                api_messages = [{"role": "system", "content": system_solo}]
                api_messages.extend(st.session_state.messages)

                with propagate_attributes(
                    session_id=st.session_state.session_id,
                    tags=["streamlit-chat", "solo"],
                ):
                    response = client.chat.completions.create(
                        model=model_solo,
                        messages=api_messages,
                    )

                reply = response.choices[0].message.content or ""
            st.markdown(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})
        get_client().flush()

with tab_manual:
    st.markdown(
        f"**Next turn:** Model **{st.session_state.duel_next_speaker}** — click the button below."
    )
    for row in st.session_state.duel_transcript:
        avatar = "🅰" if row["speaker"] == "A" else "🅱"
        label = "Model A" if row["speaker"] == "A" else "Model B"
        with st.chat_message("assistant", avatar=avatar):
            st.caption(label)
            st.markdown(row["content"])

    duel_sid = f"{st.session_state.session_id}-duel"

    if st.button("Speak next line (manual turn)", type="primary", key="duel_step"):
        sp = st.session_state.duel_next_speaker
        if not duel_topic.strip():
            st.error("Set a topic in the sidebar.")
        else:
            model = model_a if sp == "A" else model_b
            system = system_a if sp == "A" else system_b
            with st.spinner(f"Model {sp} is thinking..."):
                text = run_model_turn(
                    client,
                    speaker=sp,
                    system=system,
                    model=model,
                    topic=duel_topic.strip(),
                    transcript_rows=list(st.session_state.duel_transcript),
                    session_id=duel_sid,
                    tag="duel-manual",
                )
            st.session_state.duel_transcript.append({"speaker": sp, "content": text})
            st.session_state.duel_next_speaker = "B" if sp == "A" else "A"
            get_client().flush()
            st.rerun()

with tab_auto:
    st.write(
        "Each **interaction** is one full round: Model A speaks, then Model B. "
        "The dialogue starts fresh when you run (same topic as in the sidebar)."
    )
    num_interactions = st.number_input(
        "Number of interactions (A→B rounds)",
        min_value=1,
        max_value=30,
        value=3,
        step=1,
        key="auto_n",
    )

    duel_sid = f"{st.session_state.session_id}-duel-auto"

    if st.button("Run automated dialogue", type="primary", key="auto_run"):
        if not duel_topic.strip():
            st.error("Set a topic in the sidebar.")
        else:
            transcript: list[dict] = []
            progress = st.progress(0.0)
            total_steps = num_interactions * 2
            step_i = 0
            for _ in range(int(num_interactions)):
                for sp in ("A", "B"):
                    model = model_a if sp == "A" else model_b
                    system = system_a if sp == "A" else system_b
                    text = run_model_turn(
                        client,
                        speaker=sp,
                        system=system,
                        model=model,
                        topic=duel_topic.strip(),
                        transcript_rows=transcript,
                        session_id=duel_sid,
                        tag="duel-auto",
                    )
                    transcript.append({"speaker": sp, "content": text})
                    step_i += 1
                    progress.progress(step_i / total_steps)

            st.session_state.duel_transcript = transcript
            st.session_state.duel_next_speaker = (
                "A" if transcript and transcript[-1]["speaker"] == "B" else "B"
            )
            get_client().flush()
            progress.empty()
            st.success("Done — see **Two models (manual)** tab for the same transcript, or scroll below.")

            for row in transcript:
                avatar = "🅰" if row["speaker"] == "A" else "🅱"
                label = "Model A" if row["speaker"] == "A" else "Model B"
                with st.chat_message("assistant", avatar=avatar):
                    st.caption(label)
                    st.markdown(row["content"])
