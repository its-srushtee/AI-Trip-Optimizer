"""Destination agent — researches what to see/do at the destination.

Uses the RAG retriever over the travel documents corpus. When no LLM / vector
store is configured it returns sensible placeholder highlights so the pipeline
still runs end-to-end.
"""
from typing import Any 

from app .agents .base import BaseAgent 
from app .rag .retriever import get_retriever 

class DestinationAgent (BaseAgent ):
    name ="destination"

    def run (self ,state :dict [str ,Any ])->dict [str ,Any ]:
        req =state ["request"]
        city =req .get ("destination","")

        retriever =get_retriever ()
        docs =retriever .retrieve (f"{city } things to do top attractions",top_k =3 )

        state ["destination"]={
        "name":city ,
        "highlights":[
        "Top-rated attractions and landmarks",
        "Local food and market experiences",
        "Hidden gems away from the crowds",
        ],
        "rag_context":[d ["content"][:300 ]for d in docs ],
        "source":"rag"if docs else "placeholder",
        }
        return state 
