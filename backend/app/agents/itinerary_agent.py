"""Itinerary agent — assembles the final day-by-day plan."""
from datetime import date ,timedelta 
from typing import Any 

from app .agents .base import BaseAgent 

THEMES =["Arrival","Explore","Discover","Day trip","Relax","Highlights","Farewell"]

class ItineraryAgent (BaseAgent ):
    name ="itinerary"

    def run (self ,state :dict [str ,Any ])->dict [str ,Any ]:
        req =state ["request"]
        start =date .fromisoformat (req ["start_date"])
        end =date .fromisoformat (req ["end_date"])
        nights =(end -start ).days 
        total_days =nights +1 
        budget =int (req .get ("budget",1000 ))

        days =[]
        for i in range (total_days ):
            d =start +timedelta (days =i )
            if i ==0 :
                morning ="Arrive, check in and settle in"
            elif i ==total_days -1 :
                morning ="Pack up and head to the airport"
            else :
                morning ="Morning sightseeing at a top-rated local spot"
            days .append (
            {
            "day":i +1 ,
            "date":d .isoformat (),
            "theme":THEMES [min (i ,len (THEMES )-1 )],
            "morning":morning ,
            "afternoon":"Lunch at a well-reviewed place nearby",
            "evening":"Dinner and a relaxed evening walk",
            "stay":"Accommodation to be finalized",
            "estimate_usd":round (budget /total_days ),
            }
            )

        breakdown =state .get ("costs",{}).get ("breakdown",{})
        focus =f", focused on {', '.join (req .get ('interests',[]))}"if req .get ("interests")else ""
        state ["itinerary"]={
        "destination":req ["destination"],
        "dates":{"start":req ["start_date"],"end":req ["end_date"],"nights":nights },
        "travelers":req .get ("travelers",1 ),
        "interests":req .get ("interests",[]),
        "budget":budget ,
        "budget_breakdown":breakdown ,
        "summary":(
        f"A {nights }-night trip to {req ['destination']} for "
        f"{req .get ('travelers',1 )} traveler(s) on a ${budget :,} budget{focus }. "
        "(Placeholder — plug in LLM/RAG agents for the real plan.)"
        ),
        "days":days ,
        }
        return state 
