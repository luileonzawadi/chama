from app import create_app, db
from app.models import User, Member, Activity
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

app = create_app()

@app.before_first_request
def create_tables():
    db.create_all()
    
    # Create default admin user if not exists
    if not User.query.filter_by(is_admin=True).first():
        admin_user = User(username='admin', password=generate_password_hash('admin'), is_admin=True)
        regular_user = User(username='user', password=generate_password_hash('user'), is_admin=False)
        db.session.add_all([admin_user, regular_user])
        db.session.commit()
        
        admin = User.query.filter_by(username='admin').first()
        user = User.query.filter_by(username='user').first()
        
        member1 = Member(name='John Doe', phone='0712345678', email='john@example.com', user_id=admin.id)
        member2 = Member(name='Jane Smith', phone='0723456789', email='jane@example.com', user_id=admin.id)
        member3 = Member(name='Michael Johnson', phone='0734567890', email='michael@example.com', user_id=user.id)
        
        activity1 = Activity(title='Monthly Meeting', description='Regular monthly chama meeting', 
                           date=datetime.utcnow() + timedelta(days=7), type='meeting', created_by=admin.id)
        activity2 = Activity(title='Investment Review', description='Review of investment portfolio', 
                           date=datetime.utcnow() + timedelta(days=14), type='review', created_by=admin.id)
        
        db.session.add_all([member1, member2, member3, activity1, activity2])
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_tables()
    app.run(debug=True)