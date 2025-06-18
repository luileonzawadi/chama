from main import create_app
from models import db, Member
from datetime import datetime

app = create_app()

with app.app_context():
    # Add sample members
    members = [
        Member(
            name='John Doe',
            phone='0712345678',
            email='john@example.com',
            join_date=datetime.now(),
            status='Active'
        ),
        Member(
            name='Jane Smith',
            phone='0723456789',
            email='jane@example.com',
            join_date=datetime.now(),
            status='Active'
        ),
        Member(
            name='Michael Johnson',
            phone='0734567890',
            email='michael@example.com',
            join_date=datetime.now(),
            status='Inactive'
        )
    ]
    
    # Add members to database
    db.session.add_all(members)
    db.session.commit()
    
    print(f"Added {len(members)} sample members to the database!")