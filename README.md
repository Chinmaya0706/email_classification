# 🛡️ Sentinel-AI: Context-Aware Financial Compliance Auditor

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-Orchestration-green?style=for-the-badge&logo=chainlink&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o-Deterministic-purple?style=for-the-badge&logo=openai&logoColor=white)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red?style=for-the-badge&logo=streamlit&logoColor=white)
![ChromaDB](https://img.shields.io/badge/Vector_DB-Chroma-orange?style=for-the-badge)

> **An intelligent, RAG-powered forensic tool designed for Tier-1 Banking Compliance.** > Unlike standard classifiers, Sentinel-AI uses historical precedents and a deterministic logic gate to detect Financial Crime, Market Manipulation, and Insider Threats with **Zero-Hallucination** policy.

---

## 📖 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Architecture & Workflow](#-architecture--workflow)
- [Tech Stack](#-tech-stack)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [Project Structure](#-project-structure)

---

## 🔭 Project Overview

In the high-stakes world of financial compliance, keyword matching is not enough. **Sentinel-AI** leverages **Retrieval-Augmented Generation (RAG)** to analyze emails not just for *what* they say, but for *intent* based on confirmed historical violations.

It processes internal communications to detect:
1.  **Market Manipulation** (Artificial inflating of stock prices).
2.  **MNPI Leaks** (Material Non-Public Information).
3.  **Quid Pro Quo / Bribery**.
4.  **Coded Language** (e.g., "The weather looks stormy" = "Market crash incoming").

The system operates on a **Temperature = 0.0 (Greedy Decoding)** protocol, ensuring 100% reproducibility and strict adherence to the "Fraud Triangle" framework.

---

## 🌟 Key Features

### 1. ⚡ Instant Single-Email Forensic Analysis
- Paste an email body directly.
- The system retrieves relevant past cases from the Vector DB.
- Returns a **Structured JSON** report with Risk Score (0-100), Evidence, and Action Guidance.

### 2. 🚀 Multithreaded Bulk Processing (CSV)
- Upload a CSV containing thousands of emails.
- Uses `concurrent.futures.ThreadPoolExecutor` to process rows in **parallel**.
- Auto-handles sanitization of multi-line text and quotes.
- Outputs a downloadable, enriched Excel/CSV file.

### 3. 🧠 RAG (Retrieval-Augmented Generation)
- Uses **Parent-Document Retriever** strategy.
- Fetches precise paragraphs (`RecursiveCharacterTextSplitter`) from the knowledge base to ground the LLM's decision.
- Prevents false positives by comparing current emails against *confirmed* historical precedents.

### 4. 💬 Interactive Post-Analysis Q&A
- After processing a batch, chat with your data.
- Ask: *"Why did you flag row 45 as High Risk?"*
- The system uses the retained context to explain its decision logic.

---

## 🏗️ Architecture & Workflow

The system follows a strict pipeline to ensure data integrity and logical consistency.

```mermaid
graph TD
    A[User Input] -->|Option 1: Paste Text| B(Single Email Processor)
    A -->|Option 2: Upload CSV| C(Parallel Batch Processor)
    
    subgraph "RAG Engine"
    D[Gemini Embedding Model] -->|Vectorize| E[ChromaDB]
    E -->|Retrieve Context| F[Parent-Document Retriever]
    end
    
    B --> D
    C --> D
    
    F -->|Historical Precedents| G[Context Prompt Formulator]
    G --> H{GPT-4o Engine}
    
    style H fill:#f9f,stroke:#333,stroke-width:4px
    H -->|Temp=0.0| I[Strict JSON Output]
    
    I --> J[Streamlit Dashboard]
    I --> K[Downloadable Excel Report]