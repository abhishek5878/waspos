-- Rename reserved 'metadata' column on document_chunks to chunk_metadata (SQLAlchemy Declarative API)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'metadata'
  ) THEN
    ALTER TABLE document_chunks RENAME COLUMN metadata TO chunk_metadata;
  END IF;
END $$;
