import faiss
import numpy as np
import os
import pickle
from typing import List, Dict, Tuple

class FaissVectorStore:
    def __init__(self, dimension: int = 384, index_path: str = "faiss_index.bin", meta_path: str = "faiss_meta.pkl"):
        self.dimension = dimension
        self.index_path = index_path
        self.meta_path = meta_path
        
        if os.path.exists(index_path) and os.path.exists(meta_path):
            self.load()
        else:
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata: List[Dict] = []
            
    def add_embeddings(self, embeddings: np.ndarray, metadata: List[Dict]):
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have the same length")
        
        self.index.add(embeddings.astype('float32'))
        self.metadata.extend(metadata)
        
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Tuple[Dict, float]]:
        if self.index.ntotal == 0:
            return []
            
        distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append((self.metadata[idx], float(distances[0][i])))
        return results
        
    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.metadata, f)
            
    def load(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, 'rb') as f:
            self.metadata = pickle.load(f)
            
    def count(self) -> int:
        return self.index.ntotal
