from flask_login import UserMixin

def init_user_model(db):
    from datetime import datetime
    
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(200), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        last_login = db.Column(db.DateTime)
        is_active = db.Column(db.Boolean, default=True)
        
        def __repr__(self):
            return f'<User {self.username}>'
        
        def update_last_login(self):
            """Update the last login timestamp"""
            self.last_login = datetime.utcnow()
    
    return User