# 📚 AI Research Assistant — Multi-PDF RAG Chatbot

An AI-powered Research Assistant that allows users to upload research papers, ask questions about them, compare multiple PDFs, maintain conversational context, and optionally use web search for up-to-date information.

## 🚀 Features

- 📄 Upload and process PDF research papers
- 🔎 Retrieval-Augmented Generation (RAG)
- 🧠 Semantic search using embeddings
- 💬 Conversational question answering
- 🔄 Context-aware follow-up questions
- 📚 Multi-PDF comparison
- 🎯 Select specific documents for retrieval
- 🌐 Optional web search
- 📑 Display PDF sources and page references
- ⚡ Fast AI responses using Groq
- 🖥️ Modern React frontend

## 🏗️ System Architecture

```text
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
PDF Processing
  ↓
Text Chunking
  ↓
Sentence Transformers
  ↓
FAISS Vector Database
  ↓
Semantic Retrieval
  ↓
Groq LLM
  ↓
AI Generated Answer