from datetime import datetime

def init_contribution_model(db):
    class Contribution(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        amount = db.Column(db.Float, nullable=False)
        date = db.Column(db.DateTime, default=datetime.utcnow)
        member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
        
        def __repr__(self):
            return f'<Contribution {self.id}>'
    
    return Contribution