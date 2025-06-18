from datetime import datetime

def init_loan_model(db):
    class Loan(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        amount = db.Column(db.Float, nullable=False)
        purpose = db.Column(db.String(200))
        interest_rate = db.Column(db.Float, default=10.0)
        issue_date = db.Column(db.DateTime, default=datetime.utcnow)
        due_date = db.Column(db.DateTime, nullable=False)
        status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Rejected, Repaid
        member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
        
        def __repr__(self):
            return f'<Loan {self.id}>'
    
    return Loan