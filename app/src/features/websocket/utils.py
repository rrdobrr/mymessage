import json
from datetime import datetime

class DateTimeEncoder(json.JSONEncoder):
    """Кастомный JSON encoder для datetime объектов"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)