from flask_login import UserMixin

def init_user_model(db):
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        password = db.Column(db.String(200), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        
        def __repr__(self):
            return f'<User {self.username}>'
    
    return User