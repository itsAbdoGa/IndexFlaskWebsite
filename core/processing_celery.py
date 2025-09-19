import os
import time
import pandas as pd
import redis
from cel.tasks import process_manual_entry, process_csv_file_task, cancel_csv_job, get_job_status
from cel.celery_config import celery_app
from utils import log_message_with_store
from config import Config
from collections import defaultdict

UPLOAD_FOLDER = Config.UPLOAD_FOLDER

class CeleryStoreProcessingManager:
    def __init__(self):
        self.redis_client = redis.from_url(celery_app.conf.broker_url)
        
    def add_manual_entry(self, upc, zip_code, store):
        """Add high-priority manual entry"""
        log_message_with_store(f"Dispatching HIGH PRIORITY manual entry: UPC {upc}, ZIP {zip_code}", store)
        task = process_manual_entry.apply_async(
            args=[upc, zip_code, store],
            queue='high_priority',
            priority=9  # High priority
        )
        
        # Store task info for tracking
        self._store_task_info(f"manual_{store}_{int(time.time())}", task.id, "manual", store)
        return task.id
    
    def add_csv_processing(self, filepath, store, start_row=0, total_rows=None):
        """Add CSV processing task"""
        job_id = f"csv_{store}_{int(time.time())}"
        
        log_message_with_store(f"Dispatching CSV processing job {job_id}: {filepath}", store)
        
        task = process_csv_file_task.apply_async(
            args=[filepath, store, job_id],
            queue='csv_processing',
            priority=5  # Normal priority
        )
        
        # Store task info
        self._store_task_info(job_id, task.id, "csv", store)
        return job_id
    
    def cancel_csv_processing(self, store=None, job_id=None):
        """Cancel CSV processing for a store or specific job"""
        if job_id:
            # Cancel specific job
            task = cancel_csv_job.apply_async(args=[job_id, store])
            log_message_with_store(f"Dispatched cancellation for job {job_id}", store or "system")
            return task.id
        
        if store:
            # Cancel all jobs for a specific store
            pattern = f"task:csv_{store}_*"
            keys = self.redis_client.keys(pattern)
            cancelled_jobs = []
            
            for key in keys:
                task_info = self.redis_client.hgetall(key)
                if task_info and task_info.get(b'status', b'').decode() == 'processing':
                    job_id_from_key = key.decode().split(':', 1)[1]
                    task = cancel_csv_job.apply_async(args=[job_id_from_key, store])
                    cancelled_jobs.append(job_id_from_key)
            
            log_message_with_store(f"Cancelled {len(cancelled_jobs)} jobs for store {store}", store)
            return cancelled_jobs
        
        # Cancel all jobs for all stores
        pattern = "task:csv_*"
        keys = self.redis_client.keys(pattern)
        cancelled_jobs = []
        
        for key in keys:
            task_info = self.redis_client.hgetall(key)
            if task_info and task_info.get(b'status', b'').decode() == 'processing':
                job_id_from_key = key.decode().split(':', 1)[1]
                store_from_info = task_info.get(b'store', b'unknown').decode()
                task = cancel_csv_job.apply_async(args=[job_id_from_key, store_from_info])
                cancelled_jobs.append(job_id_from_key)
        
        log_message_with_store(f"Cancelled {len(cancelled_jobs)} jobs for all stores", "system")
        return cancelled_jobs
    
    def get_store_status(self, store):
        """Get processing status for a specific store"""
        try:
            # Count active tasks for this store
            pattern = f"task:*_{store}_*"
            keys = self.redis_client.keys(pattern)
            
            active_tasks = 0
            csv_processing = False
            queue_size = 0
            
            for key in keys:
                task_info = self.redis_client.hgetall(key)
                if task_info:
                    status = task_info.get(b'status', b'').decode()
                    task_type = task_info.get(b'type', b'').decode()
                    
                    if status == 'processing':
                        active_tasks += 1
                        if task_type == 'csv':
                            csv_processing = True
                    elif status in ['pending', 'queued']:
                        queue_size += 1
            
            # Get Celery queue sizes
            inspect = celery_app.control.inspect()
            active = inspect.active()
            reserved = inspect.reserved()
            
            worker_active = False
            if active:
                for worker, tasks in active.items():
                    for task in tasks:
                        if store in str(task.get('args', [])):
                            worker_active = True
                            break
            
            if reserved and not worker_active:
                for worker, tasks in reserved.items():
                    for task in tasks:
                        if store in str(task.get('args', [])):
                            worker_active = True
                            break
            
            return {
                "queue_size": queue_size,
                "worker_active": worker_active,
                "csv_processing": csv_processing,
                "active_tasks": active_tasks
            }
        
        except Exception as e:
            log_message_with_store(f"Error getting store status: {e}", store)
            return {
                "queue_size": 0,
                "worker_active": False,
                "csv_processing": False,
                "active_tasks": 0
            }
    
    def get_all_stores_status(self):
        """Get status for all stores"""
        try:
            stores_status = defaultdict(lambda: {
                "queue_size": 0,
                "worker_active": False,
                "csv_processing": False,
                "active_tasks": 0
            })
            
            # Get all task keys
            pattern = "task:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                task_info = self.redis_client.hgetall(key)
                if task_info:
                    store = task_info.get(b'store', b'unknown').decode()
                    status = task_info.get(b'status', b'').decode()
                    task_type = task_info.get(b'type', b'').decode()
                    
                    if status == 'processing':
                        stores_status[store]["active_tasks"] += 1
                        if task_type == 'csv':
                            stores_status[store]["csv_processing"] = True
                    elif status in ['pending', 'queued']:
                        stores_status[store]["queue_size"] += 1
            
            # Check worker activity
            try:
                inspect = celery_app.control.inspect()
                active = inspect.active()
                reserved = inspect.reserved()
                
                if active:
                    for worker, tasks in active.items():
                        for task in tasks:
                            args = task.get('args', [])
                            if len(args) >= 3 and isinstance(args[2], str):  # Store is 3rd arg
                                store = args[2]
                                stores_status[store]["worker_active"] = True
                
                if reserved:
                    for worker, tasks in reserved.items():
                        for task in tasks:
                            args = task.get('args', [])
                            if len(args) >= 3 and isinstance(args[2], str):
                                store = args[2]
                                stores_status[store]["worker_active"] = True
            
            except Exception as e:
                log_message_with_store(f"Error checking worker activity: {e}", "system")
            
            return dict(stores_status)
            
        except Exception as e:
            log_message_with_store(f"Error getting all stores status: {e}", "system")
            return {}
    
    def get_job_status(self, job_id):
        """Get status of a specific job"""
        task = get_job_status.apply_async(args=[job_id])
        return task.get(timeout=5)
    
    def _store_task_info(self, task_key, celery_task_id, task_type, store):
        """Store task information in Redis for tracking"""
        task_data = {
            "celery_task_id": celery_task_id,
            "type": task_type,
            "store": store,
            "status": "processing",
            "created_at": int(time.time())
        }
        
        self.redis_client.hmset(f"task:{task_key}", task_data)
        self.redis_client.expire(f"task:{task_key}", 86400)  # 24 hours
    
    def cleanup_completed_tasks(self, max_age_hours=24):
        """Clean up old completed/failed task records"""
        cutoff_time = int(time.time()) - (max_age_hours * 3600)
        
        pattern = "task:*"
        keys = self.redis_client.keys(pattern)
        cleaned = 0
        
        for key in keys:
            task_info = self.redis_client.hgetall(key)
            if task_info:
                created_at = int(task_info.get(b'created_at', 0))
                status = task_info.get(b'status', b'').decode()
                
                if created_at < cutoff_time and status in ['completed', 'failed', 'cancelled']:
                    self.redis_client.delete(key)
                    cleaned += 1
        
        if cleaned > 0:
            log_message_with_store(f"Cleaned up {cleaned} old task records", "system")
        
        return cleaned


# Global instance
celery_store_manager = CeleryStoreProcessingManager()

# Legacy compatibility functions
def add_manual_entry(upc, zip_code, store):
    """Add a manual entry (high priority)"""
    return celery_store_manager.add_manual_entry(upc, zip_code, store)

def add_csv_processing(filepath, store, start_row=0, total_rows=None):
    """Add CSV processing task"""
    return celery_store_manager.add_csv_processing(filepath, store, start_row, total_rows)

def cancel_csv_processing(store=None):
    """Cancel CSV processing for a store or all stores"""
    return celery_store_manager.cancel_csv_processing(store)

def get_store_status(store):
    """Get processing status for a specific store"""
    return celery_store_manager.get_store_status(store)

def get_all_status():
    """Get processing status for all stores"""
    return celery_store_manager.get_all_stores_status()

def start_processing_worker():
    """Legacy function - not needed with Celery"""
    pass