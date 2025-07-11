from datetime import datetime, timedelta
from models.user import User
from models.goal import Goal, ProgressLog

class ProgressTracker:
    def __init__(self, db):
        self.db = db
    
    def log_progress(self, user_id, weight=None, workout=None, calories=None):
        """Log user progress"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Create progress log entry
            progress_log = ProgressLog(
                user_id=user_id,
                weight=weight,
                workout=workout,
                calories=calories,
                logged_at=datetime.utcnow()
            )
            
            # Update user's current weight if provided
            if weight:
                user.weight = weight
            
            self.db.session.add(progress_log)
            self.db.session.commit()
            
            # Check progress towards goals
            progress_update = self.check_goal_progress(user)
            
            return {
                'status': 'success',
                'message': 'Progress logged successfully!',
                'progress_update': progress_update
            }
            
        except Exception as e:
            self.db.session.rollback()
            return {'error': str(e)}
    
    def check_goal_progress(self, user):
        """Check user's progress towards their active goals"""
        active_goals = Goal.query.filter_by(
            user_id=user.id,
            is_active=True,
            completed=False
        ).all()
        
        progress_updates = []
        
        for goal in active_goals:
            if goal.goal_type == 'lose_weight':
                progress = self.calculate_weight_loss_progress(user, goal)
            elif goal.goal_type == 'gain_weight':
                progress = self.calculate_weight_gain_progress(user, goal)
            else:
                progress = self.calculate_general_progress(user, goal)
            
            progress_updates.append(progress)
            
            # Check if goal is completed
            if progress['percentage'] >= 100:
                goal.completed = True
                self.db.session.commit()
        
        return progress_updates
    
    def calculate_weight_loss_progress(self, user, goal):
        """Calculate progress for weight loss goal"""
        # Get user's starting weight from first log or profile
        first_log = ProgressLog.query.filter_by(
            user_id=user.id
        ).order_by(ProgressLog.logged_at).first()
        
        starting_weight = first_log.weight if first_log and first_log.weight else user.weight
        current_weight = user.weight
        target_weight = goal.target_value
        
        total_to_lose = starting_weight - target_weight
        lost_so_far = starting_weight - current_weight
        
        percentage = (lost_so_far / total_to_lose * 100) if total_to_lose > 0 else 0
        
        return {
            'goal_type': 'Weight Loss',
            'current': current_weight,
            'target': target_weight,
            'percentage': round(percentage, 1),
            'message': f"You've lost {lost_so_far:.1f} lbs! {total_to_lose - lost_so_far:.1f} lbs to go!"
        }
    
    def calculate_weight_gain_progress(self, user, goal):
        """Calculate progress for weight gain goal"""
        first_log = ProgressLog.query.filter_by(
            user_id=user.id
        ).order_by(ProgressLog.logged_at).first()
        
        starting_weight = first_log.weight if first_log and first_log.weight else user.weight
        current_weight = user.weight
        target_weight = goal.target_value
        
        total_to_gain = target_weight - starting_weight
        gained_so_far = current_weight - starting_weight
        
        percentage = (gained_so_far / total_to_gain * 100) if total_to_gain > 0 else 0
        
        return {
            'goal_type': 'Weight Gain',
            'current': current_weight,
            'target': target_weight,
            'percentage': round(percentage, 1),
            'message': f"You've gained {gained_so_far:.1f} lbs! {total_to_gain - gained_so_far:.1f} lbs to go!"
        }
    
    def calculate_general_progress(self, user, goal):
        """Calculate progress for other goal types based on time elapsed"""
        days_elapsed = (datetime.utcnow() - goal.start_date).days
        total_days = (goal.target_date - goal.start_date).days
        
        percentage = (days_elapsed / total_days * 100) if total_days > 0 else 0
        
        return {
            'goal_type': goal.goal_type.replace('_', ' ').title(),
            'days_elapsed': days_elapsed,
            'total_days': total_days,
            'percentage': round(percentage, 1),
            'message': f"You're {percentage:.1f}% through your journey! Keep going!"
        }
    
    def get_progress_summary(self, user_id, days=30):
        """Get progress summary for the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        logs = ProgressLog.query.filter(
            ProgressLog.user_id == user_id,
            ProgressLog.logged_at >= cutoff_date
        ).order_by(ProgressLog.logged_at.desc()).all()
        
        return {
            'total_logs': len(logs),
            'logs': [log.to_dict() for log in logs],
            'workout_count': sum(1 for log in logs if log.workout),
            'average_calories': sum(log.calories or 0 for log in logs) / len(logs) if logs else 0
        }