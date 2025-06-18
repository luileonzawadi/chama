from datetime import datetime

def init_member_model(db):
    class Member(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        phone = db.Column(db.String(20), nullable=False, unique=True)
        email = db.Column(db.String(100))
        join_date = db.Column(db.DateTime, default=datetime.utcnow)
        status = db.Column(db.String(20), default='Active')
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        
        def __repr__(self):
            return f'<Member {self.name}>'
    
    return Member