from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma
from get_model import get_embedding_model
from pathlib import Path
import uuid
import json

current_dir = Path(__file__).parent
file_path = current_dir / "knowledge_data" / "knowledge_data.json"
with open(file_path, 'r') as file:
    emails = json.load(file)

def splitting_emails(email_prompt=None)->tuple[list[Document], dict]:
    paragraph_store = dict()
    all_child_lines_for_vectorDB = []
    child_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=800, 
        chunk_overlap = 50,
    )

    def child_line_splitting(email_body:str, parent_id:str)->list:
        child_lines_for_vectorDB = [] 
        child_lines = child_splitter.split_text(email_body)
        for line in child_lines:
            line_document = Document(
                page_content=line,
                metadata = {
                    "parent_id" : parent_id
                }
            )
            child_lines_for_vectorDB.append(line_document)
        return child_lines_for_vectorDB

    if email_prompt:
        parent_id = str(uuid.uuid4())
        all_child_lines_for_vectorDB = child_line_splitting(email_body=email_prompt, parent_id=parent_id)
        paragraph_store[parent_id] = email_prompt
    else:
        for email in emails:
            email_paragraph = json.dumps(email, indent=4)
            parent_id = str(uuid.uuid4())
            paragraph_store[parent_id] = email_paragraph
            all_child_lines_for_vectorDB.extend(child_line_splitting(email_body=email['body'], parent_id=parent_id))
    # for id, para in paragraph_store.items():
    #     print(id)
    #     print(json.dumps(json.loads(para), indent=4))
    
    return all_child_lines_for_vectorDB, paragraph_store

def store_to_vector_db(email_prompt=None)->None:
    all_child_lines_for_vectorDB = []
    embedding_model = get_embedding_model()
    all_child_lines_for_vectorDB, paragraph_store = splitting_emails(email_prompt=email_prompt)
    # if email_prompt:
    #     all_child_lines_for_vectorDB, paragraph_store = splitting_emails(email_prompt=email_prompt)
    # else:
    #     all_child_lines_for_vectorDB, paragraph_store = splitting_emails()
    # for line in all_child_lines_for_vectorDB:
    #     print(line)
    try:
        vector_store = Chroma.from_documents(
            documents=all_child_lines_for_vectorDB,
            embedding = embedding_model,
            persist_directory=r".\chroma_db",
            collection_name="email_classification"
        )
        print("vectores are successfully stored to vector db!!", vector_store)
        return paragraph_store
    except Exception as embedding_error:
        print(embedding_error)


if __name__ == '__main__':
    pass
    # store_to_vector_db()
    vector_store = Chroma(
        persist_directory=r".\chroma_db",
        collection_name="email_classification"
    )
    vector_store.delete_collection()
    print('successfully deleted the collection email_classification')
