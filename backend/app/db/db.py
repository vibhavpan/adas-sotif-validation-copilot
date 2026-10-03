from sentence_transformers import SentenceTransformer

#Free, CPU-friendly local embedding model
embedder=SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text:str):
    return embedder.encode(text).tolist()


