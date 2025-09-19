import os
from gevent import queue
import gevent
from gevent.pool import Pool
from config import Config, Priority
from utils import log_message_with_store
from processcon.process_engine import process_entry
from collections import defaultdict
import threading

UPLOAD_FOLDER = Config.UPLOAD_FOLDER

class StoreSpecificProcessingManager:
    def __init__(self):
        # Store-specific queues and workers
        self.store_queues = defaultdict(lambda: queue.PriorityQueue())
        self.store_workers = {}  # Track active workers per store
        self.store_csv_flags = defaultdict(bool)  # CSV processing flags per store
        self.csv_cancel_flags = defaultdict(bool)  # Cancel flags per store
        self.worker_pool = Pool(50)  # Large pool to handle multiple stores
        self.lock = threading.Lock()
        
    def add_to_store_queue(self, store, priority, item_type, data):
        """Add an item to a specific store's queue"""
        if store not in self.store_queues:
            self.store_queues[store] = queue.PriorityQueue()
        
        self.store_queues[store].put((priority, item_type, data))
        log_message_with_store(f"Added {item_type} item to {store} queue (priority: {priority})", store)
        
        # Start worker for this store if not already running
        self.ensure_store_worker(store)
    
    def ensure_store_worker(self, store):
        """Ensure a worker is running for the specified store"""
        with self.lock:
            if store not in self.store_workers or self.store_workers[store].dead:
                worker = self.worker_pool.spawn(self.store_queue_worker, store)
                self.store_workers[store] = worker
                log_message_with_store(f"Started queue worker for store: {store}", store)
    
    def store_queue_worker(self, store):
        """Background worker that processes items from a specific store's queue"""
        log_message_with_store(f"Store worker started for: {store}", store)
        
        while True:
            try:
                # Get item from this store's priority queue (blocks until available)
                if store not in self.store_queues:
                    gevent.sleep(1)
                    continue
                    
                try:
                    queue_item = self.store_queues[store].get(timeout=30)  # 30 second timeout
                except queue.Empty:
                    # No items for 30 seconds, worker can exit
                    log_message_with_store(f"Store worker for {store} idle, shutting down", store)
                    with self.lock:
                        if store in self.store_workers:
                            del self.store_workers[store]
                    return
                
                # Validate queue item structure
                if not queue_item or len(queue_item) != 3:
                    log_message_with_store(f"Store {store}: Invalid queue item received: {queue_item}", store)
                    continue
                    
                priority, item_type, data = queue_item
                
                # Validate data is not None
                if data is None:
                    log_message_with_store(f"Store {store}: Received None data for item type: {item_type}", store)
                    continue
                
                if item_type == "manual":
                    self._process_manual_entry(store, data)
                    
                elif item_type == "csv":
                    # Check for duplicates in this store's queue
                    queue_contents = list(self.store_queues[store].queue)
                    if (Priority.LOW, "csv", data) in queue_contents:
                        log_message_with_store(f"Store {store}: Duplicate CSV item detected, skipping", store)
                        continue
                    
                    # Set CSV processing flag for this store
                    self.store_csv_flags[store] = True
                    try:
                        self._process_csv_entry(store, data)
                    finally:
                        self.store_csv_flags[store] = False
                else:
                    log_message_with_store(f"Store {store}: Unknown item type: {item_type}", store)
                            
            except Exception as e:
                log_message_with_store(f"Store {store} worker error: {e}", store)
                self.store_csv_flags[store] = False
    
    def _process_manual_entry(self, store, data):
        """Process manual entry for a specific store"""
        if not isinstance(data, tuple) or len(data) != 3:
            log_message_with_store(f"Store {store}: Invalid manual entry data: {data}", store)
            return
            
        upc, zip_code, entry_store = data
        
        # Ensure the store matches (data should contain the store info)
        if entry_store != store:
            log_message_with_store(f"Store mismatch: expected {store}, got {entry_store}", store)
            return
            
        log_message_with_store(f"Store {store}: Processing HIGH PRIORITY manual entry: UPC {upc}, ZIP {zip_code}", store)
        success = process_entry(upc, zip_code, store)
        log_message_with_store(f"Store {store}: Manual entry processed: {'success' if success else 'failed'}", store)
    
    def _process_csv_entry(self, store, data):
        """Process CSV entry for a specific store"""
        try:
            if isinstance(data, tuple) and len(data) == 4:
                filepath, start_row, total_rows, csv_store = data
                if csv_store != store:
                    log_message_with_store(f"Store mismatch in CSV data: expected {store}, got {csv_store}", store)
                    return
                log_message_with_store(f"Store {store}: Processing CSV file: {filepath}", store)
                self.process_csv_file(filepath, start_row, total_rows, store)
            elif isinstance(data, tuple) and len(data) == 2:
                filepath, csv_store = data
                if csv_store != store:
                    log_message_with_store(f"Store mismatch in CSV data: expected {store}, got {csv_store}", store)
                    return
                log_message_with_store(f"Store {store}: Processing CSV file: {filepath}", store)
                self.process_csv_file(filepath, store=store)
            else:
                log_message_with_store(f"Store {store}: Invalid CSV data format: {data}", store)
        except Exception as csv_error:
            log_message_with_store(f"Store {store}: Error processing CSV: {csv_error}", store)
    
    def cancel_csv_processing(self, store):
        """Set flag to cancel ongoing CSV processing for a specific store"""
        self.csv_cancel_flags[store] = True
        log_message_with_store(f"CSV processing cancellation requested for store: {store} , will be cancelled after processing the current row", store)
    
    def process_csv_file(self, filepath, start_row=0, total_original_rows=None, store=None):
        """Process a CSV file row by row for a specific store, allowing interruption for high priority items"""
        if store is None:
            log_message_with_store("Error: store parameter is required for process_csv_file", "system")
            return
        
        # Reset cancel flag for this store
        self.csv_cancel_flags[store] = False
        
        try:
            import pandas as pd
            
            # Read the CSV/Excel file
            if filepath.endswith('.xlsx') or filepath.endswith('.xls'):
                df = pd.read_excel(filepath, engine='openpyxl')
            else:
                df = pd.read_csv(filepath,dtype=str)
            
            original_total_rows = len(df)
            df.columns = [col.strip().lower() for col in df.columns]
            
            # Calculate total rows for progress tracking
            if total_original_rows is None:
                total_original_rows = original_total_rows
                current_start = 1
            else:
                current_start = start_row + 1
                
            log_message_with_store(f"Store {store}: Starting CSV processing: {len(df)} rows (rows {current_start}-{start_row + len(df)} of {total_original_rows} total)", store)
            
            # Use enumerate to get reliable position tracking
            for current_index, (_, row) in enumerate(df.iterrows()):
                absolute_position = start_row + current_index + 1
                
                # Check for cancellation flag for this store
                if self.csv_cancel_flags[store]:
                    log_message_with_store(f"Store {store}: CSV processing cancelled at row {absolute_position}/{total_original_rows}", store)
                    return
                
                # Check if there are high priority items in THIS store's queue
                if not self.store_queues[store].empty():
                    temp_items = []
                    has_high_priority = False
                    queue_size = self.store_queues[store].qsize()
                    
                    try:
                        # Check up to 5 items in the queue
                        for _ in range(min(5, queue_size)):
                            try:
                                item = self.store_queues[store].get_nowait()
                                temp_items.append(item)
                                if item[0] == Priority.HIGH:
                                    has_high_priority = True
                            except queue.Empty:
                                break
                        
                        # Put items back
                        for item in temp_items:
                            self.store_queues[store].put(item)
                        
                        if has_high_priority:
                            log_message_with_store(f"Store {store}: Pausing CSV processing for high priority manual input at row {absolute_position}", store)
                            
                            # Re-queue remaining CSV data for this store
                            remaining_df = df.iloc[current_index:]
                            if len(remaining_df) > 0:
                                base_name = os.path.splitext(os.path.basename(filepath))[0]
                                original_ext = os.path.splitext(filepath)[1]
                                temp_filepath = f"temp_{store}_{base_name}{original_ext}"
                                temp_full_path = os.path.join(UPLOAD_FOLDER, temp_filepath)
                                
                                if original_ext.lower() in ['.xlsx', '.xls']:
                                    remaining_df.to_excel(temp_full_path, index=False, engine='openpyxl')
                                else:
                                    remaining_df.to_csv(temp_full_path, index=False)
                                
                                new_start_row = start_row + current_index
                                # Add back to THIS store's queue
                                self.store_queues[store].put((Priority.LOW, "csv", (temp_full_path, new_start_row, total_original_rows, store)))
                                log_message_with_store(f"Store {store}: Remaining {len(remaining_df)} rows re-queued as {temp_filepath} (continuing from row {new_start_row})", store)
                            return  # Exit CSV processing now
                            
                    except Exception as queue_error:
                        log_message_with_store(f"Store {store}: Error checking queue priorities: {queue_error}", store)
                        # Put items back in case of error
                        for item in temp_items:
                            self.store_queues[store].put(item)
                
                # Process the current row
                upc = row.get('upc')
                zip_code = str(row.get('zip', ''))
                
                if len(zip_code) < 5:
                    zip_code = "0" + zip_code
                
                if upc and zip_code:
                    log_message_with_store(f"Store {store}: Processing CSV row {absolute_position}/{total_original_rows}: UPC {upc}, ZIP {zip_code}", store)
                    success = process_entry(str(upc), str(zip_code), store)
                    if not success:
                        log_message_with_store(f"Store {store}: Failed to process row {absolute_position}", store)
                else:
                    log_message_with_store(f"Store {store}: Skipping row {absolute_position}/{total_original_rows}: missing UPC or ZIP", store)
                
                # Yield control to allow other greenlets to run
                gevent.sleep(0.01)
                
            log_message_with_store(f"Store {store}: Completed CSV processing: {filepath}", store)
            
            # Clean up original file
            if os.path.exists(filepath):
                os.remove(filepath)
                
        except Exception as e:
            log_message_with_store(f"Store {store}: Error processing CSV file {filepath}: {e}", store)
            import traceback
            log_message_with_store(f"Store {store}: Traceback: {traceback.format_exc()}", store)
        finally:
            self.csv_cancel_flags[store] = False
            # Cleanup temp files for this store
            if filepath and os.path.basename(filepath).startswith(f"temp_{store}_"):
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        log_message_with_store(f"Store {store}: Cleaned up temporary file: {filepath}", store)
                except Exception as e:
                    log_message_with_store(f"Store {store}: Error cleaning up temp file: {e}", store)
    
    def get_store_queue_status(self, store):
        """Get the current status of a store's queue"""
        if store not in self.store_queues:
            return {"queue_size": 0, "worker_active": False, "csv_processing": False}
        
        return {
            "queue_size": self.store_queues[store].qsize(),
            "worker_active": store in self.store_workers and not self.store_workers[store].dead,
            "csv_processing": self.store_csv_flags[store]
        }
    
    def get_all_stores_status(self):
        """Get status for all stores"""
        status = {}
        for store in self.store_queues:
            status[store] = self.get_store_queue_status(store)
        return status

