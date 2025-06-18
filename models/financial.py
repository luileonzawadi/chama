from app import db
from datetime import datetime

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    
    def __repr__(self):
        return f'<Contribution {self.id}>'

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=10.0)  # percentage
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Repaid
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    
    def __repr__(self):
        return f'<Loan {self.id}>'