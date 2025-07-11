from datetime import datetime
from app import db

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)
    target_value = db.Column(db.Float)
    target_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    completed = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_type': self.goal_type,
            'target_value': self.target_value,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'start_date': self.start_date.isoformat(),
            'is_active': self.is_active,
            'completed': self.completed
        }

class ProgressLog(db.Model):
    __tablename__ = 'progress_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    weight = db.Column(db.Float)
    workout = db.Column(db.String(200))
    calories = db.Column(db.Integer)
    notes = db.Column(db.Text)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'weight': self.weight,
            'workout': self.workout,
            'calories': self.calories,
            'notes': self.notes,
            'logged_at': self.logged_at.isoformat()
        }