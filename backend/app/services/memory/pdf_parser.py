import io
from pathlib import Path
from typing import Optional
import pdfplumber
from pypdf import PdfReader
import structlog

logger = structlog.get_logger()


class PDFParser:
    """Parse PDF documents and extract text content."""

    def __init__(self):
        self.logger = logger.bind(service="pdf_parser")

    async def parse_file(self, file_path: str) -> dict:
        """Parse a PDF file and extract text content."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        return await self._extract_content(path)

    async def parse_bytes(self, pdf_bytes: bytes, filename: str = "upload.pdf") -> dict:
        """Parse PDF from bytes."""
        return await self._extract_content_from_bytes(pdf_bytes, filename)

    async def _extract_content(self, path: Path) -> dict:
        """Extract text and metadata from PDF file."""
        self.logger.info("parsing_pdf", path=str(path))

        try:
            pages = []
            metadata = {}

            # Use pdfplumber for better text extraction
            with pdfplumber.open(path) as pdf:
                metadata["page_count"] = len(pdf.pages)

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    tables = page.extract_tables()

                    pages.append({
                        "page_number": i + 1,
                        "text": text,
                        "tables": tables,
                        "has_images": len(page.images) > 0,
                    })

            # Get additional metadata from pypdf
            with open(path, "rb") as f:
                reader = PdfReader(f)
                if reader.metadata:
                    metadata["title"] = reader.metadata.get("/Title", "")
                    metadata["author"] = reader.metadata.get("/Author", "")
                    metadata["creation_date"] = reader.metadata.get("/CreationDate", "")

            return {
                "pages": pages,
                "metadata": metadata,
                "full_text": "\n\n".join(p["text"] for p in pages),
            }

        except Exception as e:
            self.logger.error("pdf_parse_error", error=str(e), path=str(path))
            raise

    async def _extract_content_from_bytes(self, pdf_bytes: bytes, filename: str) -> dict:
        """Extract text and metadata from PDF bytes."""
        self.logger.info("parsing_pdf_bytes", filename=filename, size=len(pdf_bytes))

        try:
            pages = []
            metadata = {}

            # Use pdfplumber for better text extraction
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                metadata["page_count"] = len(pdf.pages)

                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    tables = page.extract_tables()

                    pages.append({
                        "page_number": i + 1,
                        "text": text,
                        "tables": tables,
                        "has_images": len(page.images) > 0,
                    })

            # Get additional metadata from pypdf
            reader = PdfReader(io.BytesIO(pdf_bytes))
            if reader.metadata:
                metadata["title"] = reader.metadata.get("/Title", "")
                metadata["author"] = reader.metadata.get("/Author", "")
                metadata["creation_date"] = reader.metadata.get("/CreationDate", "")

            return {
                "pages": pages,
                "metadata": metadata,
                "full_text": "\n\n".join(p["text"] for p in pages),
            }

        except Exception as e:
            self.logger.error("pdf_parse_error", error=str(e), filename=filename)
            raise

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[dict]:
        """Split text into overlapping chunks for embedding."""
        if not text:
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            # Try to find a natural break point
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind("\n\n", start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sentence_break = text.rfind(". ", start, end)
                    if sentence_break > start + chunk_size // 2:
                        end = sentence_break + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "start_char": start,
                    "end_char": end,
                })
                chunk_index += 1

            start = end - overlap if end < len(text) else len(text)

        return chunks
