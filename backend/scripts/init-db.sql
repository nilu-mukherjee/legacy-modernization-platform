-- =============================================================================
-- CodeLens AI — Database Initialization Script
-- =============================================================================
-- This script runs automatically when the PostgreSQL container starts for the
-- first time. It enables required extensions.
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector similarity search (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";

-- Enable trigram text search (for fuzzy matching)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'CodeLens AI database initialized with extensions: uuid-ossp, vector, pg_trgm';
END
$$;
