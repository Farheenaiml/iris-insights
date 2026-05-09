from .embeddings import EmbeddingModel
from .vector_store import FaissVectorStore
import time
from typing import List, Dict, Tuple

class Retriever:
    def __init__(self, embedding_model: EmbeddingModel, vector_store: FaissVectorStore):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        
    def retrieve(self, query: str, top_k: int = 5) -> Tuple[List[Dict], float]:
        start_time = time.time()
        query_emb = self.embedding_model.embed_query(query)
        results = self.vector_store.search(query_emb, top_k=top_k)
        
        retrieved_chunks = []
        for meta, distance in results:
            retrieved_chunks.append({
                "text": meta.get("text", ""),
                "metadata": meta,
                "distance": distance
            })
            
        retrieval_time = time.time() - start_time
        return retrieved_chunks, retrieval_time
