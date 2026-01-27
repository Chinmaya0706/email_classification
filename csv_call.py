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
import json

def personality_prompt():
    persona = """
        ### ROLE
            1. You are a Senior Financial Crime Detection Engine operating inside a Tier-1 Bank surveillance system.

            2. Your ONLY responsibility is to detect, classify, and score compliance risk in corporate finance emails with MAXIMUM accuracy.

            3. You are NOT a chatbot.
            4. You are NOT an assistant.
            5. You are a rule-driven compliance classifier.

        ---

        ### 🛑 ABSOLUTE OUTPUT RULES
            1. OUTPUT NOTHING except a direct call to the `output_format` function.
            2. NO explanations, NO markdown, NO commentary, NO formatting.
            3. DO NOT include code blocks, tags, or text outside the function call.
            4. Every field MUST be populated with a meaningful value.

        ---

        ### 🔍 PRIMARY OBJECTIVE
            Identify whether the email contains ANY of the following:

            • Market Manipulation  
            • Secrecy / Regulatory Concealment  
            • Bribery or Personal Benefit  
            • Client Misrepresentation  
            • Whistleblower Complaints  

            Assume emails are written by financially sophisticated actors using subtle language.

            If intent is present, classify as HIGH RISK even if wording is indirect.

        ---

        ### ⚖️ CLASSIFICATION RULES (VERY IMPORTANT)

            Market Manipulation:
            - Trade sequencing to benefit proprietary desk
            - Delaying disclosures until after trades
            - Influencing prices, spreads, liquidity, NAV, earnings timing

            Secrecy / Leaks:
            - Delaying regulators, auditors, compliance visibility
            - Offshore transfers before disclosure
            - 'Keep this between us', 'delete after reading', selective sharing

            Market Bribery:
            - Any personal benefit linked to decisions
            - Jobs, internships, favors, payments, gifts, consultancy accounts
            - Indirect benefits still count as bribery

            Ethics / Conduct:
            - Omitting risks
            - Misleading clients
            - Hiding downgrade triggers, downside exposure, stress scenarios

            Complaints:
            - Reporting manipulation, allocation abuse, overrides, misreporting
            - Whistleblower tone
            - Describing repeated misconduct

        ---

        ### 📊 RISK SCORING CALIBRATION (CRITICAL)

            You MUST assign scores using this scale:

            HIGH RISK (80–100):
            - Intentional concealment
            - Trade manipulation
            - Bribery or personal benefit
            - Regulatory evasion
            - Accounting or valuation manipulation

            MEDIUM RISK (50–79):
            - Misleading clients
            - Omitting risks
            - Ethical violations without direct illegality

            LOW RISK (0–49):
            - Normal business discussion
            - No manipulation, concealment, or unethical behavior

            If ANY intent to influence markets, regulators, or decisions exists → score MUST be ≥ 85.

        ---

        ### 🧾 EVIDENCE EXTRACTION RULE

            For `highlighted_evidence`:
            - Quote the SINGLE most suspicious phrase
            - EXACT text from the email
            - Replace internal " with '

            Example:
            Input: He said "sell now"
            Output: He said 'sell now'

        ---

        ### 🧠 REASONING STANDARD

            In `reason`:
            - Explicitly state:
            • What action is happening
            • Why it violates compliance
            • What intent is implied

            Do NOT describe generally.
            Do NOT be vague.

        ---

        ### 🚨 DEFAULT BEHAVIOR

            When in doubt:
            - Assume malicious intent
            - Prefer HIGH risk over LOW
            - Prefer stricter category

            False negatives are unacceptable.

        Proceed to classify the TARGET_EMAIL now.
    """
    return persona


class output_format(BaseModel):
    classification : Literal["Market Manipulation", "Secrecy/Leaks", "Market Bribery", "Complaints", "Ethics/Conduct"] = Field(description="""Classify this email based on the given categories""")
    risk_score : int = Field(description="calcualte the risk score of being fraud", ge=0, le=100)
    risk_level : Literal["Low", "High", "Medium"] = Field(description="High Risk (Red, Score 80-100):Medium Risk (Yellow, Score 50-79):Low Risk (Green, Score 0-49):")
    highlighted_evidence : str = Field(description="Quote the EXACT suspicious phrase from the email")
    reason : str = Field(description="Explain WHY this is a violation, referencing the retrieved context if applicable")
    action_guidance : str = Field(description="Recommended next step for the human auditor")

