from pydantic import BaseModel, Field
from typing import Annotated, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from get_model import get_api_key
import streamlit as st
import re


class RouterDecision(BaseModel):
    """Classify the user input."""
    intent: Literal["EMAIL", "CHAT"] = Field(
        ..., 
        description="The classification of the text. 'EMAIL' if it is a communication to analyze. 'CHAT' if it is a question."
    )
# 1. Define the Router Function
def intent_router(user_input: str) -> Literal["EMAIL", "CHAT"]:
    """
    Decides if input is 'EMAIL_TO_ANALYZE' or 'CHAT_QUESTION'.
    Returns: 'EMAIL' or 'CHAT'
    """
    
    # --- LAYER 1: Regex Patterns (Instant) ---
    # Look for common email headers
    email_patterns = [
        r"From:.*@",           # Matches "From: name@domain"
        r"Subject:.*",         # Matches "Subject: ..."
        r"To:.*@",             # Matches "To: name@domain"
    ]
    
    for pattern in email_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            print("🚀 Fast Route: Detected Email Headers")
            return "EMAIL"

    # --- LAYER 2: Length Heuristic (Instant) ---
    # Emails are usually dense; Questions are usually short.
    word_count = len(user_input.split())
    if word_count > 30:
        print("🚀 Fast Route: Detected Long Text (>70 words)")
        return "EMAIL"
    if word_count < 27:
        # Very short inputs like "Why?", "Explain" are definitely chat
        print("🚀 Fast Route: Detected Short Chat")
        return "CHAT"

    # --- LAYER 3: LLM Router (The "Smart" Check) ---
    # Only for ambiguous cases (50-150 words without headers)
    print("🧠 Slow Route: Asking Router LLM...")
    
    router_prompt = f"""
    Classify the following text into one of two categories:
    1. 'EMAIL': If the prompt contains a clear email or an email body with any subject, to, from. A raw email or communication text that needs compliance analysis.
    2. 'CHAT': A question, follow-up, or conversational remark about a previous analysis.

    TEXT:
    "{user_input}"  # Send only first 500 chars to save tokens

    Reply with strictly one word: 'EMAIL' or 'CHAT'.
    """
    llm_flash_model = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0, api_key=st.secrets["GROQ_API_KEY"]).with_structured_output(RouterDecision)

    response = llm_flash_model.invoke(router_prompt).intent
    return response