# Updated admin.py - Replace your existing admin routes
from flask import Blueprint, request, jsonify, render_template
from core.processing_celery import (
    celery_store_manager,
    add_manual_entry, 
    add_csv_processing, 
    cancel_csv_processing, 
    get_store_status, 
)
from utils import log_message, log_message_with_store
from config import Config
import os
import pandas as pd

UPLOAD_FOLDER = Config.UPLOAD_FOLDER
bp = Blueprint('admin', __name__)

@bp.route("/adminpanel")
def admin():
    """Admin panel route"""
    return render_template("admin.html")

@bp.route("/upload_csv", methods=["POST"])
def upload_csv():
    """Handle CSV file upload and process each entry"""
    try:
        if "file" not in request.files:
            return jsonify({"message": "No file provided"}), 400

        file = request.files["file"]
        store = request.form.get('store')
        if not store:
            return jsonify({"message": "Store parameter is required"}), 400
            
        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        base_name = os.path.splitext(file.filename)[0]
        extension = os.path.splitext(file.filename)[1]
        store_filename = f"{store}_{base_name}{extension}"
        filepath = os.path.join(UPLOAD_FOLDER, store_filename)
        
        file.save(filepath)
        log_message_with_store(f"CSV uploaded. Adding to processing queue... {filepath}", store)

        # Add CSV file to Celery processing queue
        job_id = add_csv_processing(filepath, store)
        
        # Get current queue status for this store
        store_status = get_store_status(store)
        
        log_message_with_store(f"CSV uploaded successfully. Job ID: {job_id}. Queue size: {store_status['queue_size']}", store)
        return jsonify({
            "store": store,
            "job_id": job_id,
            "queue_size": store_status["queue_size"],
            "worker_active": store_status["worker_active"],
            "active_tasks": store_status["active_tasks"]
        }), 200

    except Exception as e:
        store = request.form.get('store', 'unknown')
        log_message_with_store(f"Error uploading CSV: {e}", store)
        return jsonify({"message": f"Error uploading CSV: {e}"}), 500

    except Exception as e:
        store = request.form.get('store', 'unknown')
        log_message_with_store(f"Error uploading CSV: {e}", store)
        return jsonify({"message": f"Error uploading CSV: {e}"}), 500

@bp.route("/cancel_upload", methods=["POST"])
def cancel_upload():
    """Cancel ongoing CSV processing and clear queue"""
    try:
        data = request.json or {}
        store = data.get('store')
        job_id = data.get('job_id')
        
        if job_id:
            # Cancel specific job
            cancel_csv_processing(store, job_id)
            return jsonify({
                "job_id": job_id,
                "store": store,
                "message": f"Cancelled job {job_id}"
            })
        
        elif store:
            # Cancel all CSV processing for specific store
            cancelled_jobs = cancel_csv_processing(store)
            
            return jsonify({
                "store": store,
                "cancelled_jobs": cancelled_jobs,
                "jobs_cancelled": len(cancelled_jobs),
                "message": f"Cancelled {len(cancelled_jobs)} jobs for store {store}"
            })
        else:
            # Cancel for all stores
            cancelled_jobs = cancel_csv_processing()
            
            log_message(f"Upload cancelled for all stores. Cancelled {len(cancelled_jobs)} jobs")
            return jsonify({
                "cancelled_jobs": cancelled_jobs,
                "jobs_cancelled": len(cancelled_jobs),
                "message": f"Cancelled {len(cancelled_jobs)} jobs for all stores"
            })
        
    except Exception as e:
        log_message(f"Error cancelling upload: {e}")
        return jsonify({"message": f"Error cancelling upload: {e}"}), 500

@bp.route("/manual_input", methods=["POST"])
def manual_input():
    """Handle manual UPC & ZIP input with HIGH priority"""
    data = request.get_json(silent=True)
    if data:
        upc = data.get("upc")
        zip_code = data.get("zip")
        store = data.get("store")
        searchtype = data.get("search_type")
    else:
        # Fallback to FormData (multipart/form-data)
        upc = request.form.get("upc")
        zip_code = request.form.get("zip")   # will be None in wide search
        store = request.form.get("store")
        searchtype = request.form.get("search_type")
        zip_file = request.files.get("zip_file")  # your CSV file
        
    if not store:
        log_message("Store parameter is required for manual input")
        return jsonify({"message": "Store parameter is required"}), 400
    
    if not searchtype:
        log_message("search type parameter is required for manual input")
        return jsonify({"message": "search parameter is required"}), 400
    
    task_id = None
    job_id = None
    
    if searchtype == "single":
        if not upc or not zip_code:
            log_message_with_store("Both UPC and ZIP are required", store or "unknown")
            return jsonify({"message": "Both UPC and ZIP are required"}), 400
    
        log_message_with_store(f"Adding HIGH PRIORITY manual entry to queue: UPC {upc}, ZIP {zip_code}", store)
        task_id = add_manual_entry(str(upc), str(zip_code), str(store))
        
    else:
        # Wide search with CSV
        if not zip_file or not upc:
            log_message_with_store("UPC and ZIP file are required for wide search", store)
            return jsonify({"message": "UPC and ZIP file are required for wide search"}), 400
            
        df = pd.read_csv(zip_file.stream)
        df['upc'] = str(upc)
        save_path = os.path.join(UPLOAD_FOLDER, f"{store}_wide_search_{zip_file.filename}")
        df.to_csv(save_path, index=False)
        
        job_id = add_csv_processing(save_path, store)
        log_message_with_store(f"Adding HIGH PRIORITY wide search manual entry to queue: UPC {upc}, filepath: {save_path}", store)
    
    store_status = get_store_status(store)
    
    response_data = {
        "store": store,
        "priority": "HIGH",
        "queue_size": store_status["queue_size"],
        "worker_active": store_status["worker_active"],
        "active_tasks": store_status["active_tasks"]
    }
    
    if task_id:
        response_data["task_id"] = task_id
    if job_id:
        response_data["job_id"] = job_id
    
    return jsonify(response_data)

@bp.route("/job_status/<job_id>", methods=["GET"])
def get_job_status(job_id):
    """Get status of a specific processing job"""
    try:
        status = celery_store_manager.get_job_status(job_id)
        return jsonify(status)
    except Exception as e:
        log_message(f"Error getting job status for {job_id}: {e}")
        return jsonify({"job_id": job_id, "status": "error", "error": str(e)}), 500

@bp.route("/store_status/<store>", methods=["GET"])
def get_store_status_route(store):
    """Get processing status for a specific store"""
    try:
        status = get_store_status(store)
        return jsonify({"store": store, **status})
    except Exception as e:
        log_message_with_store(f"Error getting store status: {e}", store)
        return jsonify({"store": store, "error": str(e)}), 500

@bp.route("/all_stores_status", methods=["GET"])
def get_all_stores_status():
    """Get processing status for all stores"""
    try:
        status = celery_store_manager.get_all_stores_status()
        return jsonify(status)
    except Exception as e:
        log_message("Error getting all stores status: " + str(e))
        return jsonify({"error": str(e)}), 500

@bp.route("/cleanup_tasks", methods=["POST"])
def cleanup_tasks():
    """Clean up old completed task records"""
    try:
        data = request.json or {}
        max_age_hours = data.get('max_age_hours', 24)
        
        cleaned = celery_store_manager.cleanup_completed_tasks(max_age_hours)
        
        return jsonify({
            "cleaned_tasks": cleaned,
            "message": f"Cleaned up {cleaned} old task records"
        })
    except Exception as e:
        log_message(f"Error cleaning up tasks: {e}")
        return jsonify({"error": str(e)})

