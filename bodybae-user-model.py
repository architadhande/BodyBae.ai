from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Float, nullable=False)  # in cm
    weight = db.Column(db.Float, nullable=False)  # in lbs
    sex = db.Column(db.String(10), nullable=False)
    activity_level = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goals = db.relationship('Goal', backref='user', lazy=True)
    progress_logs = db.relationship('ProgressLog', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'height': self.height,
            'weight': self.weight,
            'sex': self.sex,
            'activity_level': self.activity_level,
            'created_at': self.created_at.isoformat()
        }
    
    def calculate_bmi(self):
        # Convert height from cm to meters
        height_m = self.height / 100
        # Convert weight from lbs to kg
        weight_kg = self.weight * 0.453592
        return round(weight_kg / (height_m ** 2), 1)