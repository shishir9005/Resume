import logging
import sys
import os
from typing import Callable, Dict, Optional, Tuple, TypeVar

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger('ats_resume_scorer')
logger.setLevel(logging.INFO)

#everything INFO and up goes to logs/ats_scorer.log
file_handler = logging.FileHandler(os.path.join(LOG_DIR, "ats_scorer.log"))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))

#only warnings and errors reach the terminal
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

class ATSBaseError(Exception):
    """message is for the logs, user_message is safe to show in the UI."""
    def __init__(self, message: str, user_message: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.user_message = user_message or 'An error occurred. Please try again.'

class FileUploadError(ATSBaseError):
    pass

class FileParsingError(ATSBaseError):
    pass

class TextExtractionError(ATSBaseError):
    pass

def log_error(error: Exception, context: Optional[str] = None) -> None:
    logger.error(f"Error in {context or 'unknown'}: {error}")

def log_warning(message: str, context: Optional[str] = None) -> None:
    logger.warning(f"{context}: {message}" if context else message)

def log_info(message: str, context: Optional[str] = None) -> None:
    logger.info(f"{context}: {message}" if context else message)

T = TypeVar('T')

def with_fallback(
    primary_func: Callable[..., T],
    fallback_func: Callable[..., T],
    *args,
    log_fallback: bool = True,
    **kwargs
) -> Tuple[T, bool]:
    #returns (result, used_fallback) so the caller can log which path ran
    try:
        return primary_func(*args, **kwargs), False
    except Exception as primary_error:
        if log_fallback:
            log_warning(f"Primary method failed, trying fallback: {primary_error}")
        try:
            return fallback_func(*args, **kwargs), True
        except Exception as fallback_error:
            log_error(fallback_error, context="fallback")
            raise

def get_default_grammar_results() -> Dict:
    return {
        'total_errors':         0,
        'critical_errors':      [],
        'moderate_errors':      [],
        'minor_errors':         [],
        'grammar_score':        100,
        'penalty_applied':      0,
        'error_free_percentage': 100,
        '_component_status':    'unavailable',
        '_note': 'Grammar checking unavailable.'
    }

def get_default_location_results() -> Dict:
    return {
        'location_found':     False,
        'detected_locations': [],
        'privacy_risk':       'unknown',
        'recommendations':    ['Location detection unavailable.'],
        'penalty_applied':    0,
        '_component_status':  'unavailable',
        '_note': 'Location detection unavailable.'
    }

def get_default_skill_validation_results() -> Dict:
    return {
        'validated_skills':     [],
        'unvalidated_skills':   [],
        'validation_percentage': 0.0,
        'skill_project_mapping': {},
        'validation_score':     0.0,
        '_component_status':    'unavailable',
        '_note': 'Skill validation unavailable.'
    }
