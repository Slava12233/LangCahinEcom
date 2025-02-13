from dataclasses import dataclass
from typing import Optional

@dataclass
class PerformanceMetrics:
    """מטריקות ביצועים"""
    
    # זמנים
    total_time: float = 0.0
    api_call_time: float = 0.0
    cache_lookup_time: float = 0.0
    
    # מטמון
    cache_hit: bool = False
    
    # תשובה
    response_length: int = 0
    
    # סוג משימה
    task_type: Optional[str] = None 