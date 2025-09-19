import json
import time
import os
import pandas as pd
import requests
from celery import group, chain
from celery.exceptions import Retry
from celery_config import celery_app
from core.database import get_db_connection
from utils import extract_number, log_message_with_store
from processcon.process_config import PROCESS_CONFIGS
from config import Config

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
CHUNK_SIZE = 50  # Process 50 rows per chunk to balance memory and efficiency


@celery_app.task(bind=True, max_retries=3)
def process_single_entry(self, upc, zip_code, store):
    """Process a single UPC-ZIP entry"""
    try:
        return _process_entry_core(upc, zip_code, store)
    except Exception as exc:
        log_message_with_store(f"Error processing {upc}: {str(exc)}", store)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        return False


@celery_app.task(bind=True, max_retries=2)
def process_manual_entry(self, upc, zip_code, store):
    """Process high-priority manual entry"""
    log_message_with_store(f"Processing HIGH PRIORITY manual entry: UPC {upc}, ZIP {zip_code}", store)
    try:
        return _process_entry_core(upc, zip_code, store)
    except Exception as exc:
        log_message_with_store(f"Error processing manual entry {upc}: {str(exc)}", store)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30, exc=exc)
        return False


@celery_app.task(bind=True, max_retries=2)
def process_csv_chunk(self, chunk_data, chunk_index, total_chunks, store, job_id):
    """Process a chunk of CSV data"""
    try:
        log_message_with_store(f"Processing chunk {chunk_index + 1}/{total_chunks} for job {job_id}", store)
        
        processed = 0
        failed = 0
        
        for row_data in chunk_data:
            upc = row_data.get('upc')
            zip_code = str(row_data.get('zip', ''))
            
            if len(zip_code) < 5:
                zip_code = "0" + zip_code
            
            if upc and zip_code:
                success = _process_entry_core(str(upc), str(zip_code), store)
                if success:
                    processed += 1
                else:
                    failed += 1
            else:
                failed += 1
                log_message_with_store(f"Skipping row with missing UPC or ZIP", store)
        
        # Update progress in Redis
        _update_job_progress(job_id, processed, failed)
        
        log_message_with_store(f"Completed chunk {chunk_index + 1}/{total_chunks}: {processed} processed, {failed} failed", store)
        return {"processed": processed, "failed": failed, "chunk_index": chunk_index}
        
    except Exception as exc:
        log_message_with_store(f"Error processing chunk {chunk_index + 1}: {str(exc)}", store)
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=120, exc=exc)
        return {"processed": 0, "failed": len(chunk_data), "chunk_index": chunk_index, "error": str(exc)}


@celery_app.task
def process_csv_file_task(filepath, store, job_id=None):
    """Process entire CSV file by splitting into chunks"""
    try:
        if job_id is None:
            job_id = f"csv_{store}_{int(time.time())}"
        
        log_message_with_store(f"Starting CSV processing for job {job_id}: {filepath}", store)
        
        # Read and validate CSV file
        if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
            df = pd.read_excel(filepath, engine='openpyxl')
        else:
            df = pd.read_csv(filepath, dtype=str)
        
        df.columns = [col.strip().lower() for col in df.columns]
        total_rows = len(df)
        
        if total_rows == 0:
            log_message_with_store(f"CSV file is empty: {filepath}", store)
            return {"job_id": job_id, "status": "completed", "total_rows": 0, "processed": 0, "failed": 0}
        
        # Initialize job tracking in Redis
        _init_job_tracking(job_id, total_rows, store)
        
        # Split DataFrame into chunks
        chunks = [df[i:i + CHUNK_SIZE] for i in range(0, len(df), CHUNK_SIZE)]
        total_chunks = len(chunks)
        
        log_message_with_store(f"Split CSV into {total_chunks} chunks of max {CHUNK_SIZE} rows each", store)
        
        # Create chunk tasks
        chunk_tasks = []
        for i, chunk in enumerate(chunks):
            chunk_data = chunk.to_dict('records')
            task = process_csv_chunk.s(chunk_data, i, total_chunks, store, job_id)
            chunk_tasks.append(task)
        
        # Execute chunks in parallel using Celery group
        job = group(chunk_tasks)
        result = job.apply_async()
        
        # Store job info in Redis for tracking
        _store_job_info(job_id, result.id, total_rows, store)
        
        log_message_with_store(f"Dispatched {total_chunks} chunk tasks for job {job_id}", store)
        return {"job_id": job_id, "celery_group_id": result.id, "total_chunks": total_chunks, "total_rows": total_rows}
        
    except Exception as e:
        log_message_with_store(f"Error processing CSV file {filepath}: {e}", store)
        return {"job_id": job_id, "status": "failed", "error": str(e)}
    finally:
        # Clean up file
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                log_message_with_store(f"Cleaned up CSV file: {filepath}", store)
            except Exception as e:
                log_message_with_store(f"Error cleaning up file {filepath}: {e}", store)


