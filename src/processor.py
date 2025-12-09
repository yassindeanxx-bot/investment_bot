import os
from typing import Protocol
from data_pipeline.ingest import PDFIngestor
from data_pipeline.chunking import Chunker
from data_pipeline.indexing import Indexer
from collections import Counter
from uuid import uuid4

# --- Protocol Definition ---
class PipelineObserver(Protocol):
    def on_start(self, filename: str): ...
    def on_progress(self, stage: str, count: int, msg: str): ...
    def on_finish(self, filename: str, stats: dict): ...
    def on_error(self, error: str): ...

# --- Default Observer ---
class ConsoleObserver:
    def on_start(self, filename): print(f"🚀 Processing {filename}...")
    def on_progress(self, stage, count, msg): print(f"[{stage}] {msg}")
    def on_finish(self, filename, stats): print(f"✅ Done! Stats: {stats}")
    def on_error(self, error): print(f"❌ Error: {error}")

# --- The Logic ---
class DocumentProcessor:
    def run(self, file_path: str, observer: PipelineObserver = ConsoleObserver()):
        try:
            job_id = uuid4().hex
            filename = os.path.basename(file_path)
            observer.on_start(filename)
            
            # 1. Setup the Lazy Streams (Pipes)
            ingestor = PDFIngestor()
            page_stream = ingestor.extract(job_id, file_path)

            counter = Counter(['INGESTION', 'CHUNKING', 'INDEXING'])
            
            chunker = Chunker()
            chunk_stream = chunker.process(self.observed_stream(page_stream, observer, counter, 'CHUNKING'), job_id)

            # 3. Pull the trigger (The Sink starts consuming)
            indexer = Indexer()
            indexer.index(self.observed_stream(chunk_stream, observer, counter, 'INDEXING'))
            
            observer.on_finish(filename, {"chunks": counter["INDEXING"]})
            
        except Exception as e:
            observer.on_error(str(e))

    def observed_stream(self, stream, observer: PipelineObserver, counter: Counter, stage: str):
        for item in stream:
            counter[stage] += 1
            if counter[stage] % 10 == 0:
                observer.on_progress(stage, counter[stage], f"Processed {counter[stage]} items...")
            yield item

# --- Manual Test ---
if __name__ == "__main__":
    proc = DocumentProcessor()
    proc.run("data/tsla-20241231-gen.pdf")