model, parser = get_chat_model()
structured_output_model = model.with_structured_output(
    output_format, 
    method="function_calling", 
    include_raw=False
)

def process_single_row(index:int, email_body:str, knowledge_paragraph_store:dict)->tuple:
    
    child_lines, paragraph_store = store_to_vector_db(type="None",email_prompt=email_body)
    # print(child_lines, paragraph_store)
    # knowledge_paragraph_store |= paragraph_store
    # final_paragraph_list_for_llm = get_relavant_lines(list_of_lines=child_lines, paragraph_store=knowledge_paragraph_store)
    # # print(final_paragraph_list_for_llm)
    # context_prompt = get_context(final_paragraph_list_for_llm=final_paragraph_list_for_llm)
    user_msg = f"""
        TARGET_EMAIL:
        {email_body}

        TASK:
        Analyze this corporate finance email for regulatory, market abuse, bribery, secrecy, ethics, or complaint risk.

        You must:
        1. Identify the strongest applicable classification.
        2. Assign a calibrated fraud risk score.
        3. Extract the exact suspicious phrase as evidence.
        4. Explain the violation clearly.
        5. Recommend the correct compliance action.

        Remember:
        - Subtle language still counts as intent.
        - Timing manipulation, disclosure delay, sequencing, or personal benefit is HIGH RISK.
    """

    message = [
        SystemMessage(content=personality_prompt()),
        # SystemMessage(content=context_prompt),
        HumanMessage(content=user_msg)
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
            ): index for index, row in df.iterrows() if isinstance(row['body'], str) and row['body'].strip()
        }

        count = 0
        for future in as_completed(future_to_row):
            try:
                row_index, result, paragraph_store = future.result()
                # print(f"row index is {row_index}\n")
                # print(f"whole row is {df.loc[row_index]}")
                # print(f"result is {result}\n")
                # print(f"paragraph store is {paragraph_store}")
                json_text_for_paragraph = {
                    "index_no" : f"this email in row no. {row_index + 2}",
                    "email_part": df.loc[row_index].to_dict()
                }
                df.at[row_index, "classification"] = result.classification
                df.at[row_index, "risk_score"] = result.risk_score
                df.at[row_index, "risk_level"] = result.risk_level
                df.at[row_index, "highlighted_evidence"] = result.highlighted_evidence
                df.at[row_index, "reason"] = result.reason
                df.at[row_index, "action_guidance"] = result.action_guidance
                json_text_for_paragraph["result"] = {
                    "classification": result.classification,
                    "risk_score": result.risk_score,
                    "risk_level": result.risk_level,
                    "highlighted_evidence": result.highlighted_evidence,
                    "reason": result.reason,
                    "action_guidance": result.action_guidance
                }
                print("entering to store_to_vector_db")
                for parent_id, _ in paragraph_store.items():
                    paragraph_store[parent_id] = str(json_text_for_paragraph)
                    _,new_paragraph_store = store_to_vector_db(email_prompt=paragraph_store[parent_id])
                print("storing json_text_for_paragraph in new_paragraph_store")
                for parent_id, _ in new_paragraph_store.items():
                    new_paragraph_store[parent_id] = json.dumps(json_text_for_paragraph, indent=4)

                print("---------------------")
                print(f"paragraph store is :\n{new_paragraph_store}\n")
                knowledge_paragraph_store |= new_paragraph_store   

                for parent_id, _ in new_paragraph_store.items():
                    print(f"In knowledge paragraph store:\n{knowledge_paragraph_store[parent_id]}")
                count += 1
                progress_bar.progress(count / len(df))

            except Exception as e:
                st.error(f"❌{e}")
                print(f"error while generating new rows{e}")
    st.success(f"✅ done")
    
    return df