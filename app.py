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
import io
import json

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
        
        def reset_state():
            """This is for clearing the session state after uploading a new file"""
            keys = ["input_data", "processed_df"]
            for key in keys:
                if key in st.session_state:
                    del st.session_state[key]

        file_upload = st.file_uploader(
            label="upload only CSV files", 
            type="csv", 
            label_visibility="hidden",
            on_change=reset_state
        )
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
                            knowledge_paragraph_store=st.session_state.paragraph_store_with_ids,
                        )

            with col2:
                # Check if we have a processed result ready in memory
                if 'processed_df' in st.session_state:
                    processed_df = st.session_state['processed_df']
                    
                    # 1. Create a Buffer (RAM storage for the file)
                    output = io.BytesIO()
                    # engine='xlsxwriter' allows us to do cool formatting!
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        processed_df.to_excel(writer, index=False, sheet_name='Analysis_Result')
                        
                        # --- PRO TIP: Auto-Adjust Column Width & Text Wrap ---
                        workbook = writer.book
                        worksheet = writer.sheets['Analysis_Result']
                        
                        # Define a format: Wrap text so long emails look nice inside the box
                        wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                        
                        last_col_index = len(processed_df.columns) - 1

                        # 4. APPLY TO ALL COLUMNS (From 0 to last_col_index)
                        # This sets the width to 30 (more readable than 50 for small cols) and applies wrapping
                        worksheet.set_column(0, last_col_index, 30, wrap_format) 
                                            
                        # 3. Get the data from RAM
                    excel_data = output.getvalue()
                    
                    st.download_button(
                        label="Download📊",
                        data=excel_data,
                        file_name=new_filename.replace('.csv', '.xlsx'), # Change extension!
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
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
    print(type_of_prompt)
    
    child_lines, paragraph_store_with_ids = store_to_vector_db(type=None, email_prompt = prompt)
    if type_of_prompt == 'EMAIL':
        st.session_state.paragraph_store_with_ids |= paragraph_store_with_ids
    paragraph_store_with_ids = st.session_state.paragraph_store_with_ids.copy()
    final_paragraph_list_for_llm = get_relavant_lines(list_of_lines=child_lines, paragraph_store=paragraph_store_with_ids)
    # for paragraph in final_paragraph_list_for_llm:
    #     print(paragraph)
    # print(type(final_paragraph_list_for_llm))
    if final_paragraph_list_for_llm:
        context_prompt = get_context(final_paragraph_list_for_llm, mode=type_of_prompt) 
        print(f"context prompt is : \n{context_prompt}")       
        message_for_llm.append(SystemMessage(content=context_prompt))
    else:
        print("No final_paragraph_list_for_llm found!")
            # print(context_prompt)
    #for printing purpose
    if type_of_prompt == 'CHAT':
        if final_paragraph_list_for_llm:
            for paragraph in final_paragraph_list_for_llm:
                print(paragraph, '\n')
        else:
            print("No final_paragraph_list_for_llm for this chat")

    message_for_llm.append(HumanMessage(content=prompt))

    model, parser = get_chat_model()
    chain = model | parser

    with st.spinner("Summoning the intelligence..."):
        with st.chat_message("assistant"):
            response = chain.invoke(message_for_llm)
            if type_of_prompt == 'EMAIL':
                final_email_prompt_for_vector_db = {
                    "EMAIL_body" : prompt,
                    "Category_result" : response
                }
                child_lines, paragraph_store_with_ids = store_to_vector_db(email_prompt=str(final_email_prompt_for_vector_db))
                st.session_state.paragraph_store_with_ids |= paragraph_store_with_ids
            st.write_stream(stream(response,0.01))
    
    # Add AI response to session state
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.message_history.append(HumanMessage(content=prompt))
    st.session_state.message_history.append(AIMessage(content=response))

    # print(len(st.session_state.message_history))
    st.rerun()