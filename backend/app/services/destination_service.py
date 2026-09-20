"""Destination catalogue: seed + list."""
from sqlalchemy .orm import Session 

from app .models .destination import Destination 

DESTINATIONS =[
{
"slug":"bali","name":"Bali","country":"Indonesia",
"image_url":"/images/bali.jpg",
"tags":["beaches","nature","culture","food"],
"styles":["Budget","Comfort","Luxury"],
"paces":["Relaxed","Balanced"],
"price_label":"$1,100",
"blurb":"Island temples, rice terraces and golden beaches.",
},
{
"slug":"maldives","name":"Maldives","country":"Indian Ocean",
"image_url":"/images/maldives.jpg",
"tags":["beaches"],
"styles":["Comfort","Luxury"],
"paces":["Relaxed"],
"price_label":"$2,400",
"blurb":"Overwater villas and endless turquoise lagoons.",
},
{
"slug":"thailand","name":"Thailand","country":"Southeast Asia",
"image_url":"/images/thailand.jpg",
"tags":["food","adventure","beaches","nightlife","culture"],
"styles":["Budget","Comfort"],
"paces":["Balanced","Packed"],
"price_label":"$900",
"blurb":"Street food, temples and island hopping.",
},
{
"slug":"paris","name":"Paris","country":"France",
"image_url":"/images/paris.jpg",
"tags":["culture","food","shopping"],
"styles":["Comfort","Luxury"],
"paces":["Balanced","Packed"],
"price_label":"$1,600",
"blurb":"Museums, cafés and iconic landmarks.",
},
{
"slug":"tokyo","name":"Tokyo","country":"Japan",
"image_url":"/images/tokyo.jpg",
"tags":["food","shopping","nightlife","culture"],
"styles":["Budget","Comfort","Luxury"],
"paces":["Balanced","Packed"],
"price_label":"$1,800",
"blurb":"Neon nights, sushi and endless discovery.",
},
{
"slug":"alps","name":"Swiss Alps","country":"Switzerland",
"image_url":"/images/alps.jpg",
"tags":["adventure","nature"],
"styles":["Comfort","Luxury"],
"paces":["Relaxed","Balanced"],
"price_label":"$2,000",
"blurb":"Alpine peaks, trails and cozy villages.",
},
{
"slug":"goa","name":"Goa","country":"India",
"image_url":"/images/goa.jpg",
"tags":["beaches","nightlife","food"],
"styles":["Budget","Comfort"],
"paces":["Relaxed","Balanced"],
"price_label":"$500",
"blurb":"Beach shacks, sunsets and laid-back vibes.",
},
]

def seed_destinations (db :Session )->int :
    """Insert the catalogue if the table is empty. Returns rows created."""
    if db .query (Destination ).count ()>0 :
        return 0 
    created =0 
    for d in DESTINATIONS :
        db .add (Destination (**d ))
        created +=1 
    db .commit ()
    return created 

def list_destinations (db :Session )->list [dict ]:
    rows =db .query (Destination ).order_by (Destination .name ).all ()
    return [
    {
    "id":d .slug ,
    "name":d .name ,
    "country":d .country ,
    "image_url":d .image_url ,
    "tags":d .tags ,
    "styles":d .styles ,
    "paces":d .paces ,
    "price":d .price_label ,
    "blurb":d .blurb ,
    }
    for d in rows 
    ]
