import asyncio
import chromadb
import os
from google import genai
from google.genai import types
from config import REASONING_MODEL, client, EMBEDDING_MODEL, chroma_client, collection

def get_embedding(text):
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    return result.embeddings[0].values

def generate_answer(query):
    print(f"🤔 Analyzing: '{query}'...")
    
    # --- Step 1: RETRIEVAL ---
    query_vector = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=5 # Get top 5 pieces of evidence
    )
    
    # Combine the retrieved text into one big string
    context_text = "\n\n".join(results['documents'][0])
    
    # --- Step 2: AUGMENTATION ---
    # This is the "Prompt Engineering" part
    prompt = f"""
    You are a Senior Financial Analyst. 
    Answer the user's question based ONLY on the following context. 
    If the answer is not in the context, say "I don't have that information in the report."
    
    CONTEXT:
    {context_text}
    
    USER QUESTION:
    {query}
    """
    
    # --- Step 3: GENERATION ---
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    
    return response.text

# --- The New Async Version ---
async def generate_answer_async(query):
    print(f"🤔 Analyzing (Async): '{query}'...")
    
    # --- Step 1: Retrieval (Blocking I/O) ---
    # ChromaDB is synchronous. If we run it directly here, it blocks the loop.
    # We offload it to a separate thread so the Event Loop stays free.
    
    def run_retrieval():
        query_vector = get_embedding(query) # This calls Sync embedding
        return collection.query(
            query_embeddings=[query_vector],
            n_results=5
        )

    # await the thread
    results = await asyncio.to_thread(run_retrieval)
    
    # Combine context
    context_text = "\n\n".join(results['documents'][0])
    
    # --- Step 2: Augmentation ---
    prompt = f"""
    You are a Senior Financial Analyst. 
    Answer the user's question based ONLY on the following context. 
    
    CONTEXT:
    {context_text}
    
    USER QUESTION:
    {query}
    """
    
    # --- Step 3: Generation (Native Async) ---
    # The new google-genai client has an '.aio' accessor for async methods
    response = await client.aio.models.generate_content(
        model=REASONING_MODEL,
        contents=prompt
    )
    
    return response.text

if __name__ == "__main__":
    # The moment of truth
    q1 = "What are the major legal risks facing the company?"
    print(f"\nUser: {q1}")
    print(f"Agent: {generate_answer(q1)}")
    
    print("-" * 50)
    
    q2 = "How much revenue did they make from Cloud services?"
    print(f"\nUser: {q2}")
    print(f"Agent: {generate_answer(q2)}")
    