# Global instance
store_processing_manager = StoreSpecificProcessingManager()

# Legacy compatibility functions
def start_processing_worker():
    """Legacy function - now handled automatically per store"""
    pass

def cancel_csv_processing(store=None):
    """Cancel CSV processing for a specific store or all stores"""
    if store:
        store_processing_manager.cancel_csv_processing(store)
    else:
        # Cancel for all stores if no specific store provided
        for store_name in store_processing_manager.csv_cancel_flags:
            store_processing_manager.cancel_csv_processing(store_name)

# New functions for the store-specific system
def add_manual_entry(upc, zip_code, store):
    """Add a manual entry to a store's queue"""
    store_processing_manager.add_to_store_queue(store, Priority.HIGH, "manual", (upc, zip_code, store))

def add_csv_processing(filepath, store, start_row=0, total_rows=None):
    """Add CSV processing to a store's queue"""
    if total_rows is not None:
        data = (filepath, start_row, total_rows, store)
    else:
        data = (filepath, store)
    store_processing_manager.add_to_store_queue(store, Priority.LOW, "csv", data)

def get_store_status(store):
    """Get processing status for a specific store"""
    return store_processing_manager.get_store_queue_status(store)

def get_all_status():
    """Get processing status for all stores"""
    return store_processing_manager.get_all_stores_status()