"""Resolve a destination name to a photo URL.

Lookup order:

    1. image_cache table          - no network call
    2. catalogue local file       - /images/<slug>.jpg shipped with the app
    3. provider chain             - Unsplash -> Pexels -> Openverse
    4. /images/hero.jpg           - final fallback, never fails

Steps 1 and 2 mean the seven seeded destinations never touch the network at
all; the providers only get hit for destinations a user types that we have no
local photo for (Kyoto, Barcelona, ...), which is exactly the gap the old
string-matching helper fell into.
"""
from __future__ import annotations 

import os 
import re 

from sqlalchemy .orm import Session 

from app .api_clients .images import (
from_openverse ,from_pexels ,from_unsplash ,trigger_download ,
)
from app .core .config import settings 
from app .models .destination import Destination 
from app .models .image_cache import ImageCache 

FALLBACK ="/images/hero.jpg"

_IMAGES_DIR =os .path .abspath (
os .path .join (os .path .dirname (__file__ ),"..","..","..","frontend","public","images")
)

def _norm (name :str )->str :
    return re .sub (r"[^a-z0-9 ]+","",(name or "").lower ()).strip ()

def _local_file_for (db :Session ,name :str )->str |None :
    """Exact/word-boundary match against the seeded catalogue.

    Deliberately NOT a substring test - `"goat island".includes("goa")` was
    the bug in the old frontend helper. We compare whole words instead.
    """
    n =_norm (name )
    if not n :
        return None 
    words =set (n .split ())
    for d in db .query (Destination ).all ():
        dn =_norm (d .name )
        if not dn :
            continue 

        if dn ==n or re .search (rf"(^| ){re .escape (dn )}( |$)",n ):
            return d .image_url 

        if " "not in dn and dn in words :
            return d .image_url 

    for d in db .query (Destination ).all ():
        dn =_norm (d .name )
        if " "in dn and any (w in words for w in dn .split ()if len (w )>3 ):
            return d .image_url 
    return None 

def _from_providers (query :str )->dict |None :

    for fn ,key in (
    (from_pexels ,settings .PEXELS_API_KEY ),
    (from_unsplash ,settings .UNSPLASH_ACCESS_KEY ),
    (from_openverse ,""),
    ):
        try :
            hit =fn (query ,key )
        except Exception :
            hit =None 
        if hit and hit .get ("url"):
            return hit 
    return None 

def resolve (db :Session ,name :str ,allow_remote :bool =True )->dict :
    """Return {url, credit, credit_url, license, provider, source}."""
    key =_norm (name )
    if not key :
        return {"url":FALLBACK ,"provider":"local","source":"fallback"}

    cached =db .get (ImageCache ,key )
    if cached :
        return {
        "url":cached .url ,
        "thumb_url":cached .thumb_url or cached .url ,
        "credit":cached .credit ,
        "credit_url":cached .credit_url ,
        "license":cached .license ,
        "license_url":cached .license_url ,
        "source_name":cached .source_name ,
        "source_url":cached .source_url ,
        "title":cached .title ,
        "provider":cached .provider ,
        "source":"cache",
        }

    local =_local_file_for (db ,name )
    if local :
        return {"url":local ,"thumb_url":local ,"credit":"","credit_url":"",
        "license":"","license_url":"","title":"",
        "source_name":"","source_url":"",
        "provider":"local","source":"catalogue"}

    if not allow_remote :
        return {"url":FALLBACK ,"provider":"local","source":"fallback"}

    hit =_from_providers (name )
    if not hit :
        return {"url":FALLBACK ,"provider":"local","source":"fallback"}

    db .add (ImageCache (query =key ,url =hit ["url"],thumb_url =hit .get ("thumb_url",""),
    credit =hit .get ("credit",""),credit_url =hit .get ("credit_url",""),
    license =hit .get ("license",""),license_url =hit .get ("license_url",""),
    source_name =hit .get ("source_name",""),
    source_url =hit .get ("source_url",""),
    title =hit .get ("title",""),provider =hit ["provider"]))
    db .commit ()

    if hit ["provider"]=="unsplash":
        trigger_download (hit .get ("download_location",""),settings .UNSPLASH_ACCESS_KEY )

    return {**hit ,"source":"provider"}
