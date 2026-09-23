"""Hotel agent — suggests stays within budget via the hotels API client."""
from typing import Any 

from app .agents .base import BaseAgent 
from app .api_clients .hotels import get_hotels_client 

class HotelAgent (BaseAgent ):
    name ="hotels"

    def run (self ,state :dict [str ,Any ])->dict [str ,Any ]:
        req =state ["request"]
        client =get_hotels_client ()
        results =client .search_hotels (
        city =req .get ("destination",""),
        check_in =req .get ("start_date"),
        check_out =req .get ("end_date"),
        budget =req .get ("budget"),
        travelers =req .get ("travelers",1 ),
        )
        state ["hotels"]={
        "options":results or [],
        "configured":client .is_configured (),
        "note":"Configure AMADEUS_API_KEY/SECRET for real hotel search.",
        }
        return state 
