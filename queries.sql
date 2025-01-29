-- Enable the pgvector extension
create extension if not exists vector;

-- Create the documentation chunks table
create table streamer_knowledge (
    id bigserial primary key,
    session_id text not null,
    file_name varchar not null,
    chunk_number integer not null,
    title varchar not null,
    summary varchar not null,
    content text not null,
    embedding vector(768),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Add a unique constraint to prevent duplicate chunks for the same URL
    unique(session_id, chunk_number)
);

-- Create an index for better vector similarity search performance
create index on streamer_knowledge using ivfflat (embedding vector_cosine_ops);

-- Create a function to search for documentation chunks
create function match_streamer_knowledge (
  query_embedding vector(768),
  user_session_id text,
  match_count int default 5
) returns table (
  id bigint,
  session_id text,
  chunk_number integer,
  title varchar,
  summary varchar,
  content text,
  similarity float
)
language plpgsql
as $$
#variable_conflict use_column
begin
  return query
  select
    id,
    session_id,
    chunk_number,
    title,
    summary,
    content,
    1 - (streamer_knowledge.embedding <=> query_embedding) as similarity
  from streamer_knowledge
  where user_session_id = session_id and similarity > 0.7
  order by streamer_knowledge.embedding <=> query_embedding
  limit match_count;
end;
$$;
