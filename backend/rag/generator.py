from groq import Groq
import os
import time
from typing import List, Dict, Tuple

class Generator:
    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=groq_api_key)
        self.model = "llama-3.1-8b-instant"
        
    def generate(self, query: str, context_chunks: List[Dict]) -> Tuple[str, Dict]:
        start_time = time.time()
        
        context_text = "\n\n".join([f"Chunk {i+1}:\n{c['text']}" for i, c in enumerate(context_chunks)])
        
        system_prompt = (
            "You are a helpful AI assistant. Answer the user's query using ONLY the provided context. "
            "If the answer is not contained in the context, say 'I cannot answer this based on the provided context.'\n\n"
            f"CONTEXT:\n{context_text}"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        answer = completion.choices[0].message.content
        tokens = {
            "prompt_tokens": completion.usage.prompt_tokens,
            "completion_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens
        }
        
        return answer, {
            "generation_time": generation_time,
            "tokens": tokens
        }
