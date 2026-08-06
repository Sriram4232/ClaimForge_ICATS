import os
import sys

# Ensure parent directory is in path so 'app' package resolves correctly
app_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if app_parent not in sys.path:
    sys.path.insert(0, app_parent)

from app.utils.icats_engine import (
    parse_date,
    levenshtein_similarity,
    clean_and_sort_tokens,
    verify_name_match,
    validate_verhoeff,
    verify_aadhaar_number,
    evaluate_claim
)
