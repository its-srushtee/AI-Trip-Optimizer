"""Embedding utilities for RAG.

Two modes:
- Local: sentence-transformers (no API key) — enable by installing the
  `sentence-transformers` package and setting EMBEDDING_BACKEND=local.
- API: OpenAI embeddings — set OPENAI_API_KEY and EMBEDDING_BACKEND=openai.

When nothing is configured, embed_texts() returns None and the retriever
falls back to keyword search over the documents/ corpus.
"""
import os 
from functools import lru_cache 
from typing import Optional 

@lru_cache (maxsize =1 )
def get_embedder ():
    backend =os .getenv ("EMBEDDING_BACKEND","").lower ()
    if backend =="openai"and os .getenv ("OPENAI_API_KEY"):
        from openai import OpenAI 

        client =OpenAI ()
        return lambda texts :[
        r .embedding 
        for r in client .embeddings .create (model ="text-embedding-3-small",input =texts ).data 
        ]
    if backend =="local":
        from sentence_transformers import SentenceTransformer 

        model =SentenceTransformer ("all-MiniLM-L6-v2")

        def _embed (texts ):
            return model .encode (texts ,normalize_embeddings =True ).tolist ()

        return _embed 
    return None 

def embed_texts (texts :list [str ])->Optional [list ]:
    """Return dense vectors for `texts`, or None if no backend is configured."""
    embedder =get_embedder ()
    if embedder is None :
        return None 
    return embedder (texts )
