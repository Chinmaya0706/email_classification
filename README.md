# 🕵️‍♂️ TCS Advanced AI Surveillance System: The "AI Compliance Officer"

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![LangChain](https://img.shields.io/badge/LangChain-RAG-orange?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?style=for-the-badge&logo=streamlit)
![Gemini](https://img.shields.io/badge/AI-Google%20Gemini-4285F4?style=for-the-badge&logo=google)

> **"Stopping Financial Crimes before they hit the headlines."**

## 📖 Executive Summary
In the high-stakes world of Finance, a single non-compliant email—Market Manipulation, Bribery, or Insider Trading—can cost billions in fines. Traditional systems rely on "keyword matching" (e.g., flagging the word "money"), leading to thousands of **False Positives** that waste human auditors' time.

This project is a **Next-Gen Communication Surveillance System**. It uses **RAG (Retrieval-Augmented Generation)** and **LLMs (Google Gemini)** to act as an intelligent "Forensic Auditor." It doesn't just read text; it understands context, detects sarcasm, catches "coded language" (e.g., "The weather is stormy" = "Sell stocks"), and prioritizes risks automatically.

---

## 🏗️ Architecture & The "Secret Sauce"

We didn't just build a chatbot; we built an **Intelligent Agentic Workflow**.

### 1. 🧠 The Brain (RAG + ParentDocumentRetriever)
Instead of simple chunks, we use a **Parent-Child Retrieval Strategy**:
* **The Problem:** Vector stores split text into small pieces, losing context.
* **Our Solution:** We split emails into small "Child Chunks" for precise searching, but when a match is found, we retrieve the **Full Parent Email**. This gives the LLM the complete evidence trail.

### 2. 🚦 The 3-Layer Intent Router
The system is smart enough to know what you want. It uses a **Cascading Router** to distinguish between analyzing a new email and chatting with the bot:
1.  **Layer 1 (Regex):** Instantly detects email headers (`From:`, `Subject:`).
2.  **Layer 2 (Heuristic):** Checks text density (Emails are long, Chat is short).
3.  **Layer 3 (LLM Router):** A lightweight AI model judges ambiguous inputs.

### 3. 🛡️ The Compliance Matrix
Every flagged email is auto-graded:
* 🔴 **High Risk:** Market Manipulation, MNPI Leaks (Immediate Freeze).
* 🟡 **Medium Risk:** Employee Ethics, Complaints (Manager Review).
* 🟢 **Low Risk:** Social Chatter (No Action).

---

## 📂 Project Structure

Here is how the codebase is organized to support this modular architecture:

```bash
EMAIL_CLASSIFICATION_PROJECT/
├── 📂 knowledge_data/           # 📄 The "Evidence Vault". JSON files containing synthetic email logs.
├── 📂 .streamlit/               # 🎨 UI Configuration for the frontend.
├── 📄 app.py                    # 🚀 MAIN ENTRY POINT. The Streamlit Dashboard.
├── 📄 get_model.py              # 🤖 Model Loader. Initializes Gemini 1.5 Flash & Embeddings.
├── 📄 knowledge_base_vector_db.py # 📚 The Librarian. Handles Data Ingestion & Vector Store creation.
├── 📄 personality_prompt.py     # 🎭 The Persona. System prompts that define the "Compliance Officer" role.
├── 📄 prompt_intent_router.py   # 🚦 The Gatekeeper. Logic for the 3-Layer Intent Router.
├── 📄 retrieving_relevant_lines.py # 🎣 The Hook. Logic for ParentDocumentRetriever (RAG).
└── 📄 requirements.txt          # 📦 Dependency list.
