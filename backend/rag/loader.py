import os
from typing import List, Dict

def load_pubmed_dataset(file_path: str, max_docs: int = None) -> List[Dict]:
    """
    Parses the PubMed RCT dataset.
    Returns a list of documents where each document contains the text and metadata.
    """
    documents = []
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return documents

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_pmid = None
    current_abstract = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_pmid and current_abstract:
                # Combine abstract sections
                text = " ".join([f"{sec}: {sent}" for sec, sent in current_abstract])
                documents.append({
                    "pmid": current_pmid,
                    "text": text,
                    "metadata": {"source": file_path, "pmid": current_pmid}
                })
                current_abstract = []
                if max_docs and len(documents) >= max_docs:
                    break
        elif line.startswith("###"):
            current_pmid = line.replace("###", "")
        else:
            parts = line.split('\t', 1)
            if len(parts) == 2:
                section, sentence = parts
                current_abstract.append((section, sentence))
    
    if current_pmid and current_abstract and (not max_docs or len(documents) < max_docs):
        text = " ".join([f"{sec}: {sent}" for sec, sent in current_abstract])
        documents.append({
            "pmid": current_pmid,
            "text": text,
            "metadata": {"source": file_path, "pmid": current_pmid}
        })

    return documents
