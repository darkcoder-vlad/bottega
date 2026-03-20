from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional, List

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from models.visit import Visit
from models.reward import Reward
from models.shift_code import ShiftCode


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        return self.db.query(User).filter(User.phone == phone).first()

    def create(self, telegram_id: str, username: str = None, 
               first_name: str = None, last_name: str = None) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            registered_at=datetime.utcnow()
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_phone(self, user: User, phone: str) -> User:
        user.phone = phone
        self.db.commit()
        self.db.refresh(user)
        return user

    def add_visit(self, user: User, amount: float) -> User:
        user.visits_count += 1
        user.last_visit_date = datetime.utcnow()
        
        if not user.first_visit_date:
            user.first_visit_date = datetime.utcnow()
        if not user.cycle_start_date:
            user.cycle_start_date = datetime.utcnow()
        
        # Check if 9 visits reached
        if user.visits_count == 9 and not user.reward_available:
            user.reward_available = True
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_all_active_users(self) -> List[User]:
        return self.db.query(User).filter(User.is_active == True).all()

    def get_users_for_notification(self, inactive_days: int = 7) -> List[User]:
        """Get users who haven't visited for specified days and have active cycle"""
        cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)
        return self.db.query(User).filter(
            User.is_active == True,
            User.last_visit_date != None,
            User.last_visit_date < cutoff_date,
            User.cycle_start_date != None,
            User.visits_count < 9
        ).all()

    def reset_user_cycle(self, user: User) -> User:
        user.reset_cycle()
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_stats(self) -> dict:
        total_users = self.db.query(func.count(User.id)).scalar()
        active_users = self.db.query(func.count(User.id)).filter(
            User.is_active == True,
            User.cycle_start_date != None
        ).scalar()
        rewards_issued = self.db.query(func.count(User.id)).filter(
            User.reward_available == True
        ).scalar()
        completed_cycles = self.db.query(func.count(User.id)).filter(
            User.current_cycle > 1
        ).scalar()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'rewards_issued': rewards_issued,
            'completed_cycles': completed_cycles
        }


class VisitRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, check_amount: float, status: str = 'pending', shift_code: str = None) -> Visit:
        visit = Visit(
            user_id=user_id,
            amount=check_amount,
            shift_code=shift_code or 'ADMIN',
            visit_date=datetime.utcnow(),
            is_valid=(status == 'approved')
        )
        self.db.add(visit)
        self.db.commit()
        self.db.refresh(visit)
        return visit

    def get_today_visits(self, user_id: int) -> List[Visit]:
        today = datetime.utcnow().date()
        return self.db.query(Visit).filter(
            Visit.user_id == user_id,
            func.date(Visit.visit_date) == today
        ).all()

    def get_user_visits(self, user_id: int) -> List[Visit]:
        return self.db.query(Visit).filter(
            Visit.user_id == user_id
        ).order_by(Visit.visit_date.desc()).all()


class RewardRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, reward_code: str, amount: float = None) -> Reward:
        reward = Reward(
            user_id=user_id,
            reward_code=reward_code,
            amount=amount
        )
        self.db.add(reward)
        self.db.commit()
        self.db.refresh(reward)
        return reward

    def get_by_code(self, reward_code: str) -> Optional[Reward]:
        return self.db.query(Reward).filter(Reward.reward_code == reward_code).first()

    def get_user_reward(self, user_id: int) -> Optional[Reward]:
        return self.db.query(Reward).filter(Reward.user_id == user_id).first()

    def mark_as_used(self, reward: Reward) -> Reward:
        reward.is_used = True
        reward.used_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(reward)
        return reward


class ShiftCodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_code(self) -> Optional[ShiftCode]:
        return self.db.query(ShiftCode).filter(
            ShiftCode.is_active == True
        ).order_by(ShiftCode.created_at.desc()).first()

    def set_code(self, code: str) -> ShiftCode:
        # Deactivate old codes
        self.db.query(ShiftCode).update({ShiftCode.is_active: False})
        
        # Create new code
        shift_code = ShiftCode(code=code, is_active=True)
        self.db.add(shift_code)
        self.db.commit()
        self.db.refresh(shift_code)
        return shift_code

    def validate_code(self, code: str) -> bool:
        shift_code = self.db.query(ShiftCode).filter(
            ShiftCode.code == code,
            ShiftCode.is_active == True
        ).first()
        return shift_code is not None


class ReceiptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, receipt_id: str, user_id: int, telegram_id: str, 
               amount: float, file_id: str, caption: str = None) -> 'Receipt':
        from models.receipt import Receipt
        receipt = Receipt(
            receipt_id=receipt_id,
            user_id=user_id,
            telegram_id=telegram_id,
            amount=amount,
            file_id=file_id,
            caption=caption
        )
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def get_by_receipt_id(self, receipt_id: str) -> 'Receipt':
        from models.receipt import Receipt
        return self.db.query(Receipt).filter(
            Receipt.receipt_id == receipt_id,
            Receipt.is_confirmed == False,
            Receipt.is_rejected == False
        ).first()

    def confirm(self, receipt: 'Receipt', admin_id: str) -> 'Receipt':
        from datetime import datetime
        receipt.is_confirmed = True
        receipt.confirmed_at = datetime.utcnow()
        receipt.confirmed_by = admin_id
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def reject(self, receipt: 'Receipt') -> 'Receipt':
        receipt.is_rejected = True
        self.db.commit()
        self.db.refresh(receipt)
        return receipt

    def get_user_receipts(self, user_id: int) -> list:
        from models.receipt import Receipt
        return self.db.query(Receipt).filter(
            Receipt.user_id == user_id
        ).order_by(Receipt.created_at.desc()).all()


class ConsentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_telegram_id(self, telegram_id: str) -> 'Consent':
        from models.consent import Consent
        return self.db.query(Consent).filter(Consent.telegram_id == telegram_id).first()

    def create(self, telegram_id: str, user_id: int = None) -> 'Consent':
        from models.consent import Consent
        consent = Consent(
            telegram_id=telegram_id,
            user_id=user_id
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        return consent

    def accept(self, consent: 'Consent') -> 'Consent':
        from datetime import datetime
        consent.is_accepted = True
        consent.accepted_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(consent)
        return consent

    def has_accepted(self, telegram_id: str) -> bool:
        consent = self.get_by_telegram_id(telegram_id)
        if not consent:
            return False
        return consent.is_accepted
