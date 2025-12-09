import chromadb
import os
from google import genai

# 1. Setup (Same as before)
client = genai.Client(api_key="AIzaSyDboT5__Cp9rZtJb42SjbvhU_FFBHsIA8s")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="financial_reports")

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    ret = result.embeddings[0].values
    # print(f"text: {text} 😯embedding: ({ret})")
    return ret

def search(query):
    print(f"\n🔎 Searching for: '{query}'...")
    
    # 1. Convert your query to numbers
    query_vector = get_embedding(query)
    
    # 2. Find the 3 closest chunks in the database
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=5
    )
    
    # 3. Print the results
    for i, doc in enumerate(results['documents'][0]):
        source = results['metadatas'][0][i]['source']
        page = results['metadatas'][0][i]['page']
        print(f"\n--- Result {i+1} (Source: {source}, Page {page}) ---")
        print(doc[:200] + "...") # Print first 200 chars

if __name__ == "__main__":
    # Test 1: Direct Question
    search("What are the risks related to AI?")
    
    # Test 2: Semantic Question (The word "Regulation" might not appear, but "Law" might)
    search("Is the company facing any legal threats?")