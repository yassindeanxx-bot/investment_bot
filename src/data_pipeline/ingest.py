import fitz  # PyMuPDF
from typing import Iterator

class PDFIngestor:
    def extract(self, job_id, pdf_path: str) -> Iterator[dict]:
        """
        Generator: Yields one page at a time.
        Memory: O(1) (Only holds one page text in RAM).
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            yield {
                "job_id": job_id,
                "page_number": page_num + 1,
                "total_pages": total_pages,
                "content": text.strip(),
                "source": pdf_path
            }