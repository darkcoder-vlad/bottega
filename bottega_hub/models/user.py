from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from .base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, unique=True, nullable=True)
    
    # Loyalty program fields
    first_visit_date = Column(DateTime, nullable=True)
    visits_count = Column(Integer, default=0)
    cycle_start_date = Column(DateTime, nullable=True)
    reward_available = Column(Boolean, default=False)
    reward_generated = Column(Boolean, default=False)
    reward_used = Column(Boolean, default=False)
    current_cycle = Column(Integer, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_visit_date = Column(DateTime, nullable=True)
    last_notification_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, phone={self.phone})>"

    def can_check_in_today(self) -> bool:
        """Check if user can check in today (max 1 visit per day)"""
        if not self.last_visit_date:
            return True
        return self.last_visit_date.date() != datetime.utcnow().date()

    def get_days_remaining(self) -> int:
        """Get remaining days in current cycle"""
        if not self.cycle_start_date:
            return 60
        from datetime import timedelta
        cycle_end = self.cycle_start_date + timedelta(days=60)
        remaining = (cycle_end - datetime.utcnow()).days
        return max(0, remaining)

    def is_cycle_expired(self) -> bool:
        """Check if current cycle has expired"""
        if not self.cycle_start_date:
            return False
        from datetime import timedelta
        cycle_end = self.cycle_start_date + timedelta(days=60)
        return datetime.utcnow() > cycle_end

    def reset_cycle(self):
        """Reset cycle after reward is used"""
        self.visits_count = 0
        self.cycle_start_date = None
        self.first_visit_date = None
        self.reward_available = False
        self.reward_generated = False
        self.reward_used = False
        self.current_cycle += 1
        self.last_visit_date = None
