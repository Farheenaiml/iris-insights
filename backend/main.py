import os
import time
import base64
from io import BytesIO
from fastapi import FastAPI, HTTPException, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient
import PyPDF2
from rag import RAGPipeline

# Load environment variables from .env file
load_dotenv()

# Initialize RAG Pipeline
rag_pipeline = RAGPipeline(data_dir="../data", index_dir="rag_index")

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# Initialize Tavily client
tavily_api_key = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None

# QueryRequest is removed because we use Form/File inputs directly.

class BaselineResponse(BaseModel):
    answer: str
    tokens: int
    responseTime: int
    cost: float

class VectorRAGResponse(BaseModel):
    answer: str
    tokens: int
    responseTime: int
    cost: float
    retrievedChunks: int

class GraphNode(BaseModel):
    id: str
    group: int

class GraphEdge(BaseModel):
    source: str
    target: str
    highlight: Optional[bool] = False

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class GraphRAGResponse(BaseModel):
    answer: str
    tokens: int
    responseTime: int
    cost: float
    reasoningPath: List[str]
    graph: GraphData

class Comparison(BaseModel):
    tokensSavedPct: int
    timeSavedPct: int
    costSavedPct: int

class QueryResponse(BaseModel):
    query: str
    baseline: BaselineResponse
    vectorrag: VectorRAGResponse
    graphrag: GraphRAGResponse
    comparison: Comparison

