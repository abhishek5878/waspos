#!/usr/bin/env python3
"""
CLI tool to index historical IC memos into the vector store.

Usage:
    python scripts/index_memos.py --firm-id <uuid> --folder <path>
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.db.pgbouncer import get_pgbouncer_connect_args
from app.models.document import Document, DocumentType
from app.services.memory.pdf_parser import PDFParser
from app.services.memory.vector_store import VectorStore


async def index_folder(firm_id: UUID, folder_path: str, db_url: str):
    """Index all PDFs in a folder into the vector store."""
    folder = Path(folder_path)
    if not folder.exists():
        print(f"Error: Folder not found: {folder_path}")
        return

    pdf_files = list(folder.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return

    print(f"Found {len(pdf_files)} PDF files to index")

    # Create database connection (pgbouncer-safe for Supabase transaction pool mode)
    engine = create_async_engine(db_url, connect_args=get_pgbouncer_connect_args())
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    parser = PDFParser()

    async with async_session() as db:
        vector_store = VectorStore(db, firm_id)

        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")

            try:
                # Check if already indexed
                # (simplified - would need proper check in production)

                # Parse PDF
                with open(pdf_path, "rb") as f:
                    content = f.read()

                parsed = await parser.parse_bytes(content, pdf_path.name)

                # Create document record
                doc = Document(
                    firm_id=firm_id,
                    filename=pdf_path.name,
                    original_filename=pdf_path.name,
                    file_path=str(pdf_path),
                    file_size=len(content),
                    mime_type="application/pdf",
                    document_type=DocumentType.IC_MEMO,
                    is_processed="yes",
                    page_count=parsed["metadata"].get("page_count", 0),
                )
                db.add(doc)
                await db.flush()

                # Chunk and embed
                chunks = parser.chunk_text(parsed["full_text"])
                for chunk in chunks:
                    chunk["section_type"] = "ic_memo"

                await vector_store.add_chunks(doc.id, chunks)

                print(f"  ✓ Indexed {len(chunks)} chunks")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue

        await db.commit()

    print(f"\nDone! Indexed {len(pdf_files)} memos for firm {firm_id}")


def main():
    parser = argparse.ArgumentParser(description="Index historical IC memos")
    parser.add_argument("--firm-id", required=True, help="Firm UUID")
    parser.add_argument("--folder", required=True, help="Path to folder with PDF memos")
    parser.add_argument("--db-url", default=settings.DATABASE_URL, help="Database URL")

    args = parser.parse_args()

    try:
        firm_id = UUID(args.firm_id)
    except ValueError:
        print(f"Error: Invalid UUID: {args.firm_id}")
        sys.exit(1)

    asyncio.run(index_folder(firm_id, args.folder, args.db_url))


if __name__ == "__main__":
    main()
