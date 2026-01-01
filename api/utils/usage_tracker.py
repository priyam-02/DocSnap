import time
from collections import defaultdict


class UsageTracker:
    """Track character usage toward HF API limits"""

    def __init__(self, monthly_limit: int = 30000):
        self.monthly_limit = monthly_limit
        self.usage = defaultdict(int)  # {month: char_count}

    def track(self, char_count: int):
        """Record character usage for current month"""
        month_key = time.strftime("%Y-%m")
        self.usage[month_key] += char_count

    def get_remaining(self) -> int:
        """Get remaining characters for current month"""
        month_key = time.strftime("%Y-%m")
        used = self.usage.get(month_key, 0)
        return max(0, self.monthly_limit - used)

    def is_quota_exceeded(self) -> bool:
        """Check if monthly quota is exceeded"""
        return self.get_remaining() == 0


# Global tracker instance
usage_tracker = UsageTracker()
