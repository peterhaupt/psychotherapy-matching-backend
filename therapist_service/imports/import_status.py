"""Import status tracking for monitoring."""
from datetime import datetime, date, timedelta
from typing import Dict, Optional, List
import threading


class ImportStatus:
    """Track import statistics and status."""
    
    # Class-level state
    _lock = threading.Lock()
    _status = {
        'running': True,
        'last_check': None,
        'last_import_run': None,
        'files_processed_today': 0,
        'therapists_processed_today': 0,
        'therapists_failed_today': 0,
        'last_error': None,
        'last_error_time': None,
        'total_files_processed': 0,
        'total_therapists_processed': 0,
        'total_therapists_failed': 0,
        'current_date': date.today(),
        'recent_imports': []  # List of recent file imports
    }
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get current import status.
        
        Returns:
            Dictionary with current status
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['therapists_processed_today'] = 0
                cls._status['therapists_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            return {
                'running': cls._status['running'],
                'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                'last_import_run': cls._status['last_import_run'].isoformat() if cls._status['last_import_run'] else None,
                'next_import_run': cls._calculate_next_run(),
                'files_processed_today': cls._status['files_processed_today'],
                'therapists_processed_today': cls._status['therapists_processed_today'],
                'therapists_failed_today': cls._status['therapists_failed_today'],
                'last_error': cls._status['last_error'],
                'last_error_time': cls._status['last_error_time'].isoformat() if cls._status['last_error_time'] else None,
                'total_files_processed': cls._status['total_files_processed'],
                'total_therapists_processed': cls._status['total_therapists_processed'],
                'total_therapists_failed': cls._status['total_therapists_failed'],
                'recent_imports': cls._status['recent_imports'][-10:]  # Last 10 imports
            }
    
    @classmethod
    def get_health_status(cls) -> Dict:
        """Get health status for the import system.
        
        Returns:
            Dictionary with health status in same format as main health endpoint
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['therapists_processed_today'] = 0
                cls._status['therapists_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            # Determine health status
            is_healthy = True
            issues = []
            
            # Check if monitor is running
            if not cls._status['running']:
                is_healthy = False
                issues.append("Import monitor not running")
            
            # Check for recent startup/critical errors
            if cls._status['last_error'] and cls._status['last_error_time']:
                error_age = datetime.utcnow() - cls._status['last_error_time']
                # If error is recent (within last hour) and we haven't processed files since
                if error_age < timedelta(hours=1) and cls._status['last_check'] is None:
                    is_healthy = False
                    issues.append("Recent startup error")
            
            # Check failure rate for recent imports (last 20 imports)
            recent_imports = cls._status['recent_imports'][-20:]
            if len(recent_imports) >= 5:  # Only check if we have enough data
                failed_recent = sum(1 for imp in recent_imports if imp.get('failed_count', 0) > 0)
                total_therapists = sum(imp.get('therapist_count', 0) for imp in recent_imports)
                total_failed = sum(imp.get('failed_count', 0) for imp in recent_imports)
                
                if total_therapists > 0:
                    failure_rate = total_failed / total_therapists
                    if failure_rate > 0.5:  # More than 50% failure rate
                        is_healthy = False
                        issues.append(f"High failure rate: {failure_rate:.1%}")
            
            # Check if last check was too long ago (more than 25 hours for therapist import)
            if cls._status['last_check']:
                time_since_check = datetime.utcnow() - cls._status['last_check']
                if time_since_check > timedelta(hours=25):
                    is_healthy = False
                    issues.append("Monitor inactive for too long")
            
            return {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'service': 'therapist-import-monitor',
                'details': {
                    'monitor_running': cls._status['running'],
                    'last_check': cls._status['last_check'].isoformat() if cls._status['last_check'] else None,
                    'files_processed_today': cls._status['files_processed_today'],
                    'therapists_processed_today': cls._status['therapists_processed_today'],
                    'therapists_failed_today': cls._status['therapists_failed_today'],
                    'last_error': cls._status['last_error'],
                    'last_error_time': cls._status['last_error_time'].isoformat() if cls._status['last_error_time'] else None,
                    'issues': issues
                }
            }
    
    @classmethod
    def _calculate_next_run(cls) -> Optional[str]:
        """Calculate when the next import run will occur.
        
        Returns:
            ISO formatted datetime string or None
        """
        if not cls._status['last_import_run']:
            return None
        
        # Add 24 hours to last run
        from datetime import timedelta
        next_run = cls._status['last_import_run'] + timedelta(hours=24)
        return next_run.isoformat()
    
    @classmethod
    def update_last_check(cls):
        """Update the last check timestamp."""
        with cls._lock:
            cls._status['last_check'] = datetime.utcnow()
            cls._status['last_import_run'] = datetime.utcnow()
    
    @classmethod
    def record_file_processed(cls, file_name: str, therapist_count: int, failed_count: int):
        """Record a processed file with therapist counts.
        
        Args:
            file_name: Name of the processed file
            therapist_count: Total therapists in the file
            failed_count: Number of failed imports
        """
        with cls._lock:
            # Reset daily counters if date changed
            if cls._status['current_date'] != date.today():
                cls._status['current_date'] = date.today()
                cls._status['files_processed_today'] = 0
                cls._status['therapists_processed_today'] = 0
                cls._status['therapists_failed_today'] = 0
                cls._status['recent_imports'] = []
            
            cls._status['files_processed_today'] += 1
            cls._status['therapists_processed_today'] += therapist_count
            cls._status['therapists_failed_today'] += failed_count
            
            cls._status['total_files_processed'] += 1
            cls._status['total_therapists_processed'] += therapist_count
            cls._status['total_therapists_failed'] += failed_count
            
            cls._status['recent_imports'].append({
                'file': file_name,
                'therapist_count': therapist_count,
                'success_count': therapist_count - failed_count,
                'failed_count': failed_count,
                'time': datetime.utcnow().isoformat()
            })
            
            # Keep only last 50 imports in memory
            if len(cls._status['recent_imports']) > 50:
                cls._status['recent_imports'] = cls._status['recent_imports'][-50:]
    
    @classmethod
    def record_error(cls, error: str):
        """Record a general error (not file-specific).
        
        Args:
            error: Error message
        """
        with cls._lock:
            cls._status['last_error'] = error
            cls._status['last_error_time'] = datetime.utcnow()
    
    @classmethod
    def set_running(cls, running: bool):
        """Set the running status.
        
        Args:
            running: Whether the import is running
        """
        with cls._lock:
            cls._status['running'] = running