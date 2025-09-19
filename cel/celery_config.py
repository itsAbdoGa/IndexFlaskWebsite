from celery import Celery
from kombu import Queue
import os
import ssl
# Redis configuration
REDIS_URL = "rediss://default:ARjgAAImcDI0ZjM3MjE0ODYwZjI0Mjk1YmM2OGE5MGQyNDNmMzU5NXAyNjM2OA@growing-rabbit-6368.upstash.io:6379"
ssl_options = {
    'ssl_cert_reqs': ssl.CERT_NONE  # or CERT_REQUIRED if you have proper certs
}
# Create Celery app
celery_app = Celery('store_processor')

# Celery configuration
celery_app.conf.update(
    # Broker and result backend
    broker_url=REDIS_URL,
    result_backend=REDIS_URL,
    broker_use_ssl=ssl_options,
    
    # Task routing - separate queues for each store
    task_routes={
        'tasks.process_single_entry': {'queue': 'default'},
        'tasks.process_csv_chunk': {'queue': 'csv_processing'},
        'tasks.process_manual_entry': {'queue': 'high_priority'},
    },
    
    # Queue definitions
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('csv_processing', routing_key='csv_processing'),
        Queue('high_priority', routing_key='high_priority'),
    ),
    
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Optimization settings
    task_compression='gzip',
    result_compression='gzip',
    
    # Memory and performance optimization
    worker_prefetch_multiplier=2,  # Reduce prefetching to save memory
    task_acks_late=True,  # Acknowledge tasks after completion for reliability
    worker_disable_rate_limits=True,
    
    # Result expiration
    result_expires=3600,  # 1 hour
    
    # Task retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Concurrency settings
    worker_concurrency=4,  # Adjust based on your server specs
    
    # Memory management
    worker_max_tasks_per_child=100,  # Restart workers after 100 tasks to prevent memory leaks
    worker_max_memory_per_child=200000,  # 200MB per worker

)


