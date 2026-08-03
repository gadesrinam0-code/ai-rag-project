# 🤖 AI Hybrid RAG Project

An AI-powered **Hybrid Retrieval-Augmented Generation (RAG)** application that enables users to upload PDF documents, perform optional live web searches, and receive intelligent, context-aware answers using Groq LLM.

---

# 🚀 Features

- 📄 Upload PDF documents
- 📖 Extract text from PDFs
- ✂️ Split text into semantic chunks
- 🧠 Generate embeddings using Hugging Face
- 🗂️ Store embeddings in FAISS Vector Database
- 🔍 Retrieve relevant PDF context
- 🌐 Hybrid PDF + Web Search
- 🔀 Web Search Toggle (PDF Only / PDF + Web)
- 🤖 AI-powered answers using Groq LLM
- 💬 Chat History
- 🧹 Clear Chat
- ⚡ Fast and responsive UI
- ☁️ Live deployment using Vercel & Railway

---

# 🛠️ Tech Stack

## Frontend

- React
- Vite
- Axios
- Tailwind CSS

## Backend

- FastAPI
- LangChain
- FAISS
- Hugging Face Embeddings
- Groq LLM
- Tavily Search API
- PyPDF

---

# 📂 Project Structure

```
ai-rag-project
│
├── frontend
│   ├── src
│   ├── public
│   ├── package.json
│   └── vite.config.js
│
├── backend
│   ├── app.py
│   ├── requirements.txt
│   ├── uploads
│   └── faiss_index
│
└── README.md
```

---

# ⚙️ How It Works

### 📄 PDF Processing

1. User uploads a PDF document.
2. The application extracts text from the PDF.
3. The extracted text is divided into semantic chunks.
4. Hugging Face generates vector embeddings.
5. FAISS stores all embeddings for semantic retrieval.

### 🤖 Question Answering

1. User enters a question.
2. If **Web Search is OFF**
   - FAISS retrieves the most relevant PDF chunks.
3. If **Web Search is ON**
   - FAISS retrieves relevant PDF chunks.
   - Tavily searches the live web.
4. Groq LLM combines all available context.
5. The application returns an intelligent answer.

---

# 🏗️ System Architecture

```
                    User Question
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
      Search Uploaded PDF       Search Live Web
           (FAISS)                (Tavily)
             │                         │
             └────────────┬────────────┘
                          ▼
                  Combine Context
                          ▼
                     Groq LLM
                          ▼
                  AI Generated Answer
```

---

# 🌐 Live Demo

## Frontend

https://ai-rag-project-psi.vercel.app

## Backend

https://ai-rag-project-production.up.railway.app

---

# 📸 Application Features

✅ Upload PDF

✅ Ask Questions

✅ Hybrid PDF + Web Search

✅ Web Search Toggle

✅ Chat History

✅ Clear Chat

✅ Intelligent AI Responses

---

# 📈 Future Improvements

- Multiple PDF Support
- User Authentication
- Source Citations
- PDF Page References
- Voice Input
- Multi-language Support
- Export Chat as PDF
- OCR Support for Scanned PDFs

---

# 👨‍💻 Author

**Srinam Gade**

---

# 🙏 Acknowledgements

This project was built using:

- React
- FastAPI
- LangChain
- Hugging Face
- FAISS
- Groq LLM
- Tavily Search API
- Vercel
- Railway

---

# ⭐ If you found this project useful, consider giving it a star on GitHub!
