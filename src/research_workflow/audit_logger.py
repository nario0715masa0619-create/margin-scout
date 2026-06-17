import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class AuditLogger:
    def __init__(self, log_dir: str):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().isoformat()
        self.log_path = self.log_dir / f"audit_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.stats = {
            'total_input': 0,
            'successful': 0,
            'skipped': 0
        }
        self.errors = []

    def log_event(self, event_name: str, data: Dict[str, Any]):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_name,
            'data': data
        }
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def log_error(self, sku: str, row_index: int, error_type: str, error_message: str):
        error_detail = {
            'sku': sku,
            'row_index': row_index,
            'error_type': error_type,
            'error_message': error_message
        }
        self.errors.append(error_detail)
        self.log_event('error', error_detail)

    def get_error_details(self) -> list:
        return self.errors
