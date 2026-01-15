def get_context(final_paragraph_list_for_llm:list)->str:
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
    return context_prompt