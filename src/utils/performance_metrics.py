from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from src.agents.task_type import TaskType

@dataclass
class PerformanceMetrics:
    """מחלקה לאיסוף וניתוח מדדי ביצועים"""
    
    # זמני ביצוע
    start_time: datetime = field(default_factory=datetime.now)
    total_time: float = 0.0  # זמן כולל בשניות
    api_call_time: float = 0.0  # זמן קריאה ל-API
    cache_lookup_time: float = 0.0  # זמן חיפוש במטמון
    
    # מידע על הבקשה
    task_type: Optional[TaskType] = None  # סוג המשימה
    attempt_count: int = 0  # מספר ניסיונות
    response_length: int = 0  # אורך התשובה בתווים
    
    # מידע על המטמון
    cache_hit: bool = False  # האם נמצא במטמון
    
    def to_dict(self) -> dict:
        """המרה למילון לצורך שמירה בלוג"""
        return {
            "timestamp": self.start_time.isoformat(),
            "total_time_seconds": round(self.total_time, 3),
            "api_call_time_seconds": round(self.api_call_time, 3),
            "cache_lookup_time_seconds": round(self.cache_lookup_time, 3),
            "task_type": self.task_type.name if self.task_type else None,
            "attempt_count": self.attempt_count,
            "response_length": self.response_length,
            "cache_hit": self.cache_hit
        }
    
    @staticmethod
    def calculate_averages(metrics_list: list['PerformanceMetrics']) -> dict:
        """חישוב ממוצעים וסטטיסטיקות"""
        if not metrics_list:
            return {}
            
        total_metrics = len(metrics_list)
        cache_hits = sum(1 for m in metrics_list if m.cache_hit)
        
        # מיון לפי זמן כולל
        sorted_total_times = sorted(m.total_time for m in metrics_list)
        median_total_time = sorted_total_times[total_metrics // 2]
        
        return {
            "avg_total_time": sum(m.total_time for m in metrics_list) / total_metrics,
            "avg_api_time": sum(m.api_call_time for m in metrics_list) / total_metrics,
            "avg_cache_lookup_time": sum(m.cache_lookup_time for m in metrics_list) / total_metrics,
            "cache_hit_rate": cache_hits / total_metrics,
            "median_total_time": median_total_time,
            "max_total_time": max(m.total_time for m in metrics_list),
            "avg_attempts": sum(m.attempt_count for m in metrics_list) / total_metrics,
            "avg_response_length": sum(m.response_length for m in metrics_list) / total_metrics,
            "total_requests": total_metrics,
            
            # התפלגות לפי סוג משימה
            "task_type_distribution": {
                task_type.name: sum(1 for m in metrics_list if m.task_type == task_type) / total_metrics
                for task_type in TaskType
                if any(m.task_type == task_type for m in metrics_list)
            }
        } 