from datetime import datetime

def init_discussion_model(db):
    class Discussion(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        content = db.Column(db.Text, nullable=False)
        date = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        
        def __repr__(self):
            return f'<Discussion {self.id}>'
    
    return Discussion