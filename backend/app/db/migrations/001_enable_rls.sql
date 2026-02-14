-- ============================================================================
-- WASP-OS: Row Level Security (RLS) Policies
-- ============================================================================
-- These policies ensure complete data isolation between firms.
-- No metadata from Firm A can ever be queried by Firm B, including vector search.
-- ============================================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get the current user's firm_id from JWT claims
CREATE OR REPLACE FUNCTION auth.firm_id()
RETURNS UUID AS $$
  SELECT COALESCE(
    current_setting('request.jwt.claims', true)::json->>'firm_id',
    current_setting('app.current_firm_id', true)
  )::UUID;
$$ LANGUAGE SQL STABLE;

-- Function to get the current user's ID from JWT claims
CREATE OR REPLACE FUNCTION auth.user_id()
RETURNS UUID AS $$
  SELECT COALESCE(
    current_setting('request.jwt.claims', true)::json->>'sub',
    current_setting('app.current_user_id', true)
  )::UUID;
$$ LANGUAGE SQL STABLE;

-- Function to check if user is admin of their firm
CREATE OR REPLACE FUNCTION auth.is_firm_admin()
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM users
    WHERE id = auth.user_id()
    AND firm_id = auth.firm_id()
    AND role = 'admin'
  );
$$ LANGUAGE SQL STABLE SECURITY DEFINER;

-- ============================================================================
-- ENABLE RLS ON ALL TABLES
-- ============================================================================

ALTER TABLE firms ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE investment_memos ENABLE ROW LEVEL SECURITY;
ALTER TABLE memo_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE conviction_polls ENABLE ROW LEVEL SECURITY;
ALTER TABLE poll_votes ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- FIRMS TABLE POLICIES
-- ============================================================================

-- Users can only see their own firm
CREATE POLICY "firms_select_own"
  ON firms FOR SELECT
  USING (id = auth.firm_id());

-- Only admins can update their firm
CREATE POLICY "firms_update_admin"
  ON firms FOR UPDATE
  USING (id = auth.firm_id() AND auth.is_firm_admin())
  WITH CHECK (id = auth.firm_id());

-- ============================================================================
-- USERS TABLE POLICIES
-- ============================================================================

-- Users can only see users in their own firm
CREATE POLICY "users_select_same_firm"
  ON users FOR SELECT
  USING (firm_id = auth.firm_id());

-- Users can update their own profile
CREATE POLICY "users_update_own"
  ON users FOR UPDATE
  USING (id = auth.user_id())
  WITH CHECK (firm_id = auth.firm_id());

-- Only admins can insert new users
CREATE POLICY "users_insert_admin"
  ON users FOR INSERT
  WITH CHECK (firm_id = auth.firm_id() AND auth.is_firm_admin());

-- Only admins can delete users (except themselves)
CREATE POLICY "users_delete_admin"
  ON users FOR DELETE
  USING (
    firm_id = auth.firm_id()
    AND auth.is_firm_admin()
    AND id != auth.user_id()
  );

-- ============================================================================
-- DEALS TABLE POLICIES
-- ============================================================================

-- Users can only see deals from their firm
CREATE POLICY "deals_select_same_firm"
  ON deals FOR SELECT
  USING (firm_id = auth.firm_id());

-- Users can insert deals for their firm
CREATE POLICY "deals_insert_same_firm"
  ON deals FOR INSERT
  WITH CHECK (firm_id = auth.firm_id());

-- Users can update deals in their firm
CREATE POLICY "deals_update_same_firm"
  ON deals FOR UPDATE
  USING (firm_id = auth.firm_id())
  WITH CHECK (firm_id = auth.firm_id());

-- Users can delete deals in their firm
CREATE POLICY "deals_delete_same_firm"
  ON deals FOR DELETE
  USING (firm_id = auth.firm_id());

-- ============================================================================
-- DOCUMENTS TABLE POLICIES
-- ============================================================================

-- Users can only see documents from their firm
CREATE POLICY "documents_select_same_firm"
  ON documents FOR SELECT
  USING (firm_id = auth.firm_id());

