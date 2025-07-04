from datetime import datetime

def init_message_model(db):
    class Message(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'), nullable=False)
        
        # Relationships
        user = db.relationship('User', backref='messages')
        
        def __repr__(self):
            return f'<Message {self.id}>'
    
    return Message