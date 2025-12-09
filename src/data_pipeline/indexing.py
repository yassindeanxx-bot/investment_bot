import chromadb
from typing import Iterator
# Import the centralized client we created earlier
from config import client, EMBEDDING_MODEL, chroma_client, collection

class Indexer:
    def get_embedding(self, text):
        return client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        ).embeddings[0].values

    def index(self, chunk_stream: Iterator[dict]):
        """
        Sink: Consumes the stream and writes to DB in batches.
        """
        batch_size = 10
        batch = []
        
        for chunk in chunk_stream:
            batch.append(chunk)
            
            if len(batch) >= batch_size:
                self._flush(batch)
                batch = [] # Reset
        
        # Flush leftovers
        if batch:
            self._flush(batch)

    def _flush(self, batch):
        ids = [item["chunk_id"] for item in batch]
        documents = [item["text"] for item in batch]
        metadatas = [{"page": item["page"], "source": item["source"]} for item in batch]
        embeddings = []
        
        # This is where we pay the Time Cost (Network Latency)
        # TODO: use batch api to request for embeddings
        for item in batch:
            try:
                embeddings.append(self.get_embedding(item["text"]))
            except Exception as e:
                print(f"Embedding failed: {e}")
                continue

        if embeddings:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )