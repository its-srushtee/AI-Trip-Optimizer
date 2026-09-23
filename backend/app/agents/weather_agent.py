"""Weather agent — pulls a forecast for the trip window."""
from typing import Any 

from app .agents .base import BaseAgent 
from app .api_clients .weather import get_weather_client 

class WeatherAgent (BaseAgent ):
    name ="weather"

    def run (self ,state :dict [str ,Any ])->dict [str ,Any ]:
        req =state ["request"]
        client =get_weather_client ()
        forecast =client .forecast (
        city =req .get ("destination",""),
        start =req .get ("start_date"),
        end =req .get ("end_date"),
        )
        state ["weather"]={
        "forecast":forecast ,
        "configured":client .is_configured (),
        "note":"Configure OPENWEATHERMAP_API_KEY for live weather.",
        }
        return state 
