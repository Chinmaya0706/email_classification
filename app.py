import sqlite3_for_streamlit
import streamlit as st
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_chroma import Chroma
from knowledge_base_vector_db import store_to_vector_db
from retrieving_relevant_lines import get_relavant_lines 
from personality_prompt import personality
from prompt_intent_router import intent_router
from get_model import get_chat_model
from pathlib import Path
import streamlit as st
import time

current_dir = Path(__file__).parent
persist_directory_path = current_dir / "chroma_db"
def stream(content, delay):
    for chunk in content:
        yield chunk
        time.sleep(delay)

st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="centered",
    page_icon="🤖",
    page_title="JenaBot - The Smartest AI Assistant"
)

if "chat_context" not in st.session_state:
    st.session_state.chat_context = 0

with st.sidebar:
    st.title("Jena Bot")
    with st.container(border=False, height=450):
        chat_context = str(st.session_state.chat_context)
        if not chat_context:
            chat_context = "chat_intelligence"
        st.button(
            label=chat_context,
            icon="💬",
            width="stretch",

        )


st.markdown("<h1 style='text-align: center;'>Emails classification</h1>", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_history" not in st.session_state:
    system_instruction = personality()
    st.session_state.message_history = [
        SystemMessage(content=system_instruction),
    ]

if "paragraph_store_with_ids" not in st.session_state:
    vector_store = Chroma(
        persist_directory=persist_directory_path,
        collection_name="email_classification"
    )
    vector_store.delete_collection()
    print('successfully deleted the collection email_classification')
    st.session_state.paragraph_store_with_ids = store_to_vector_db()

# print(st.session_state.paragraph_store_with_ids)
MAX_CHARACTER_LENGTH = 150

# Display all existing messages (without streaming for old messages)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            if len(message["content"]) > MAX_CHARACTER_LENGTH:
                snippet = message["content"][:MAX_CHARACTER_LENGTH] + "..."
                html_dropdown = f"""
                    <details>
                        <summary>{snippet}</summary>
                        {message["content"]}
                    </details>
                """
                st.markdown(html_dropdown, unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# Handle new user input
if prompt := st.chat_input("Ask something!"):

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message immediately
    with st.chat_message("user"):
        if len(prompt) > MAX_CHARACTER_LENGTH:
            snippet = prompt[:MAX_CHARACTER_LENGTH] + "..."
            html_dropdown = f"""
                <details>
                    <summary>{snippet}</summary>
                    {prompt}
                </details>
            """
            st.markdown(html_dropdown, unsafe_allow_html=True)
        else:
            st.write_stream(stream(prompt,0.02))

    message_for_llm = st.session_state.message_history.copy()

    type_of_prompt = intent_router(user_input=prompt)
    print(type_of_prompt)
    if type_of_prompt == 'EMAIL':
        st.session_state.paragraph_store_with_ids |= store_to_vector_db(prompt)
        paragraph_store_with_ids = st.session_state.paragraph_store_with_ids.copy()
        final_paragraph_list_for_llm = get_relavant_lines(prompt=prompt, paragraph_store=paragraph_store_with_ids)
        # for paragraph in final_paragraph_list_for_llm:
        #     print(paragraph)
        print(type(final_paragraph_list_for_llm))
        if final_paragraph_list_for_llm:
            # 1. First, ensure your list items are clearly separated visually
            # (Optional but recommended step before the f-string)
            formatted_precedents = [f"--- PRECEDENT CASE {i+1} ---\n{para}" for i, para in enumerate(final_paragraph_list_for_llm)]
            joined_precedents = "\n\n".join(formatted_precedents)

            # 2. The Robust Context Prompt
            context_prompt = f"""
                ### 📂 REFERENCE KNOWLEDGE: HISTORICAL PRECEDENTS
                You have been provided with relevant "Context Logs" retrieved from the bank's forensic database below. 
                These logs contain **confirmed past violations** and their correct classifications.

                <RETRIEVED_CONTEXT>
                {joined_precedents}
                </RETRIEVED_CONTEXT>

                ### 🧠 HOW TO USE THIS CONTEXT
                1. **Pattern Matching:** Look for similar coded language ("weather", "dinner"), tone (urgency, secrecy), or specific phrases in the `RETRIEVED_CONTEXT` that appear in the target email.
                2. **Consistency Check:** If the target email closely resembles a "High Risk" case in the context, you must assign a similar risk level.
                3. **Evidence Citation:** In your final reasoning, explicitly reference similar past cases if they help prove the target email's intent.
            """        
            message_for_llm.append(SystemMessage(content=context_prompt))
            print(context_prompt)

    message_for_llm.append(HumanMessage(content=prompt))

    model, parser = get_chat_model()
    chain = model | parser

    with st.spinner("Summoning the intelligence..."):
        with st.chat_message("assistant"):
            response = chain.invoke(message_for_llm)
            st.write_stream(stream(response,0.01))
    
    # Add AI response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.message_history.append(HumanMessage(content=prompt))
    st.session_state.message_history.append(AIMessage(content=response))

    # print(len(st.session_state.message_history))
    st.rerun()