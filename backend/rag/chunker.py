from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Chunks text into smaller pieces of `chunk_size` characters with `overlap` characters.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += (chunk_size - overlap)
    return chunks

def chunk_documents(documents: List[Dict], chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    """
    Chunks a list of documents and propagates metadata.
    """
    chunked_docs = []
    for doc in documents:
        chunks = chunk_text(doc["text"], chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            chunked_docs.append({
                "text": chunk,
                "metadata": {
                    **doc["metadata"],
                    "chunk_id": i
                }
            })
    return chunked_docs
