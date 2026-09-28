"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-14

"""
from typing import Sequence ,Union 

from alembic import op 
import sqlalchemy as sa 

revision :str ="0001"
down_revision :Union [str ,None ]=None 
branch_labels :Union [str ,Sequence [str ],None ]=None 
depends_on :Union [str ,Sequence [str ],None ]=None 

def upgrade ()->None :
    op .create_table (
    "users",
    sa .Column ("id",sa .Integer (),primary_key =True ),
    sa .Column ("name",sa .String (length =120 ),nullable =False ),
    sa .Column ("email",sa .String (length =255 ),nullable =False ),
    sa .Column ("hashed_password",sa .String (length =255 ),nullable =False ),
    sa .Column ("preferences",sa .JSON (),nullable =False ,server_default ="{}"),
    sa .Column ("created_at",sa .DateTime (timezone =True ),server_default =sa .func .now (),nullable =False ),
    )
    op .create_index ("ix_users_email","users",["email"],unique =True )

    op .create_table (
    "trips",
    sa .Column ("id",sa .Integer (),primary_key =True ),
    sa .Column ("user_id",sa .Integer (),sa .ForeignKey ("users.id",ondelete ="CASCADE"),nullable =False ),
    sa .Column ("destination",sa .String (length =120 ),nullable =False ),
    sa .Column ("start_date",sa .Date (),nullable =False ),
    sa .Column ("end_date",sa .Date (),nullable =False ),
    sa .Column ("budget",sa .Integer (),nullable =False ,server_default ="1000"),
    sa .Column ("travelers",sa .Integer (),nullable =False ,server_default ="1"),
    sa .Column ("interests",sa .JSON (),nullable =False ,server_default ="[]"),
    sa .Column ("status",sa .String (length =40 ),nullable =False ,server_default ="Planning"),
    sa .Column ("created_at",sa .DateTime (timezone =True ),server_default =sa .func .now (),nullable =False ),
    )
    op .create_index ("ix_trips_user_id","trips",["user_id"])

    op .create_table (
    "destinations",
    sa .Column ("id",sa .Integer (),primary_key =True ),
    sa .Column ("slug",sa .String (length =80 ),nullable =False ),
    sa .Column ("name",sa .String (length =120 ),nullable =False ),
    sa .Column ("country",sa .String (length =120 ),nullable =False ),
    sa .Column ("image_url",sa .Text (),nullable =False ),
    sa .Column ("tags",sa .JSON (),nullable =False ,server_default ="[]"),
    sa .Column ("styles",sa .JSON (),nullable =False ,server_default ="[]"),
    sa .Column ("paces",sa .JSON (),nullable =False ,server_default ="[]"),
    sa .Column ("price_label",sa .String (length =40 ),nullable =False ),
    sa .Column ("blurb",sa .Text (),nullable =False ),
    )
    op .create_index ("ix_destinations_slug","destinations",["slug"],unique =True )

def downgrade ()->None :
    op .drop_table ("destinations")
    op .drop_table ("trips")
    op .drop_table ("users")
