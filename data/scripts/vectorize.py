'''
    Reads policy_doc.md file -> chunks the document -> generates embeddings ->
    Then. Manually store embeddings in a vector database (supabase + pgvector)
'''

import os
import re
import sys
import json
import yaml
import psycopg2
from psycopg2.extras import execute_values
from typing import List, Tuple

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'supabase_config.yaml')
POLICY_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'policy')
POLICY_DOC_PATH = os.path.join(POLICY_DIR, 'policy_doc.md')

with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

PWD = config['pwd']
PROJECT_ID = config['project_id']

# Direct connection URL
# SUPABASE_DB_URL = os.getenv(
#     "SUPABASE_DB_URL",
#     f"postgresql://postgres:{PWD}@db.{PROJECT_ID}.supabase.co:5432/postgres"
# )

# Pooler connection URL
SUPABASE_DB_URL = os.getenv(
    "SUPABASE_DB_URL",
    f"postgresql://postgres.{PROJECT_ID}:{PWD}@aws-1-us-east-2.pooler.supabase.com:5432/postgres"
)

BATCH_SIZE = 10

def get_connection():
    try:
        conn = psycopg2.connect(SUPABASE_DB_URL, connect_timeout = 10)
        return conn

    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        sys.exit(1)


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] #First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def chunk_by_sections(content: str) -> List[Tuple[str, str]]:
    """
    Chunks the content into sections based on the sections in the policy document.
    Returns a list of tuples, where each tuple contains the section name and the content.
    """

    chunks = []
    lines = content.split('\n')

    current_title = None
    current_content = []

    for line in lines:
        if line.strip().startswith('#'):
            if current_title and current_content:
                chunks.append((
                    current_title,
                    '\n'.join(current_content).strip()
                ))

            current_title = line.strip().lstrip('#').strip()
            current_content = []

        else:
            if line.strip() or current_content:
                current_content.append(line)
    
    if current_title and current_content:
        chunks.append((
            current_title,
            '\n'.join(current_content).strip()
        ))

    return chunks


def read_policy_document(file_path: str) -> str:
    with open(file_path, 'r', encoding = 'utf-8') as f:
        return f.read()


def generate_embeddings(texts: List[str], tokenizer, model, device='cpu') -> torch.Tensor:
    """Generates embeddings for a list of text chunks"""
    
    encoded_input = tokenizer(texts, padding=True, truncation=True, return_tensors='pt').to(device)

    with torch.no_grad():
        model_output = model(**encoded_input)
    
    sentence_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    sentence_embeddings = F.normalize(sentence_embeddings, p=2, dim=1)
    
    return sentence_embeddings


def embedding_to_pgvector_string(embedding: torch.Tensor) -> str:
    """Convert embedding tensor to pgvector string format [v1, v2, v3, ...]"""

    embedding_list = embedding.cpu().numpy().tolist()
    # Format as PostgreSQL array string for pgvector
    pgvector_string = '[' + ','.join(str(val) for val in embedding_list) + ']'

    return pgvector_string


def insert_policy_chunks_batch(conn, chunks_data: List[Tuple]):
    """Insert a batch of policy chunks using execute_values"""
    if not chunks_data:
        return
    
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO policy_document (title, content, embedding, metadata)
            VALUES %s
            """,
            chunks_data,
            template = None,
            page_size = 100
        )
    conn.commit()



def main():
    print("=" * 60)
    print("Policy Document Vectorization")
    print("=" * 60)

    if not os.path.exists(POLICY_DOC_PATH):
        print(f"Error: Policy document not found at {POLICY_DOC_PATH}")
        sys.exit(1)
    
    print(f"\nReading policy document...")
    policy_content = read_policy_document(POLICY_DOC_PATH)
    print(f"✓ Read {len(policy_content)} characters")

    print(f"\nChunking policy document into sections...")
    chunks = chunk_by_sections(policy_content)
    print(f"✓ Generated {len(chunks)} chunks")

    if len(chunks) == 0:
        print(f"Error: No chunks generated from policy document. Check document format.")
        sys.exit(1)
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
    model.to(device)
    model.eval()

    print (f"✓ Model loaded")

    # Generate embeddings for each chunk
    titles = [chunk[0] for chunk in chunks]
    contents = [chunk[1] for chunk in chunks]

    EMBEDDING_BATCH_SIZE = 8
    all_embeddings = []

    for i in range(0, len(contents), EMBEDDING_BATCH_SIZE):
        batch = contents[i:i+EMBEDDING_BATCH_SIZE]
        batch_embeddings = generate_embeddings(batch, tokenizer, model, device)
        all_embeddings.append(batch_embeddings)
        print (f"✓ Processed {min(i+EMBEDDING_BATCH_SIZE, len(contents))} of {len(contents)} chunks")

    embeddings = torch.cat(all_embeddings, dim=0)
    print(f"\n✓ Generated {embeddings.shape[0]} embeddings (dimension: {embeddings.shape[1]})")

    # Connect to database
    print (f"\n Connecting to database...")
    conn = get_connection()
    print (f"✓ Connected successfully")

    # Prepare data for insertion
    print("\n📝 Preparing data for insertion...")
    chunks_data = []
    for idx, (title, content) in enumerate(chunks):
        embedding_str = embedding_to_pgvector_string(embeddings[idx])

        metadata = json.dumps({
            'section_number': idx + 1,
            'chunk_type': 'section',
            'document': 'policy_doc.md'
        })

        chunks_data.append((
            title,
            content,
            embedding_str,  # pgvector format: '[v1, v2, v3, ...]'
            metadata
        ))

    # Insert data in batches
    print(f"\n📥 Inserting {len(chunks_data)} chunks in batches of {BATCH_SIZE}...")
    total_inserted = 0

    for i in range(0, len(chunks_data), BATCH_SIZE):
        batch = chunks_data[i:i+BATCH_SIZE]
        try:
            insert_policy_chunks_batch(conn, batch)
            total_inserted += len(batch)
            print(f"  ✓ Inserted {total_inserted}/{len(chunks_data)} chunks...", end='\r')
        except Exception as e:
            print(f"\n❌ Error inserting batch at index {i}: {e}")
            conn.rollback()
            raise
    
    print(f"\n✓ Successfully inserted {total_inserted} chunks")
    
    # Verify final count
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM policy_document;")
        final_count = cur.fetchone()[0]
        print(f"\n✅ Final document count: {final_count}")
    
    conn.close()
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()