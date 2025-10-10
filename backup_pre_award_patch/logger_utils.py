import logging
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
import json

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class PIIMaskedFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        
    def mask_name_fields(self, text):
        def replace_double_quote(match):
            key = match.group(1)
            return f'"{key}": "[REDACTED]"'
        
        def replace_single_quote(match):
            key = match.group(1)
            return f"'{key}': '[REDACTED]'"
        
        text = re.sub(r'"(name|firstName|lastName)"\s*:\s*"(?:[^"\\]|\\.)*"', replace_double_quote, text)
        text = re.sub(r"'(name|firstName|lastName)'\s*:\s*'(?:[^'\\]|\\.)*'", replace_single_quote, text)
        
        return text
        
    def format(self, record):
        original = super().format(record)
        masked = self.email_pattern.sub(lambda m: self.mask_email(m.group()), original)
        masked = self.phone_pattern.sub('***-***-****', masked)
        masked = self.mask_name_fields(masked)
        return masked
    
    def mask_email(self, email):
        parts = email.split('@')
        if len(parts) == 2:
            username = parts[0]
            domain = parts[1]
            if len(username) > 2:
                masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
            else:
                masked_username = '*' * len(username)
            return f"{masked_username}@{domain}"
        return email

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(PIIMaskedFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    logger.addHandler(handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(PIIMaskedFormatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)
    
    return logger

def purge_old_logs():
    cutoff_date = datetime.now() - timedelta(days=7)
    for log_file in LOG_DIR.glob("*.log"):
        file_date_str = log_file.stem.split('_')[-1]
        try:
            file_date = datetime.strptime(file_date_str, '%Y%m%d')
            if file_date < cutoff_date:
                log_file.unlink()
                print(f"Purged old log: {log_file}")
        except (ValueError, IndexError):
            pass

logger = setup_logger('welfor_health')
