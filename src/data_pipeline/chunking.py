from typing import Iterator
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    def process(self, page_stream: Iterator[dict], job_id: str) -> Iterator[dict]:
        """
        Stream Transformer: Consumes Pages -> Yields Chunks.
        """
        for page in page_stream:
            text = page['content']
            chunks_text = self.splitter.split_text(text)
            
            for i, chunk_text in enumerate(chunks_text):
                yield {
                    "chunk_id": f"pg{page['page_number']}_chk{i}_{job_id}",
                    "page": page['page_number'],
                    "text": chunk_text,
                    "source": page['source']
                }