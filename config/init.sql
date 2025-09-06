-- Initialize PostgreSQL database with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database user for the application
-- (already exists as postgres user from docker-compose)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE neetimanthan TO postgres;
