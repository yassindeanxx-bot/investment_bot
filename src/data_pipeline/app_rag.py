import streamlit as st
import os
import shutil

# --- Import your Backend Modules ---
# These act as the bridge to the scripts you wrote yesterday
from ingest import PDFIngestor
from chunking import Chunker
from indexing import Indexer
from rag_agent import generate_answer

# --- UI Configuration ---
st.set_page_config(page_title="Deep Research Agent", layout="wide")

st.title("🧐 Enterprise RAG: The 10-K Researcher")
st.markdown("---")

# --- SIDEBAR: The Data Pipeline ---
with st.sidebar:
    st.header("1. Data Ingestion")
    st.info("Upload a financial report to update the brain.")
    
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file:
        # Define where to save it
        target_folder = "data"
        target_path = os.path.join(target_folder, "source.pdf")
        
        # Save the file
        with open(target_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File Saved!")
        
        # The "Trigger" Button
        if st.button("🚀 Process & Index Document"):
            with st.status("Running ETL Pipeline...", expanded=True) as status:
                
                # 1. Ingest
                st.write("📄 Extracting text from PDF...")
                ingestor = PDFIngestor(target_path)
                raw_data = ingestor.extract_text()
                ingestor.save_to_json(raw_data)
                
                # 2. Chunk
                st.write("✂️ Splitting into semantic chunks...")
                chunker = Chunker()
                chunks = chunker.process()
                chunker.save(chunks)
                
                # 3. Index
                st.write("🧠 Embedding into Vector Database...")
                # We need to clear old DB logic or just append. 
                # For MVP, appending is fine, or you can delete ./chroma_db manually to reset.
                indexer = Indexer()
                indexer.run()
                
                status.update(label="✅ Knowledge Base Updated!", state="complete", expanded=False)

# --- MAIN AREA: The Chat Interface ---
st.header("2. Chat with your Data")

# Session State to hold chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "I have read the report. Ask me about revenue, risks, or debt."}
    ]

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle User Input
if prompt := st.chat_input("Ex: What are the primary risk factors?"):
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call the RAG Agent we built yesterday
                response_text = generate_answer(prompt)
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            except Exception as e:
                st.error(f"Error: {e}")