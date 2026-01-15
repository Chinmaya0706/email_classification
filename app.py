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
from langchain_community.document_loaders import DataFrameLoader
from pathlib import Path
from context_for_llm import get_context
from csv_call import csv_summary
import streamlit as st
import pandas as pd
import time
import os

current_dir = Path(__file__).parent
persist_directory_path = current_dir / "chroma_db"
new_csv_file_path = current_dir / "result" / "result_csv.csv"
def stream(content, delay):
    for chunk in content:
        yield chunk
        time.sleep(delay)

st.set_page_config(
    initial_sidebar_state="collapsed",
    layout="centered",
    page_icon="🤖",
    page_title="Email classification"
)

if "chat_context" not in st.session_state:
    st.session_state.chat_context = 0

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
    _, st.session_state.paragraph_store_with_ids = store_to_vector_db()

with st.sidebar:
    st.header("Upload Email CSV files")
    with st.container(border=False, height=450):
        file_upload = st.file_uploader(label="upload only CSV files", type="csv", label_visibility="hidden")
        # print(f"name of csv file is : {file_upload}")
        # print(f"type of csv file is {type(file_upload)}")

        if file_upload:
            original_name = file_upload.name
            new_filename = f"{os.path.splitext(original_name)[0]}_result.csv"
            if 'input_data' not in st.session_state:
                st.session_state['input_data'] = pd.read_csv(file_upload)

            df = st.session_state['input_data']
            # print("columns of csv file are :", df.columns)
            if "body" not in df.columns.str.lower():
                st.error("❌ Error: The uploaded CSV file must contain a column named 'body'.")
                st.stop()
            col1, col2 = st.columns([1,2])
            with col1:
                if st.button(label='Result'):
                    if "processed_df" not in st.session_state:
                        st.session_state.processed_df = csv_summary(
                            df=df, 
                            knowledge_paragraph_store=st.session_state.paragraph_store_with_ids
                        )

            with col2:
                # Check if we have a processed result ready in memory
                if 'processed_df' in st.session_state:
                    processed_df = st.session_state['processed_df']
                    
                    # Convert DF to CSV string (RAM only, no disk save needed!)
                    csv_data = processed_df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="Download 📥",
                        data=csv_data,
                        file_name=new_filename, # Use the dynamic name we created
                        mime="text/csv"
                    )
            
                    # st.success("File Loaded into RAM!", icon="✅")
                # csv_dataframe = pd.read_csv(file_upload, index_col=None)
                # st.write(csv_dataframe)

st.markdown("<h1 style='text-align: center;'>Emails classification</h1>", unsafe_allow_html=True)



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
    # print(type_of_prompt)
    if type_of_prompt == 'EMAIL':
        child_lines, paragraph_store_with_ids = store_to_vector_db(email_prompt = prompt)
        st.session_state.paragraph_store_with_ids |= paragraph_store_with_ids
        paragraph_store_with_ids = st.session_state.paragraph_store_with_ids.copy()
        final_paragraph_list_for_llm = get_relavant_lines(list_of_lines=child_lines, paragraph_store=paragraph_store_with_ids)
        # for paragraph in final_paragraph_list_for_llm:
        #     print(paragraph)
        # print(type(final_paragraph_list_for_llm))
        if final_paragraph_list_for_llm:
            context_prompt = get_context(final_paragraph_list_for_llm)        
            message_for_llm.append(SystemMessage(content=context_prompt))
            # print(context_prompt)

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