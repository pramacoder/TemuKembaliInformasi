import re

def clean_text(text):
    """
    Cleans raw text by:
    1. Lowercasing
    2. Removing non-alphabetic characters (except whitespace)
    3. Normalizing whitespaces
    """
    if not text:
        return ""
    
    # 1. Case folding
    text = text.lower()
    
    # 2. Remove numbers, symbols, and non-alphabetic characters
    # Keep only a-z and whitespace
    text = re.sub(r'[^a-z\s]', ' ', text)
    
    # 3. Normalize whitespaces (convert newlines/tabs to space, remove double spaces)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
