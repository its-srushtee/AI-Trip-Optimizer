"""Cost agent — validates budget/time feasibility and produces a breakdown."""
from datetime import date 
from typing import Any 

from app .agents .base import BaseAgent 

class CostAgent (BaseAgent ):
    name ="cost"

    def run (self ,state :dict [str ,Any ])->dict [str ,Any ]:
        req =state ["request"]
        budget =int (req .get ("budget",1000 ))
        try :
            nights =(date .fromisoformat (req ["end_date"])-date .fromisoformat (req ["start_date"])).days 
        except (KeyError ,TypeError ,ValueError ):
            nights =0 
        nights =max (nights ,1 )

        breakdown ={
        "flights":round (budget *0.30 ),
        "stay":round (budget *0.35 ),
        "food":round (budget *0.15 ),
        "activities":round (budget *0.20 ),
        "total":budget ,
        }
        state ["costs"]={
        "breakdown":breakdown ,
        "per_day":round (budget /(nights +1 )),
        "feasible":breakdown ["total"]<=budget ,
        "note":"Estimates — replace with live pricing in cost_agent.",
        }
        return state 
