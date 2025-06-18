from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_models(app):
    db.init_app(app)
    
    from .user import init_user_model
    from .members import init_member_model
    
    User = init_user_model(db)
    Member = init_member_model(db)
    
    return db, User, Member