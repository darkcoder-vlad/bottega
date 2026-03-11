import re
from config import MIN_CHECK_AMOUNT


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Russian phone number
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    elif len(digits) == 11 and digits.startswith('7'):
        pass
    else:
        return False
    
    return True


def normalize_phone(phone: str) -> str:
    """Normalize phone number to +7 format"""
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    
    return f"+{digits}"


def validate_amount(amount_str: str) -> tuple:
    """Validate check amount. Returns (is_valid, amount_float)"""
    try:
        # Replace comma with dot for decimal
        amount_str = amount_str.replace(',', '.')
        amount = float(amount_str)
        
        if amount >= MIN_CHECK_AMOUNT:
            return True, amount
        return False, 0
    except (ValueError, TypeError):
        return False, 0


def validate_shift_code(code: str) -> bool:
    """Validate shift code format (4 digits)"""
    return bool(re.match(r'^\d{4}$', code))
