from datetime import datetime

def init_notification_model(db):
    class Notification(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(100), nullable=False)
        message = db.Column(db.Text, nullable=False)
        date = db.Column(db.DateTime, default=datetime.utcnow)
        is_read = db.Column(db.Boolean, default=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        
        def __repr__(self):
            return f'<Notification {self.id}>'
    
    return Notification