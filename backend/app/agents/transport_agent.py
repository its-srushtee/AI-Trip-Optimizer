"""Transport agent — travel guidelines + getting-around notes.

Currently produces static guidance. TODO: wire an external transport /
flights API (e.g. Amadeus Flight Offers, Skyscanner) for live prices.
"""
from typing import Any 

from app .agents .base import BaseAgent 

class TransportAgent (BaseAgent ):
    name ="transport"

    def run (self ,state :dict [str ,Any ])->dict [str ,Any ]:
        req =state ["request"]
        city =req .get ("destination","")
        state ["transport"]={
        "guidelines":[
        f"Check entry requirements and travel advisories for {city }.",
        "Prefer mid-week departures — often cheaper.",
        "Use local transit passes for getting around.",
        ],
        "note":"Wire a flights/transport API for live options.",
        }
        return state 
