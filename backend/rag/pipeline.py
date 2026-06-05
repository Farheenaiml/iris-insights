import os
import time
from .loader import load_pubmed_dataset
from .chunker import chunk_documents
from .embeddings import EmbeddingModel
from .vector_store import FaissVectorStore
from .retriever import Retriever
from .generator import Generator
from .graph_store import MedicalGraphStore
from .extractor import MedicalExtractor
from typing import Dict, Any, List

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
        
        # GraphRAG additions
        self.graph_store = MedicalGraphStore(
            filepath=os.path.join(self.index_dir, "medical_graph.json")
        )
        self.extractor = MedicalExtractor()
        
        # Pre-seed graph if it is empty
        if self.graph_store.graph.number_of_nodes() == 0:
            self._seed_graph()
            
    def _seed_graph(self):
        """Pre-seeds the medical knowledge graph with key study relationships from the dataset."""
        print("Pre-seeding medical knowledge graph with core dataset relationships...")
        
        # 1. Dermabond vs Sutures (PMID 14744358)
        self.graph_store.add_node("Dermabond", "treatment")
        self.graph_store.add_node("Subcuticular sutures", "treatment")
        self.graph_store.add_node("Laparoscopic trocar sites", "condition")
        self.graph_store.add_node("3.7 minutes", "metric")
        self.graph_store.add_node("14.0 minutes", "metric")
        self.graph_store.add_node("$198 USD", "metric")
        self.graph_store.add_node("$497 USD", "metric")
        self.graph_store.add_node("Wound complications", "condition")
        self.graph_store.add_node("Subcuticular seroma", "condition")

        self.graph_store.add_edge("Dermabond", "Subcuticular sutures", "compared_to")
        self.graph_store.add_edge("Dermabond", "Laparoscopic trocar sites", "used_for_closure_of")
        self.graph_store.add_edge("Subcuticular sutures", "Laparoscopic trocar sites", "used_for_closure_of")
        self.graph_store.add_edge("Dermabond", "3.7 minutes", "has_average_closure_time")
        self.graph_store.add_edge("Subcuticular sutures", "14.0 minutes", "has_average_closure_time")
        self.graph_store.add_edge("Dermabond", "$198 USD", "has_average_closure_cost")
        self.graph_store.add_edge("Subcuticular sutures", "$497 USD", "has_average_closure_cost")
        self.graph_store.add_edge("Dermabond", "Wound complications", "causes_same_rate_as_sutures")
        self.graph_store.add_edge("Wound complications", "Subcuticular seroma", "includes")

        # 2. Atenolol vs Perindopril (PMID 11023935)
        self.graph_store.add_node("Perindopril", "drug")
        self.graph_store.add_node("Atenolol", "drug")
        self.graph_store.add_node("Obese hypertensive patients", "condition")
        self.graph_store.add_node("Left ventricular mass (LVM)", "metric")
        self.graph_store.add_node("Glucose & insulin metabolism (GIM)", "metric")
        self.graph_store.add_node("Regression of LVM", "metric")
        self.graph_store.add_node("Worsened GIM profile", "metric")

        self.graph_store.add_edge("Perindopril", "Atenolol", "compared_to")
        self.graph_store.add_edge("Perindopril", "Obese hypertensive patients", "used_to_treat")
        self.graph_store.add_edge("Atenolol", "Obese hypertensive patients", "used_to_treat")
        self.graph_store.add_edge("Perindopril", "Regression of LVM", "leads_to")
        self.graph_store.add_edge("Regression of LVM", "Left ventricular mass (LVM)", "improves")
        self.graph_store.add_edge("Atenolol", "Left ventricular mass (LVM)", "has_no_effect_on")
        self.graph_store.add_edge("Perindopril", "Glucose & insulin metabolism (GIM)", "does_not_affect")
        self.graph_store.add_edge("Atenolol", "Worsened GIM profile", "leads_to")
        self.graph_store.add_edge("Worsened GIM profile", "Glucose & insulin metabolism (GIM)", "degrades")

        # 3. Bucindolol (BEST Trial, PMID 15337700)
        self.graph_store.add_node("Bucindolol", "drug")
        self.graph_store.add_node("Placebo", "treatment")
        self.graph_store.add_node("Chronic heart failure (CHF)", "condition")
        self.graph_store.add_node("Sympatholysis", "condition")
        self.graph_store.add_node("Increased risk of death", "condition")
        self.graph_store.add_node("Systemic venous norepinephrine", "metric")

        self.graph_store.add_edge("Bucindolol", "Placebo", "compared_to")
        self.graph_store.add_edge("Bucindolol", "Chronic heart failure (CHF)", "used_to_treat")
        self.graph_store.add_edge("Bucindolol", "Sympatholysis", "causes_in_subset")
        self.graph_store.add_edge("Sympatholysis", "Increased risk of death", "leads_to")
        self.graph_store.add_edge("Bucindolol", "Systemic venous norepinephrine", "reduces")

        # 4. REM sleep (PMID 25409100)
        self.graph_store.add_node("REM sleep", "condition")
        self.graph_store.add_node("NREM sleep", "condition")
        self.graph_store.add_node("Semantic priming", "metric")
        self.graph_store.add_node("Associational breadth", "metric")
        self.graph_store.add_node("Emotional cue words", "value")

        self.graph_store.add_edge("REM sleep", "Semantic priming", "selectively_consolidates")
        self.graph_store.add_edge("REM sleep", "Associational breadth", "enhances")
        self.graph_store.add_edge("Semantic priming", "Emotional cue words", "occurs_for")
        self.graph_store.add_edge("NREM sleep", "Semantic priming", "does_not_consolidate")

        # 5. Personal Formulary (PMID 18338161)
        self.graph_store.add_node("Personal formulary training", "treatment")
        self.graph_store.add_node("Existing formulary training", "treatment")
        self.graph_store.add_node("Prescribing competency", "metric")
        self.graph_store.add_node("23% score increase", "metric")
        self.graph_store.add_node("19% score increase", "metric")
        self.graph_store.add_node("Classic medical curriculum", "condition")

        self.graph_store.add_edge("Personal formulary training", "Existing formulary training", "compared_to")
        self.graph_store.add_edge("Personal formulary training", "23% score increase", "leads_to_competency_gain")
        self.graph_store.add_edge("Existing formulary training", "19% score increase", "leads_to_competency_gain")
        self.graph_store.add_edge("23% score increase", "Prescribing competency", "improves")
        self.graph_store.add_edge("19% score increase", "Prescribing competency", "improves")
        self.graph_store.add_edge("Personal formulary training", "Classic medical curriculum", "highly_effective_in")

        self.graph_store.save()

    def index_data(self, file_name: str = "dev.txt", max_docs: int = 1000) -> Dict[str, Any]:
        """
        Indexes data from the dataset into both Vector and Graph stores.
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
        
        for doc in chunked_docs:
            doc["metadata"]["text"] = doc["text"]
        metadatas = [doc["metadata"] for doc in chunked_docs]
        
        # 3. Embed & save vector index
        print(f"Embedding {len(texts)} chunks...")
        embeddings = self.embedding_model.embed_texts(texts)
        print("Saving to vector store...")
        self.vector_store.add_embeddings(embeddings, metadatas)
        self.vector_store.save()
        
        # 4. Extract entities & relations for the graph
        # Limit LLM extraction to the first 30 chunks to prevent rate-limiting during bulk indexing
        print("Extracting GraphRAG triples from text chunks...")
        extracted_count = 0
        for i, chunk in enumerate(chunked_docs[:30]):
            try:
                entities, relations = self.extractor.extract_triples_from_text(chunk["text"])
                if entities or relations:
                    extracted_count += 1
                    for ent in entities:
                        self.graph_store.add_node(ent["name"], ent.get("type", "Entity"))
                    for rel in relations:
                        self.graph_store.add_edge(rel["source"], rel["target"], rel["type"])
            except Exception as e:
                print(f"Failed to extract triples for chunk {i}: {e}")
                
        if extracted_count > 0:
            self.graph_store.save()
        
        end_time = time.time()
        
        return {
            "status": "success",
            "docs_processed": len(docs),
            "chunks_created": len(chunked_docs),
            "graph_chunks_extracted": extracted_count,
            "time_taken_seconds": end_time - start_time
        }
        
    def query(self, user_query: str, top_k: int = 5) -> Dict[str, Any]:
        """Runs standard Vector RAG query."""
        if self.generator is None:
            self.generator = Generator()
            
        total_start_time = time.time()
        retrieved_chunks, retrieval_time = self.retriever.retrieve(user_query, top_k=top_k)
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

    def query_graph_rag(self, user_query: str) -> Dict[str, Any]:
        """
        Runs the GraphRAG query:
        1. Extract query entities
        2. Query sub-graph relations (triples)
        3. Prompt generator with compressed structured triples instead of large paragraphs.
        """
        if self.generator is None:
            self.generator = Generator()
            
        total_start_time = time.time()
        reasoning_path = []
        
        # 1. Extract query entities
        reasoning_path.append("Step 1: Extract entities from user query")
        query_entities = self.extractor.extract_entities_from_query(user_query)
        print(f"Extracted entities for graph lookup: {query_entities}")
        
        # 2. Query matching subgraph
        reasoning_path.append(f"Step 2: Look up matched concepts in Knowledge Graph: {', '.join(query_entities)}")
        nodes, edges, triples = self.graph_store.get_subgraph_for_entities(query_entities, max_depth=1)
        
        # 3. Handle Fallback if graph is sparse/empty for this query
        if not triples:
            reasoning_path.append("Step 3: Graph sparse - Fallback to vector search for supplemental context")
            # Retrieve vector context chunks but represent them as a synthetic graph
            retrieved_chunks, _ = self.retriever.retrieve(user_query, top_k=2)
            context_text = "\n".join([c["text"] for c in retrieved_chunks])
            
            # Formulate answer using standard generator
            answer, gen_stats = self.generator.generate(user_query, retrieved_chunks)
            
            # Create a simple synthetic node pair for UI
            nodes = [{"id": q, "group": 0} for q in query_entities[:3]]
            edges = []
            if len(nodes) >= 2:
                edges = [{"source": nodes[0]["id"], "target": nodes[1]["id"], "relation": "related_to", "highlight": True}]
        else:
            reasoning_path.append(f"Step 3: Found {len(triples)} relevant relationships. Constructing compressed GraphRAG prompt.")
            
            # Format triples context for generator
            triples_context = "\n".join(triples)
            
            system_prompt = (
                "You are a helpful AI assistant. Answer the user's query using ONLY the provided structured facts (Knowledge Graph triples).\n"
                "Be extremely precise and concise. Do not use extra words. Keep your answer direct.\n\n"
                f"KNOWLEDGE GRAPH RELATIONSHIPS:\n{triples_context}"
            )
            
            # Use Groq to generate response
            gen_start = time.time()
            completion = self.generator.client.chat.completions.create(
                model=self.generator.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.1,
                max_tokens=512
            )
            gen_end = time.time()
            
            answer = completion.choices[0].message.content
            
            gen_stats = {
                "generation_time": gen_end - gen_start,
                "tokens": {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens
                }
            }
            
        total_time = time.time() - total_start_time
        
        return {
            "answer": answer,
            "metrics": {
                "latency_ms": int(total_time * 1000),
                "generation_time_ms": int(gen_stats["generation_time"] * 1000),
                "token_usage": gen_stats["tokens"]
            },
            "reasoning_path": reasoning_path,
            "graph": {
                "nodes": nodes,
                "edges": edges
            }
        }
        
    def status(self) -> Dict[str, Any]:
        return {
            "vector_store_count": self.vector_store.count(),
            "dimension": self.vector_store.dimension,
            "index_path": self.vector_store.index_path,
            "graph_nodes_count": self.graph_store.graph.number_of_nodes(),
            "graph_edges_count": self.graph_store.graph.number_of_edges()
        }