@celery_app.task
def cancel_csv_job(job_id, store):
    """Cancel a CSV processing job"""
    try:
        import redis
        redis_client = redis.from_url(celery_app.conf.broker_url)
        
        # Get job info
        job_info = redis_client.hgetall(f"job:{job_id}")
        if job_info:
            celery_group_id = job_info.get(b'celery_group_id', b'').decode()
            if celery_group_id:
                # Revoke all tasks in the group
                celery_app.control.revoke(celery_group_id, terminate=True)
                log_message_with_store(f"Cancelled job {job_id} (group: {celery_group_id})", store)
        
        # Update job status
        redis_client.hset(f"job:{job_id}", "status", "cancelled")
        redis_client.expire(f"job:{job_id}", 3600)  # Expire in 1 hour
        
        return {"job_id": job_id, "status": "cancelled"}
        
    except Exception as e:
        log_message_with_store(f"Error cancelling job {job_id}: {e}", store)
        return {"job_id": job_id, "status": "error", "error": str(e)}


def _process_entry_core(upc, zip_code, store):
    """Core processing logic for UPC-ZIP entries"""
    conf = PROCESS_CONFIGS[store]
    
    # Store in olditem table
    _store_upc_zip(upc, zip_code, store)
    
    if len(zip_code) < 5:
        zip_code = "0" + zip_code
    
    if not upc or not zip_code:
        return False
    
    payload = json.dumps({"storeName": store, "upc": upc, "zip": zip_code})
    headers = {'Content-Type': 'application/json'}
    
    try:
        # Use requests with timeout
        response = requests.post(conf["API"], headers=headers, data=payload, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        log_message_with_store(f"API request failed for {upc}: {str(e)}", store)
        return False
    
    if "stores" not in response_data or "itemDetails" not in response_data:
        log_message_with_store(f"Invalid API response for {upc}: missing stores or itemDetails", store)
        return False
    
    # Database operations with connection pooling
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            item = response_data["itemDetails"]
            schema = conf['schema']
            productid = extract_number(item.get("url"))
            
            # Insert item
            if store == "walmart":
                cursor.execute(
                    conf["itemquery"],
                    (item["name"], upc, productid, item.get("msrp"), item.get("imageUrl"))
                )
            else:
                cursor.execute(
                    conf["itemquery"],
                    (item["name"], upc, productid, item.get("imageUrl"))
                )
            
            conn.commit()
            
            # Get item ID
            cursor.execute(f"SELECT id FROM {schema}.items WHERE upc = %s", (upc,))
            item_id = cursor.fetchone()[0]
            
            # Process stores
            for location in response_data["stores"]:
                store_id = int(location["id"])
                
                # Insert store
                cursor.execute(
                    conf["storequery"],
                    (store_id, location["address"], location["city"], location["state"], location["zip"])
                )
                
                # Insert store-item relationship
                if store == "walmart":
                    cursor.execute(
                        conf["siquery"],
                        (
                            store_id,
                            item_id,
                            location["price"],
                            location.get("salesFloor", 0),
                            location.get("backRoom", 0),
                            location.get("aisles", "None"),
                        )
                    )
                else:
                    cursor.execute(
                        conf["siquery"],
                        (
                            store_id,
                            item_id,
                            location["storePrice"],
                            location["storeStock"],
                        )
                    )
            
            conn.commit()
            log_message_with_store(f"Successfully processed: UPC {upc}, ZIP {zip_code}", store)
            return True
            
    except Exception as e:
        log_message_with_store(f"Database error for UPC {upc}: {str(e)}", store)
        return False


def _store_upc_zip(upc, zip_code, store):
    """Store UPC-ZIP combination in olditem table"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = int(time.time())
        
        cursor.execute("""
            INSERT INTO main.olditem (upc, zip, timestamp, store)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (upc, zip) DO UPDATE
            SET timestamp = EXCLUDED.timestamp, store = EXCLUDED.store
        """, (upc, zip_code, current_time, store))
        
        conn.commit()


def _init_job_tracking(job_id, total_rows, store):
    """Initialize job tracking in Redis"""
    import redis
    redis_client = redis.from_url(celery_app.conf.broker_url)
    
    job_data = {
        "status": "processing",
        "total_rows": total_rows,
        "processed": 0,
        "failed": 0,
        "store": store,
        "created_at": int(time.time())
    }
    
    redis_client.hmset(f"job:{job_id}", job_data)
    redis_client.expire(f"job:{job_id}", 86400)  # Expire in 24 hours


def _store_job_info(job_id, celery_group_id, total_rows, store):
    """Store additional job info in Redis"""
    import redis
    redis_client = redis.from_url(celery_app.conf.broker_url)
    
    redis_client.hset(f"job:{job_id}", "celery_group_id", celery_group_id)


def _update_job_progress(job_id, processed_delta, failed_delta):
    """Update job progress in Redis"""
    import redis
    redis_client = redis.from_url(celery_app.conf.broker_url)
    
    pipe = redis_client.pipeline()
    pipe.hincrby(f"job:{job_id}", "processed", processed_delta)
    pipe.hincrby(f"job:{job_id}", "failed", failed_delta)
    pipe.execute()


# Task monitoring functions
@celery_app.task
def get_job_status(job_id):
    """Get status of a processing job"""
    import redis
    redis_client = redis.from_url(celery_app.conf.broker_url)
    
    job_data = redis_client.hgetall(f"job:{job_id}")
    if not job_data:
        return {"job_id": job_id, "status": "not_found"}
    
    # Convert bytes to strings
    result = {}
    for key, value in job_data.items():
        result[key.decode()] = value.decode()
    
    # Convert numeric fields
    for field in ['total_rows', 'processed', 'failed', 'created_at']:
        if field in result:
            result[field] = int(result[field])
    
    result['job_id'] = job_id
    return result