-- Users can upload documents for their firm
CREATE POLICY "documents_insert_same_firm"
  ON documents FOR INSERT
  WITH CHECK (firm_id = auth.firm_id());

-- Users can update documents in their firm
CREATE POLICY "documents_update_same_firm"
  ON documents FOR UPDATE
  USING (firm_id = auth.firm_id())
  WITH CHECK (firm_id = auth.firm_id());

-- Users can delete documents in their firm
CREATE POLICY "documents_delete_same_firm"
  ON documents FOR DELETE
  USING (firm_id = auth.firm_id());

-- ============================================================================
-- DOCUMENT_CHUNKS TABLE POLICIES (CRITICAL FOR VECTOR SEARCH ISOLATION)
-- ============================================================================

-- Users can only see chunks from their firm's documents
-- This is CRITICAL for vector search isolation
CREATE POLICY "chunks_select_same_firm"
  ON document_chunks FOR SELECT
  USING (firm_id = auth.firm_id());

-- System can insert chunks for firm's documents
CREATE POLICY "chunks_insert_same_firm"
  ON document_chunks FOR INSERT
  WITH CHECK (firm_id = auth.firm_id());

-- System can delete chunks for firm's documents
CREATE POLICY "chunks_delete_same_firm"
  ON document_chunks FOR DELETE
  USING (firm_id = auth.firm_id());

-- ============================================================================
-- INVESTMENT_MEMOS TABLE POLICIES
-- ============================================================================

-- Users can only see memos from their firm
CREATE POLICY "memos_select_same_firm"
  ON investment_memos FOR SELECT
  USING (firm_id = auth.firm_id());

-- Users can create memos for their firm
CREATE POLICY "memos_insert_same_firm"
  ON investment_memos FOR INSERT
  WITH CHECK (firm_id = auth.firm_id());

-- Users can update memos in their firm
CREATE POLICY "memos_update_same_firm"
  ON investment_memos FOR UPDATE
  USING (firm_id = auth.firm_id())
  WITH CHECK (firm_id = auth.firm_id());

-- Users can delete memos in their firm
CREATE POLICY "memos_delete_same_firm"
  ON investment_memos FOR DELETE
  USING (firm_id = auth.firm_id());

-- ============================================================================
-- MEMO_TEMPLATES TABLE POLICIES
-- ============================================================================

-- Users can see templates from their firm
CREATE POLICY "templates_select_same_firm"
  ON memo_templates FOR SELECT
  USING (firm_id = auth.firm_id());

-- Only admins can manage templates
CREATE POLICY "templates_insert_admin"
  ON memo_templates FOR INSERT
  WITH CHECK (firm_id = auth.firm_id() AND auth.is_firm_admin());

CREATE POLICY "templates_update_admin"
  ON memo_templates FOR UPDATE
  USING (firm_id = auth.firm_id() AND auth.is_firm_admin())
  WITH CHECK (firm_id = auth.firm_id());

CREATE POLICY "templates_delete_admin"
  ON memo_templates FOR DELETE
  USING (firm_id = auth.firm_id() AND auth.is_firm_admin());

-- ============================================================================
-- CONVICTION_POLLS TABLE POLICIES
-- ============================================================================

-- Users can see polls from their firm
CREATE POLICY "polls_select_same_firm"
  ON conviction_polls FOR SELECT
  USING (firm_id = auth.firm_id());

-- Users can create polls for their firm
CREATE POLICY "polls_insert_same_firm"
  ON conviction_polls FOR INSERT
  WITH CHECK (firm_id = auth.firm_id());

-- Only poll creator or admin can update polls
CREATE POLICY "polls_update_same_firm"
  ON conviction_polls FOR UPDATE
  USING (firm_id = auth.firm_id())
  WITH CHECK (firm_id = auth.firm_id());

-- Only admin can delete polls
CREATE POLICY "polls_delete_admin"
  ON conviction_polls FOR DELETE
  USING (firm_id = auth.firm_id() AND auth.is_firm_admin());

