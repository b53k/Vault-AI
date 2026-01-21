import json
from typing import Optional
from pathlib import Path

ORCHESTRATION_PROMPTS_PATH = Path(__file__).parent.parent / "llm" / "prompts" / "orchestration.json"

with open(ORCHESTRATION_PROMPTS_PATH, "r") as file:
    orchestration_prompts = json.load(file)
    VALID_CATEGORIES = orchestration_prompts["categories"]

# Category mapping dictionary for common aliases
CATEGORY_ALIASES = {
    "cofee": "Coffee Shops",
    "coffe": "Coffee Shops",
    "coffee": "Coffee Shops",
    "coffee shop": "Coffee Shops",
    "coffee shops": "Coffee Shops",
    "starbucks": "Coffee Shops",
    "dunkin": "Coffee Shops",
    "dunkin'": "Coffee Shops",
    
    "food": "Food & Dining",
    "dining": "Food & Dining",
    "fast food": "Food & Dining",
    "restaurant": "Restaurants",
    "restaurants": "Restaurants",
    
    "grocery": "Groceries",
    "groceries": "Groceries",
    "supermarket": "Groceries",
    
    "gas": "Gas & Fuel",
    "fuel": "Gas & Fuel",
    "gas station": "Gas & Fuel",
    
    "bills": "Bills & Utilities",
    "utilities": "Bills & Utilities",
    "utility": "Bills & Utilities",
    
    "atm": "ATM Withdrawal",
    "withdrawal": "ATM Withdrawal",
    "withdrawl": "ATM Withdrawal",
    "cash": "ATM Withdrawal",
    
    "entertainment": "Entertainment",
    "netflix": "Entertainment",
    "spotify": "Entertainment",
    
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "pharmacy": "Healthcare",
    
    "shopping": "Shopping",
    "amazon": "Shopping",
    
    "transportation": "Transportation",
    "transport": "Transportation",
    "uber": "Transportation",
    "lyft": "Transportation",
    
    "travel": "Travel",
    "hotel": "Travel",
    
    "transfer": "Transfer",
    "zelle": "Transfer",
    "venmo": "Transfer",
    
    "salary": "Salary",
    "payroll": "Salary",
    "income": "Salary",
    
    "investment": "Investment",
    "investments": "Investment",
    
    "online services": "Online Services",
    "software": "Online Services",
    "subscription": "Online Services",
    "subscriptions": "Online Services",
    "cloud": "Online Services",
}

def _simple_similarity(s1: str, s2: str) -> float:
    """
        Calculate simple similarity between two strings. (0.01 -1.0) 
        based on character overlap and length similarity.
    """

    s1_lower = s1.lower()
    s2_lower = s2.lower()

    if s1_lower == s2_lower:
        return 1.0
    
    if (s1_lower in s2_lower) or (s2_lower in s1_lower):
        shorter = min(len(s1_lower), len(s2_lower))
        longer = max(len(s1_lower), len(s2_lower))
        return shorter / longer if longer > 0 else 0.0
    
    # Character overlap similarity
    chars1 = set(s1_lower.replace(" ", "").replace("&", ""))
    chars2 = set(s2_lower.replace(" ", "").replace("&", ""))

    if not chars1 or not chars2:
        return 0.0
    
    intersection = len(chars1 & chars2)
    union = len(chars1 | chars2)

    # Jaccard similarity
    jaccard = intersection / union if union > 0 else 0.0

    # Length similarity: penalizes if lengths are very different
    len_ratio = min(len(s1_lower), len(s2_lower)) / max(len(s1_lower), len(s2_lower)) if max(len(s1_lower), len(s2_lower)) > 0 else 0.0

    # weighted average of scores
    return (jaccard * 0.7) + (len_ratio * 0.3)


def normalize_category(category: Optional[str]) -> Optional[str]:
    """
    Normalize a category name to match exact database category names.
    
    Uses a three-tier approach:
    1. Direct match (case-insensitive)
    2. Alias mapping (common user terms)
    3. Simple similarity matching (no external libraries)
    
    Args:
        category: Category name from user query or LLM
        
    Returns:
        Normalized category name matching database, or None if no match found
    """

    if not category:
        return None
    
    category_clean = category.strip()

    if not category_clean:
        return None
    
    category_lower = category_clean.lower()

    # Direct match (case-insensitive)
    for valid_category in VALID_CATEGORIES:
        if valid_category.lower() == category_lower:
            return valid_category
    
    # Alias mapping
    if category_lower in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[category_lower]
    
    # Simple similarity matching
    best_match = None
    best_score = 0.6        # minimum threshold

    for valid_cat in VALID_CATEGORIES:
        score = _simple_similarity(category_clean, valid_cat)
        if score > best_score:
            best_match = valid_cat
            best_score = score

    return best_match



def validate_category(category: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validate and normalize a category.
    
    Returns:
        Tuple of (is_valid, normalized_category)
        If is_valid is False, normalized_category is None
    """
    if not category:
        return True, None  # None is valid (no filter)
    
    normalized = normalize_category(category)
    if normalized:
        return True, normalized
    
    return False, None



if __name__ == "__main__":
    print(validate_category("Coe"))
    print(validate_category("coffee shops"))
    print(validate_category("food"))
    print(validate_category("groceries"))
    print(validate_category("gas station"))
    print(validate_category("bills"))
    print(validate_category("atm"))
    print(validate_category("entertainment"))
    print(validate_category("healthcar"))
    print(validate_category("shopping"))