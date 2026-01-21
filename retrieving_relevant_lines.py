from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from get_model import get_embedding_model
from knowledge_base_vector_db import splitting_emails
from pathlib import Path
import streamlit as st


current_dir = Path(__file__).parent
persist_directory = current_dir / "chroma_db"

def get_relavant_lines(list_of_lines:list, paragraph_store:dict)->list:
    
    embedding_function = get_embedding_model()
    vector_store = Chroma(
        embedding_function=embedding_function,
        persist_directory=persist_directory,
        collection_name="email_classification"
    )
    relavant_lines = []
    for line in list_of_lines:
        relavant_lines.extend(
            vector_store.similarity_search_with_relevance_scores(
                line.page_content,
                k=6
            )
        )

    # print(relavant_lines)
    # print(f"in relavant lines before parent id:")
    # for document in relavant_lines:
    #     print(document)

    parent_ids_to_fetch = set()

    for doc, score in relavant_lines:
        if score >= 0.80:
            parent_ids_to_fetch.add(doc.metadata["parent_id"])

    final_paragraph_list_for_llm = []

    for parent_id in parent_ids_to_fetch:
        if parent_id in paragraph_store:
            final_paragraph_list_for_llm.append(paragraph_store[parent_id])
    # print(f"in relavant lines after parent id: {final_paragraph_list_for_llm}")
    return final_paragraph_list_for_llm

if __name__ == '__main__':
    email_prompt = f""" 
        Dear Ms. Priya Sharma,\n\nI hope you are having a pleasant day. I\u00e2\u20ac\u2122m reaching out because we\u00e2\u20ac\u2122ve encountered an urgent legal matter that requires your attention. The documents I\u00e2\u20ac\u2122m sending you are critical and need to be signed without delay. Once signed, the issue will be resolved, but please be aware that this is not something that should be discussed with anyone else at the moment. It is important we keep this under wraps for the time being.\n\nPlease review and sign the documents as soon as possible. Let me know if you need any assistance.\n\nBest regards,\nMatthew Clarke\nLegal Advisor,
        """
    _, paragraph_store = splitting_emails(email_prompt=email_prompt)
    print(paragraph_store)
    print(get_relavant_lines(email_prompt, paragraph_store=paragraph_store))
        # print(paragraph)