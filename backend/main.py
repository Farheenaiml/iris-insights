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

# Load environment variables from .env file
load_dotenv()

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
    if file:
        file_bytes = await file.read()
        mime_type = file.content_type
        
        if mime_type.startswith("image/"):
            is_image = True
            base64_image = base64.b64encode(file_bytes).decode("utf-8")
        elif mime_type == "application/pdf":
            try:
                reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                extracted_text = ""
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

    # 2. GraphRAG Pipeline (Dummy for now, to be implemented next)
    # We use some dummy math based on baseline to make the comparison UI work temporarily
    grTokens = int(baseline_tokens * 0.4) if baseline_tokens > 0 else 720
    grTime = int(baseline_time * 0.35) if baseline_time > 0 else 1450
    grCost = baseline_cost * 0.4 if baseline_cost > 0 else 0.0162
    
    return QueryResponse(
        query=query,
        baseline=BaselineResponse(
            answer=baseline_answer,
            tokens=baseline_tokens,
            responseTime=baseline_time,
            cost=round(baseline_cost, 6)
        ),
        graphrag=GraphRAGResponse(
            answer=f"[GraphRAG Placeholder] This will eventually be the enhanced answer for: '{query}' using graph context. The graph approach is currently under construction.",
            tokens=grTokens,
            responseTime=grTime,
            cost=round(grCost, 6),
            reasoningPath=[
                "Step 1: Extract entities (Pending)",
                "Step 2: Query TigerGraph (Pending)",
                "Step 3: Generate enhanced response (Pending)"
            ],
            graph=GraphData(
                nodes=[
                    {"id": "Entity A", "group": 0},
                    {"id": "Entity B", "group": 1}
                ],
                edges=[
                    {"source": "Entity A", "target": "Entity B", "highlight": True}
                ]
            )
        ),
        comparison=Comparison(
            tokensSavedPct=round(((baseline_tokens - grTokens) / baseline_tokens) * 100) if baseline_tokens > 0 else 0,
            timeSavedPct=round(((baseline_time - grTime) / baseline_time) * 100) if baseline_time > 0 else 0,
            costSavedPct=round(((baseline_cost - grCost) / baseline_cost) * 100) if baseline_cost > 0 else 0
        )
    )