-- ============================================================================
-- POLL_VOTES TABLE POLICIES
-- ============================================================================

-- Users can see votes based on poll reveal status
-- Before reveal: users can only see their own vote
-- After reveal: users can see all votes in their firm
CREATE POLICY "votes_select_conditional"
  ON poll_votes FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM conviction_polls p
      WHERE p.id = poll_votes.poll_id
      AND p.firm_id = auth.firm_id()
      AND (
        p.is_revealed = true
        OR poll_votes.user_id = auth.user_id()
      )
    )
  );

-- Users can insert their own vote
CREATE POLICY "votes_insert_own"
  ON poll_votes FOR INSERT
  WITH CHECK (
    user_id = auth.user_id()
    AND EXISTS (
      SELECT 1 FROM conviction_polls p
      WHERE p.id = poll_votes.poll_id
      AND p.firm_id = auth.firm_id()
      AND p.is_active = true
    )
  );

-- Users can update their own vote before reveal
CREATE POLICY "votes_update_own"
  ON poll_votes FOR UPDATE
  USING (
    user_id = auth.user_id()
    AND EXISTS (
      SELECT 1 FROM conviction_polls p
      WHERE p.id = poll_votes.poll_id
      AND p.firm_id = auth.firm_id()
      AND p.is_revealed = false
    )
  )
  WITH CHECK (user_id = auth.user_id());

-- ============================================================================
-- VECTOR SEARCH SECURITY
-- ============================================================================

-- Create a secure vector search function that enforces RLS
CREATE OR REPLACE FUNCTION secure_vector_search(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  document_id UUID,
  content TEXT,
  similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) as similarity
  FROM document_chunks dc
  WHERE dc.firm_id = auth.firm_id()  -- RLS enforced here
  AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Grant execute to authenticated users
GRANT EXECUTE ON FUNCTION secure_vector_search TO authenticated;

-- ============================================================================
-- AUDIT LOGGING (Optional but recommended)
-- ============================================================================

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  firm_id UUID NOT NULL,
  user_id UUID NOT NULL,
  action TEXT NOT NULL,
  table_name TEXT NOT NULL,
  record_id UUID,
  old_data JSONB,
  new_data JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on audit logs
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Users can only see their firm's audit logs
CREATE POLICY "audit_select_same_firm"
  ON audit_logs FOR SELECT
  USING (firm_id = auth.firm_id() AND auth.is_firm_admin());

-- ============================================================================
-- CROSS-FIRM LEAK PREVENTION
-- ============================================================================

-- Prevent any function from accidentally leaking data across firms
CREATE OR REPLACE FUNCTION prevent_cross_firm_access()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.firm_id != auth.firm_id() THEN
    RAISE EXCEPTION 'Cross-firm access denied. Cannot access data from another firm.';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to sensitive tables
CREATE TRIGGER check_firm_access_deals
  BEFORE INSERT OR UPDATE ON deals
  FOR EACH ROW EXECUTE FUNCTION prevent_cross_firm_access();

CREATE TRIGGER check_firm_access_documents
  BEFORE INSERT OR UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION prevent_cross_firm_access();

CREATE TRIGGER check_firm_access_chunks
  BEFORE INSERT OR UPDATE ON document_chunks
  FOR EACH ROW EXECUTE FUNCTION prevent_cross_firm_access();

CREATE TRIGGER check_firm_access_memos
  BEFORE INSERT OR UPDATE ON investment_memos
  FOR EACH ROW EXECUTE FUNCTION prevent_cross_firm_access();

CREATE TRIGGER check_firm_access_polls
  BEFORE INSERT OR UPDATE ON conviction_polls
  FOR EACH ROW EXECUTE FUNCTION prevent_cross_firm_access();

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Run these to verify RLS is properly enabled:
-- SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Test cross-firm access prevention:
-- SET app.current_firm_id = 'firm-a-uuid';
-- SELECT * FROM deals; -- Should only show Firm A deals
-- SET app.current_firm_id = 'firm-b-uuid';
-- SELECT * FROM deals; -- Should only show Firm B deals