@app.post("/api/query", response_model=QueryResponse)
async def handle_query(
    query: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    if not groq_client:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured in backend.")

    start_time = time.time()
    
    context = ""
    is_image = False
    base64_image = ""
    mime_type = ""

    # Process file if provided
    temp_pipeline = None
    if file:
        file_bytes = await file.read()
        mime_type = file.content_type
        
        extracted_text = ""
        if mime_type.startswith("image/"):
            is_image = True
            base64_image = base64.b64encode(file_bytes).decode("utf-8")
        elif mime_type == "application/pdf":
            try:
                reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                for page in reader.pages:
                    extracted_text += page.extract_text() + "\n"
                
                if len(extracted_text) > 15000:
                    extracted_text = extracted_text[:15000] + "\n...[Content truncated due to size limits]..."
                    
                context += f"\n\nExtracted PDF Document Content:\n{extracted_text}"
            except Exception as e:
                print(f"Failed to read PDF: {e}")
        elif mime_type == "text/plain" or mime_type.startswith("text/"):
            try:
                extracted_text = file_bytes.decode("utf-8")
                
                if len(extracted_text) > 15000:
                    extracted_text = extracted_text[:15000] + "\n...[Content truncated due to size limits]..."
                    
                context += f"\n\nExtracted Text File Content:\n{extracted_text}"
            except Exception as e:
                print(f"Failed to read text file: {e}")

        # Index text content dynamically
        if extracted_text.strip() and not is_image:
            try:
                print(f"Dynamically indexing uploaded file ({len(extracted_text)} chars)...")
                # Create a temporary index directory specifically for this request
                temp_index_dir = os.path.join(os.path.dirname(__file__), f"temp_index_{int(time.time())}")
                temp_pipeline = RAGPipeline(index_dir=temp_index_dir)
                
                # Chunk the text
                from rag.chunker import chunk_documents
                pseudo_docs = [{
                    "pmid": "uploaded_doc",
                    "text": extracted_text,
                    "metadata": {
                        "pmid": "uploaded_doc",
                        "source": file.filename
                    }
                }]
                chunked_docs = chunk_documents(pseudo_docs, chunk_size=300, overlap=50)
                
                # Add to Vector Store
                texts = [doc["text"] for doc in chunked_docs]
                for doc in chunked_docs:
                    doc["metadata"]["text"] = doc["text"]
                metadatas = [doc["metadata"] for doc in chunked_docs]
                
                embeddings = temp_pipeline.embedding_model.embed_texts(texts)
                temp_pipeline.vector_store.add_embeddings(embeddings, metadatas)
                
                # Add to Graph Store (limit to first 8 chunks to keep it fast)
                for chunk in chunked_docs[:8]:
                    try:
                        entities, relations = temp_pipeline.extractor.extract_triples_from_text(chunk["text"])
                        for ent in entities:
                            temp_pipeline.graph_store.add_node(ent["name"], ent.get("type", "Entity"))
                        for rel in relations:
                            temp_pipeline.graph_store.add_edge(rel["source"], rel["target"], rel["type"])
                    except Exception as e:
                        print(f"Temp graph extraction failed: {e}")
                
                temp_pipeline.graph_store.save()
            except Exception as e:
                print(f"Failed to dynamically index uploaded file: {e}")

    # Web search
    if tavily_client and not is_image: # Skip search for pure image analysis usually, but let's allow it if there's a strong query
        try:
            search_response = tavily_client.search(query=query, search_depth="basic")
            results = search_response.get("results", [])
            context += "\n\nWeb Search Results:\n" + "\n".join([f"- [{res['title']}]({res.get('url', '')}): {res['content']}" for res in results])
        except Exception as e:
            print(f"Tavily search failed: {e}")

    system_prompt = "You are a helpful AI assistant. Answer the user's query clearly and concisely. Format your response nicely using Markdown (use proper bullet points for lists)."
    
    if context:
        if len(context) > 15000:
            context = context[:15000] + "\n...[Context truncated due to size limits]..."
        system_prompt += f"\n\nUse the following context to inform your answer. Important: ALWAYS include the source URLs as clickable markdown links (e.g. [Title](URL)) for any information you reference from the search results!\n{context}"

    try:
        if is_image:
            raise HTTPException(status_code=400, detail="Image analysis is temporarily unavailable as Groq has decommissioned their vision models. Please upload a PDF or Text file instead.")
        else:
            # Standard Text Request
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            model = "llama-3.1-8b-instant"

        completion = groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=1024,
        )
        end_time = time.time()
        
        baseline_answer = completion.choices[0].message.content
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        baseline_tokens = prompt_tokens + completion_tokens
        
        baseline_time = int((end_time - start_time) * 1000) # in ms
        
        # Estimate cost (e.g., LLaMA3 8B is ~$0.05 / 1M tokens for input, ~$0.08 / 1M for output)
        baseline_cost = (prompt_tokens * 0.05 / 1000000) + (completion_tokens * 0.08 / 1000000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with Groq: {str(e)}")

    # Determine which pipeline to query (temp file-based or global database)
    active_pipeline = temp_pipeline if temp_pipeline else rag_pipeline

    # 2. VectorRAG Pipeline
    try:
        if is_image:
            # Fallback if image
            vr_answer = "Vector RAG not supported for images directly."
            vr_tokens = 0
            vr_time = 0
            vr_cost = 0.0
            vr_chunks = 0
        else:
            rag_res = active_pipeline.query(user_query=query, top_k=5)
            vr_answer = rag_res["answer"]
            vr_time = rag_res["metrics"]["latency_ms"]
            p_tokens = rag_res["metrics"]["token_usage"]["prompt_tokens"]
            c_tokens = rag_res["metrics"]["token_usage"]["completion_tokens"]
            vr_tokens = p_tokens + c_tokens
            vr_cost = (p_tokens * 0.05 / 1000000) + (c_tokens * 0.08 / 1000000)
            vr_chunks = rag_res["metrics"]["retrieved_chunks_count"]
    except Exception as e:
        print(f"Vector RAG failed: {e}")
        vr_answer = f"Vector RAG failed: {str(e)}"
        vr_tokens = 0
        vr_time = 0
        vr_cost = 0.0
        vr_chunks = 0

    # 3. GraphRAG Pipeline (Actual Implementation)
    try:
        if is_image:
            gr_answer = "Graph RAG not supported for images."
            gr_tokens = 0
            gr_time = 0
            gr_cost = 0.0
            gr_reasoning = ["Image queries bypass graph search"]
            gr_graph = GraphData(nodes=[], edges=[])
        else:
            gr_res = active_pipeline.query_graph_rag(user_query=query)
            gr_answer = gr_res["answer"]
            gr_time = gr_res["metrics"]["latency_ms"]
            p_tokens = gr_res["metrics"]["token_usage"]["prompt_tokens"]
            c_tokens = gr_res["metrics"]["token_usage"]["completion_tokens"]
            gr_tokens = p_tokens + c_tokens
            gr_cost = (p_tokens * 0.05 / 1000000) + (c_tokens * 0.08 / 1000000)
            gr_reasoning = gr_res["reasoning_path"]
            gr_graph = GraphData(
                nodes=[GraphNode(id=n["id"], group=n["group"]) for n in gr_res["graph"]["nodes"]],
                edges=[GraphEdge(source=e["source"], target=e["target"], highlight=e.get("highlight", False)) for e in gr_res["graph"]["edges"]]
            )
    except Exception as e:
        print(f"Graph RAG failed: {e}")
        gr_answer = f"Graph RAG failed: {str(e)}"
        gr_tokens = 0
        gr_time = 0
        gr_cost = 0.0
        gr_reasoning = [f"Failed: {str(e)}"]
        gr_graph = GraphData(nodes=[], edges=[])

    # Clean up temp index folder if created
    if temp_pipeline:
        try:
            import shutil
            shutil.rmtree(temp_pipeline.index_dir, ignore_errors=True)
        except Exception as e:
            print(f"Failed to delete temp index dir: {e}")

    # Calculate savings compared to Baseline
    tokens_saved_pct = round(((baseline_tokens - gr_tokens) / baseline_tokens) * 100) if baseline_tokens > 0 else 0
    time_saved_pct = round(((baseline_time - gr_time) / baseline_time) * 100) if baseline_time > 0 else 0
    cost_saved_pct = round(((baseline_cost - gr_cost) / baseline_cost) * 100) if baseline_cost > 0 else 0
    
    # Ensure they are not negative in case of anomalies
    tokens_saved_pct = max(0, tokens_saved_pct)
    time_saved_pct = max(0, time_saved_pct)
    cost_saved_pct = max(0, cost_saved_pct)

    return QueryResponse(
        query=query,
        baseline=BaselineResponse(
            answer=baseline_answer,
            tokens=baseline_tokens,
            responseTime=baseline_time,
            cost=round(baseline_cost, 6)
        ),
        vectorrag=VectorRAGResponse(
            answer=vr_answer,
            tokens=vr_tokens,
            responseTime=vr_time,
            cost=round(vr_cost, 6),
            retrievedChunks=vr_chunks
        ),
        graphrag=GraphRAGResponse(
            answer=gr_answer,
            tokens=gr_tokens,
            responseTime=gr_time,
            cost=round(gr_cost, 6),
            reasoningPath=gr_reasoning,
            graph=gr_graph
        ),
        comparison=Comparison(
            tokensSavedPct=tokens_saved_pct,
            timeSavedPct=time_saved_pct,
            costSavedPct=cost_saved_pct
        )
    )

class IndexRequest(BaseModel):
    file_name: str = "dev.txt"
    max_docs: int = 1000

@app.post("/api/rag/index")
async def rag_index(req: IndexRequest):
    try:
        return rag_pipeline.index_data(file_name=req.file_name, max_docs=req.max_docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RagQueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/api/rag/query")
async def rag_query(req: RagQueryRequest):
    try:
        return rag_pipeline.query(user_query=req.query, top_k=req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/status")
async def rag_status():
    return rag_pipeline.status()
