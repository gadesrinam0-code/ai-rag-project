import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

try:
    result = embeddings.embed_query("Hello")
    print("✅ Embedding works!")
    print(result[:5])
except Exception as e:
    print("❌ Error:")
    print(e)