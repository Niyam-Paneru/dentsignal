"""Check database for clinics and their Twilio numbers."""
from sqlmodel import select
from db import get_session, Client, create_db

create_db()

with get_session() as session:
    clients = list(session.exec(select(Client)))
    print(f"Found {len(clients)} clients:")
    for c in clients:
        print(f"  ID={c.id}, Name='{c.name}', TwilioNumber={c.twilio_number}, PhoneDisplay={c.phone_display}")
    
    if not clients:
        print("\nNo clients found! Need to seed the database.")
