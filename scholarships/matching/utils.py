import re
from datetime import datetime
from typing import Optional

def parse_float(text: str) -> Optional[float]:
    try:
        match = re.findall(r'\d+(?:\.\d+)?', text)
        return float(match[0]) if match else None
    except (ValueError, TypeError):
        return None

def parse_date(text: str) -> Optional[datetime.date]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    return None
