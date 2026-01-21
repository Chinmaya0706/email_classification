from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI, AzureChatOpenAI
import streamlit as st
import os

@st.cache_resource
def get_api_key()->str:
    try:
        api_key = None
        if "TCS_API_KEY" in st.secrets:
            api_key = st.secrets["TCS_API_KEY"]
        
        # 2. If not found, fall back to environment variables (for local development with .env)
        else:
            st.error("No API key is present")
    except Exception as e:
            load_dotenv() # Load the .env file contents
            api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        st.error("🔑 API Key Missing! Please set GOOGLE_API_KEY in .env or Streamlit Secrets.")
        st.stop()
    
    return api_key

@st.cache_resource
def get_embedding_model()->GoogleGenerativeAIEmbeddings:
    # api_key = get_api_key()
        
    return GoogleGenerativeAIEmbeddings(
        # model="models/gemini-embedding-001",
        model = 'models/text-embedding-004',
        google_api_key=st.secrets["GOOGLE_API_KEY"]
    )

@st.cache_resource
def get_chat_model(temperature = 0.0)->tuple[AzureChatOpenAI, StrOutputParser]:
    # api_key = get_api_key()
    model = AzureChatOpenAI(
        base_url= st.secrets["BASE_URL"],
        # base_url = "https://genailab.tcs.in",
        temperature=temperature, 
        model="gpt-4o", # Or "mixtral-8x7b-32768"
        api_key=st.secrets["TCS_API_KEY"],
        api_version="2025-01-01-preview"
    )
    return model, StrOutputParser()