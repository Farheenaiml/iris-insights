import os
import json
from typing import List, Dict, Any, Tuple
from groq import Groq

class MedicalExtractor:
    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=groq_api_key) if groq_api_key else None
        self.model = "llama-3.1-8b-instant"

    def extract_entities_from_query(self, query: str) -> List[str]:
        """
        Uses LLM to identify the main medical/treatment entities, drugs, or concepts
        present in the user's query to look up in the Knowledge Graph.
        """
        if not self.client:
            # Simple fallback: split by words
            return [w.strip(",.?()\"'") for w in query.split() if len(w) > 4]

        prompt = (
            "Identify the key entities, subjects, topics, terms, or concepts in the user's query.\n"
            "Return them as a simple comma-separated list of strings. Do not include any explanation or extra text.\n\n"
            f"Query: {query}\n"
            "Entities:"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=100
            )
            response = completion.choices[0].message.content.strip()
            # Parse comma-separated list
            entities = [item.strip() for item in response.split(",") if item.strip()]
            return entities
        except Exception as e:
            print(f"Error extracting entities from query: {e}")
            # Fallback
            return [w.strip(",.?()\"'") for w in query.split() if len(w) > 4]

    def extract_triples_from_text(self, text: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Uses LLM to extract entities and relations (triples) from a research abstract chunk.
        """
        if not self.client:
            return [], []

        prompt = (
            "You are an advanced knowledge graph builder. "
            "Extract key entities and their relationships from the text below.\n"
            "Represent the relationships clearly as (source, relation, target) triples.\n\n"
            "Rules:\n"
            "1. Entities should be concise names (e.g. 'Dermabond', 'Apex Corporation', 'Q1 2026 revenue', 'Mean closure time').\n"
            "2. Relations should be lowercase verbs/prepositions (e.g. 'compared_to', 'increased_by', 'used_for', 'reduces', 'costs').\n"
            "3. Format your response strictly as a JSON object with keys 'entities' and 'relations'. "
            "Do not include markdown tags like ```json or any other text before/after.\n\n"
            "Format example:\n"
            "{\n"
            "  \"entities\": [\n"
            "    {\"name\": \"Dermabond\", \"type\": \"Treatment\"},\n"
            "    {\"name\": \"Subcuticular sutures\", \"type\": \"Treatment\"}\n"
            "  ],\n"
            "  \"relations\": [\n"
            "    {\"source\": \"Dermabond\", \"target\": \"Subcuticular sutures\", \"type\": \"compared_to\"}\n"
            "  ]\n"
            "}\n\n"
            f"Text:\n{text}\n\n"
            "JSON Output:"
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024
            )
            raw_content = completion.choices[0].message.content.strip()
            
            # Clean JSON markdown wrapper if present
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_content = "\n".join(lines).strip()
                
            data = json.loads(raw_content)
            return data.get("entities", []), data.get("relations", [])
        except Exception as e:
            print(f"Error extracting triples: {e}")
            return [], []
