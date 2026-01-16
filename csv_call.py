from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from typing import Literal
from pydantic import BaseModel, Field
from get_model import get_chat_model
# from personality_prompt import personality
from langchain_core.messages import HumanMessage, SystemMessage
from context_for_llm import get_context
from retrieving_relevant_lines import get_relavant_lines
from knowledge_base_vector_db import store_to_vector_db
import streamlit as st

personality_prompt = f"""                
    ### ROLE & OBJECTIVE
    You are a Senior Financial Compliance Officer and Forensic Auditor for a Tier-1 Global Bank. 
    Your job is to analyze internal communications (emails) to detect potential financial crimes, misconduct, or policy violations.
    You have a "Zero Tolerance" policy for missed risks, but you must also avoid flagging innocent conversations (False Positives).
    Don't talk unnecessary. Tell something which is required!!

    ### INPUT DATA
    1. **TARGET_EMAIL**: The new email you must analyze.
    2. **RETRIEVED_CONTEXT**: Past similar emails that were confirmed as violations (Precedents).

    ### ANALYSIS GUIDELINES
    You must analyze the 'TARGET_EMAIL' by comparing it strictly against the 'RETRIEVED_CONTEXT' and standard financial compliance rules.

    **Look for these specific indicators:**
    1. **Coded Language:** Users often use metaphors like "weather," "dinner plans," or "golf" to discuss market moves. (e.g., "The weather looks stormy" = "Market crash coming").
    2. **Urgency & Secrecy:** Phrases like "Keep this between us," "Offline," "Don't email me," or "Delete this."
    3. **Quid Pro Quo (Bribery):** mentions of "gifts," "scholarships," or "favors" linked to business outcomes.
    4. **Data Exfiltration:** Sending work documents to personal emails (Gmail, Yahoo) or unauthorized devices.

    ### SCORING RULES
    - **High Risk (Red, Score 80-100):** Clear evidence of Intent (Market Manipulation, Bribery, Leaking MNPI, Blackmail).
    - **Medium Risk (Yellow, Score 50-79):** Suspicious behavior, angry complaints, or policy "grey areas" (e.g., rude language, minor data policy breach).
    - **Low Risk (Green, Score 0-49):** Innocent social chatter (Lunch, Holidays) or standard business operations.
"""

class output_format(BaseModel):
    classification : Literal["Market Manipulation", "Secrecy/Leaks", "Market Bribery", "Complaints", "Ethics/Conduct"] = Field(description="""Classify this email based on the given categories""")
    risk_score : int = Field(description="calcualte the risk score of being fraud", ge=0, le=100)
    risk_level : Literal["Low", "High", "Medium"] = Field(description="High Risk (Red, Score 80-100):Medium Risk (Yellow, Score 50-79):Low Risk (Green, Score 0-49):")
    highlighted_evidence : str = Field(description="Quote the EXACT suspicious phrase from the email")
    reason : str = Field(description="Explain WHY this is a violation, referencing the retrieved context if applicable")
    action_guidance : str = Field(description="Recommended next step for the human auditor")

model, parser = get_chat_model()
structured_output_model = model.with_structured_output(output_format)

def process_single_row(index:int, email_body:str, knowledge_paragraph_store:dict)->tuple:
    
    child_lines, paragraph_store = store_to_vector_db(email_prompt=email_body)
    # print(child_lines, paragraph_store)
    # knowledge_paragraph_store |= paragraph_store
    final_paragraph_list_for_llm = get_relavant_lines(list_of_lines=child_lines, paragraph_store=knowledge_paragraph_store)
    # print(final_paragraph_list_for_llm)
    context_prompt = get_context(final_paragraph_list_for_llm=final_paragraph_list_for_llm)
    message = [
        SystemMessage(content=personality_prompt),
        SystemMessage(content=context_prompt),
        HumanMessage(content=email_body)
    ]
    result = structured_output_model.invoke(message)
    # print(result)
    return index, result, paragraph_store

def csv_summary(df:pd, knowledge_paragraph_store:dict):
    # df[["classification", "risk_score", "risk_level", "highlighted_evidence", "reason", "action_guidance"]] = None
    df = df.assign(
        classification = "Unknown",
        risk_score = 0.0,
        risk_level = "Unknown",
        highlighted_evidence = "Unknown",
        reason = "Unknown",
        action_guidance = "Unknonw"
    )
    
    progress_bar = st.progress(0)
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_row = {
            executor.submit(
                process_single_row, 
                index, 
                row['body'],
                knowledge_paragraph_store.copy(),
            ): index for index, row in df.iterrows()
        }

        count = 0
        for future in as_completed(future_to_row):
            try:
                row_index, result, paragraph_store = future.result()
                knowledge_paragraph_store |= paragraph_store
                df.at[row_index, "classification"] = result.classification
                df.at[row_index, "risk_score"] = result.risk_score
                df.at[row_index, "risk_level"] = result.risk_level
                df.at[row_index, "highlighted_evidence"] = result.highlighted_evidence
                df.at[row_index, "reason"] = result.reason
                df.at[row_index, "action_guidance"] = result.action_guidance
                count += 1
                progress_bar.progress(count / len(df))

            except Exception as e:
                st.error(f"❌{e}")
                print(f"error while generating new rows{e}")
    st.success(f"✅")
    
    return df