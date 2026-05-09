import os
import time
from .loader import load_pubmed_dataset
from .chunker import chunk_documents
from .embeddings import EmbeddingModel
from .vector_store import FaissVectorStore
from .retriever import Retriever
from .generator import Generator
from typing import Dict, Any

class RAGPipeline:
    def __init__(self, data_dir: str = "../data", index_dir: str = "rag_index"):
        self.data_dir = data_dir
        self.index_dir = index_dir
        os.makedirs(self.index_dir, exist_ok=True)
        
        self.embedding_model = EmbeddingModel()
        self.vector_store = FaissVectorStore(
            index_path=os.path.join(self.index_dir, "faiss_index.bin"),
            meta_path=os.path.join(self.index_dir, "faiss_meta.pkl")
        )
        self.retriever = Retriever(self.embedding_model, self.vector_store)
        self.generator = None # Initialize lazily to avoid Groq errors if key is missing during startup
        
    def index_data(self, file_name: str = "dev.txt", max_docs: int = 1000) -> Dict[str, Any]:
        """
        Indexes data from the dataset.
        """
        file_path = os.path.join(self.data_dir, file_name)
        
        start_time = time.time()
        
        # 1. Load
        print(f"Loading data from {file_path}...")
        docs = load_pubmed_dataset(file_path, max_docs=max_docs)
        
        # 2. Chunk
        print("Chunking documents...")
        chunked_docs = chunk_documents(docs, chunk_size=500, overlap=100)
        
        texts = [doc["text"] for doc in chunked_docs]
        
        # In vector store metadata, we need to store the text so we can retrieve it
        for doc in chunked_docs:
            doc["metadata"]["text"] = doc["text"]
            
        metadatas = [doc["metadata"] for doc in chunked_docs]
        
        # 3. Embed
        print(f"Embedding {len(texts)} chunks...")
        embeddings = self.embedding_model.embed_texts(texts)
        
        # 4. Store
        print("Saving to vector store...")
        self.vector_store.add_embeddings(embeddings, metadatas)
        self.vector_store.save()
        
        end_time = time.time()
        
        return {
            "status": "success",
            "docs_processed": len(docs),
            "chunks_created": len(chunked_docs),
            "time_taken_seconds": end_time - start_time
        }
        
    def query(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        if self.generator is None:
            self.generator = Generator()
            
        total_start_time = time.time()
        
        # Retrieve
        retrieved_chunks, retrieval_time = self.retriever.retrieve(user_query, top_k=top_k)
        
        # Generate
        answer, gen_stats = self.generator.generate(user_query, retrieved_chunks)
        
        total_time = time.time() - total_start_time
        
        return {
            "answer": answer,
            "metrics": {
                "latency_ms": int(total_time * 1000),
                "retrieval_time_ms": int(retrieval_time * 1000),
                "generation_time_ms": int(gen_stats["generation_time"] * 1000),
                "token_usage": gen_stats["tokens"],
                "retrieved_chunks_count": len(retrieved_chunks)
            },
            "context": retrieved_chunks
        }
        
    def status(self) -> Dict[str, Any]:
        return {
            "vector_store_count": self.vector_store.count(),
            "dimension": self.vector_store.dimension,
            "index_path": self.vector_store.index_path
        }
