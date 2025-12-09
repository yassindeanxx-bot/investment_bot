import streamlit as st
import requests
import time
import os

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Deep Research Client", layout="wide")
st.title("🌐 Enterprise RAG: Client Mode")

# --- Sidebar: Async Upload ---
with st.sidebar:
    st.header("1. Upload to Server")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file and st.button("🚀 Upload & Process"):
        with st.spinner("Uploading to API..."):
            # 1. Send File to API
            files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
            try:
                response = requests.post(f"{API_URL}/ingest", files=files)
                
                if response.status_code == 200:
                    job_id = response.json()["job_id"]
                    st.success(f"Job Started! ID: {job_id}")
                    
                    # 2. The Polling Loop (The 'Loading Bar' Logic)
                    progress_bar = st.progress(0)
                    status_area = st.empty()
                    
                    while True:
                        time.sleep(0.5) # Poll every 500ms
                        
                        status_res = requests.get(f"{API_URL}/status/{job_id}")
                        if status_res.status_code != 200:
                            st.error("Lost connection to server.")
                            break
                            
                        job_data = status_res.json()
                        state = job_data["status"]
                        logs = job_data.get("log", [])
                        current_log = logs[-1] if logs else "Starting..."
                        
                        # Update UI
                        status_area.code(f"Status: {state.upper()}\nLatest: {current_log}")
                        
                        # Progress bar logic (Simple estimation or real count)
                        # Since we track chunks, let's just show activity
                        # or map 0-100 if we knew the total.
                        
                        if state == "completed":
                            progress_bar.progress(100)
                            st.balloons()
                            st.success("Indexing Complete!")
                            break
                        elif state == "failed":
                            st.error(f"Job Failed: {job_data.get('error')}")
                            break
                            
                else:
                    st.error(f"Upload failed: {response.text}")
                    
            except Exception as e:
                st.error(f"Could not connect to API: {e}")

# --- Main Window: Chat ---
st.header("2. Chat with the Brain")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask about the report..."):
    # Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Call API
    with st.chat_message("assistant"):
        with st.spinner("Waiting for Server..."):
            try:
                payload = {"question": prompt}
                res = requests.post(f"{API_URL}/chat", json=payload)
                
                if res.status_code == 200:
                    answer = res.json()["answer"]
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"API Error: {res.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")