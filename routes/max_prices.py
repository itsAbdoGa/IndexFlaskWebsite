from flask import Blueprint, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config
import csv
import os
from utils import log_message
import time
from core.database import get_db_connection
bp = Blueprint('max_prices', __name__)

# Database connection string
UPLOAD_FOLDER = Config.UPLOAD_FOLDER


@bp.route("/max_prices")
def max_prices():
    """Route for managing UPC max prices"""
    return render_template("max_prices.html")


@bp.route("/get_profiles", methods=["GET"])
def get_profiles():
    """Return all available profiles"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get distinct profiles from the table
            cursor.execute("SELECT DISTINCT profile FROM main.upc_max_prices WHERE profile IS NOT NULL ORDER BY profile")
            
            profiles = [row[0] for row in cursor.fetchall()]            
            
            # Always ensure 'Default' is in the list
            if 'Default' not in profiles:
                profiles.insert(0, 'Default')
            
            return jsonify({'success': True, 'profiles': profiles})
    except Exception as e:
        log_message(f"Error getting profiles: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# NEW ROUTE: Manage profiles (create/delete)
@bp.route("/manage_profile", methods=["POST"])
def manage_profile():
    """Create or delete profiles"""
    try:
        data = request.json
        action = data.get('action')
        profile_name = data.get('profile_name')
        
        if not profile_name:
            return jsonify({'success': False, 'message': 'Profile name is required'}), 400
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if action == 'create':
                copy_from = data.get('copy_from')
                
                # Check if profile already exists
                cursor.execute("SELECT COUNT(*) FROM main.upc_max_prices WHERE profile = %s", (profile_name,))
                if cursor.fetchone()[0] > 0:
                    return jsonify({'success': False, 'message': 'Profile already exists'}), 400
                
                if copy_from:
                    # Copy all records from another profile
                    if copy_from == 'Default':
                        cursor.execute("""
                            INSERT INTO main.upc_max_prices (upc, max_price, description, net, department, productid, profile)
                            SELECT upc, max_price, description, net, department, productid, %s 
                            FROM main.upc_max_prices 
                            WHERE profile IS NULL OR profile = 'Default'
                        """, (profile_name,))
                    else:
                        cursor.execute("""
                            INSERT INTO main.upc_max_prices (upc, max_price, description, net, department, productid, profile)
                            SELECT upc, max_price, description, net, department, productid, %s 
                            FROM main.upc_max_prices 
                            WHERE profile = %s
                        """, (profile_name, copy_from))
                
                conn.commit()
                log_message(f"Profile '{profile_name}' created successfully")
                
            elif action == 'delete':
                if profile_name == 'Default':
                    return jsonify({'success': False, 'message': 'Cannot delete Default profile'}), 400
                
                # Delete all records for this profile
                cursor.execute("DELETE FROM main.upc_max_prices WHERE profile = %s", (profile_name,))
                deleted_count = cursor.rowcount
                conn.commit()
                
                log_message(f"Profile '{profile_name}' deleted with {deleted_count} records")
        
        return jsonify({'success': True})
        
    except Exception as e:
        log_message(f"Error managing profile: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route("/upload_max_prices", methods=["POST"])
def upload_max_prices():
    """Handle CSV file upload for UPC max prices with profile support"""
    try:
        if "file" not in request.files:
            return jsonify({"message": "No file provided"}), 400

        file = request.files["file"]
        profile = request.form.get('profile', 'Default')  # Get profile from form data
        
        if file.filename == "":
            return jsonify({"message": "No selected file"}), 400

        # Save and process the file
        filepath = os.path.join(UPLOAD_FOLDER, "max_prices_" + file.filename)
        file.save(filepath)
        log_message(f"Max prices CSV uploaded for profile '{profile}'. Processing... {filepath}")

        # Process CSV file
        success_count = 0
        error_count = 0

        with get_db_connection() as conn:
            cursor = conn.cursor()

            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = [h.upper() for h in next(reader)]  # Convert headers to uppercase
                
                # Find column indices (case-insensitive matching)
                upc_col = next((i for i, h in enumerate(headers) if h == "UPC"), None)
                price_col = next((i for i, h in enumerate(headers) if h == "PRICE"), None)
                desc_col = next((i for i, h in enumerate(headers) if h == "DESCRIPTION"), None)
                net_col = next((i for i, h in enumerate(headers) if h == "NET"), None)
                dept_col = next((i for i, h in enumerate(headers) if h == "DEPARTMENT"), None)
                product_col = next((i for i, h in enumerate(headers) if h == "PRODUCTID"), None)
                profile_col = next((i for i, h in enumerate(headers) if h == "PROFILE"), None)  # New profile column
                
                if upc_col is None or price_col is None:
                    os.remove(filepath)
                    return jsonify({"message": "CSV must contain UPC and PRICE columns"}), 400
                
                for row in reader:
                    if len(row) <= max(upc_col, price_col):
                        error_count += 1
                        continue
                        
                    upc = row[upc_col].strip()
                    price_str = row[price_col].strip()
                    
                    # Remove currency symbols and clean price string
                    price_str = price_str.replace('$', '').replace('£', '').replace('€', '').strip()
                    
                    # Get profile from CSV or use current profile
                    row_profile = profile  # Default to current profile
                    if profile_col is not None and len(row) > profile_col and row[profile_col].strip():
                        row_profile = row[profile_col].strip()
                    
                    # Convert profile to database format (None for Default)
                    profile_value = row_profile or "Default"
                    
                    # Get optional fields if available
                    description = ""
                    if desc_col is not None and len(row) > desc_col:
                        description = row[desc_col].strip()
                    
                    net = None
                    if net_col is not None and len(row) > net_col and row[net_col].strip():
                        net_str = row[net_col].strip().replace('$', '').replace('£', '').replace('€', '').strip()
                        try:
                            net = float(net_str)
                        except ValueError:
                            pass  # Leave as None if can't convert
                    
                    department = ""
                    if dept_col is not None and len(row) > dept_col:
                        department = row[dept_col].strip()
                    
                    productid = ""
                    if product_col is not None and len(row) > product_col:
                        productid = row[product_col].strip()
                    
                    if not upc or not price_str:
                        error_count += 1
                        continue
                    
                    try:
                        price = float(price_str)
                        
                        # Check if record exists for this UPC and profile using PostgreSQL UPSERT
                        cursor.execute("""
                            INSERT INTO main.upc_max_prices (upc, max_price, description, net, department, productid, profile)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (upc, profile)
                            DO UPDATE SET 
                                max_price = EXCLUDED.max_price,
                                description = EXCLUDED.description,
                                net = EXCLUDED.net,
                                department = EXCLUDED.department,
                                productid = EXCLUDED.productid
                        """, (upc, price, description, net, department, productid, profile_value))
                        
                        success_count += 1
                    except (ValueError, psycopg2.Error) as e:
                        log_message(f"Error processing {upc}: {str(e)}")
                        error_count += 1
            
            conn.commit()
        
        os.remove(filepath)
        
        return jsonify({
            "success": True,
            "count": success_count,
            "message": f"Max prices uploaded successfully to profile '{profile}'. Processed: {success_count}, Errors: {error_count}"
        }), 200
        
    except Exception as e:
        log_message(f"Error uploading max prices: {str(e)}")
        return jsonify({"success": False, "message": f"Error uploading max prices: {str(e)}"}), 500

@bp.route("/manage_max_price", methods=["POST"])
def manage_max_price():
    """Add, update or delete a max price record with profile support"""
    try:
        data = request.json
        action = data.get("action")
        profile = data.get("profile", "Default")  # Get profile from request
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if action == "add":
                upc = data.get("upc")
                price = data.get("price")
                description = data.get("description", "")
                net = data.get("net")
                department = data.get("department", "")
                productid = data.get("productid", "")
                
                if not upc or not price:
                    return jsonify({"success": False, "message": "UPC and price are required"}), 400
                
                try:
                    price = float(price)
                    if net is not None and net != "":
                        net = float(net)
                    else:
                        net = None
                    
                    # Use PostgreSQL UPSERT to handle insert/update
                    cursor.execute("""
                        INSERT INTO main.upc_max_prices (upc, max_price, description, net, department, productid, profile)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (upc, profile)
                        DO UPDATE SET 
                            max_price = EXCLUDED.max_price,
                            description = EXCLUDED.description,
                            net = EXCLUDED.net,
                            department = EXCLUDED.department,
                            productid = EXCLUDED.productid
                    """, (upc, price, description, net, department, productid, profile))
                    
                    conn.commit()
                    
                    return jsonify({
                        "success": True, 
                        "message": f"Max price for UPC {upc} added/updated successfully in profile '{profile}'"
                    }), 200
                except ValueError:
                    return jsonify({
                        "success": False, 
                        "message": "Price and net must be valid numbers"
                    }), 400
                except psycopg2.Error as e:
                    log_message(f"Database error in manage_max_price: {str(e)}")
                    return jsonify({
                        "success": False, 
                        "message": f"Database error: {str(e)}"
                    }), 500
            
            elif action == "delete":
                upc = data.get("upc")
                
                if not upc:
                    return jsonify({"success": False, "message": "UPC is required"}), 400
                
                try:
                    cursor.execute("""
                        DELETE FROM main.upc_max_prices 
                        WHERE upc = %s AND (
                            (profile IS NULL AND %s IS NULL) OR 
                            (profile = %s)
                        )
                    """, (upc, profile, profile))
                    conn.commit()
                    
                    return jsonify({
                        "success": True, 
                        "message": f"Max price for UPC {upc} deleted successfully from profile '{profile}'"
                    }), 200
                except psycopg2.Error as e:
                    log_message(f"Database error in manage_max_price delete: {str(e)}")
                    return jsonify({
                        "success": False, 
                        "message": f"Database error: {str(e)}"
                    }), 500
            
            else:
                return jsonify({
                    "success": False, 
                    "message": "Invalid action"
                }), 400
                
    except Exception as e:
        log_message(f"Error managing max price: {str(e)}")
        return jsonify({
            "success": False, 
            "message": f"Error managing max price: {str(e)}"
        }), 500

@bp.route("/get_max_prices", methods=["GET"])
def get_max_prices():
    """Return UPC max price entries for a specific profile"""
    try:
        profile = request.args.get('profile', 'Default')
        
        with get_db_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if profile == 'Default':
                # Get records with NULL profile or 'Default' profile
                cursor.execute("""
                    SELECT ump.upc, ump.max_price, ump.description, ump.net, ump.department, ump.productid, 
                           COALESCE(ump.profile, 'Default') as profile, i.name 
                    FROM main.upc_max_prices ump
                    LEFT JOIN walmart.items i ON ump.upc = i.upc
                    WHERE ump.profile IS NULL OR ump.profile = 'Default'
                    ORDER BY ump.upc
                """)
            else:
                # Get records for specific profile
                cursor.execute("""
                    SELECT ump.upc, ump.max_price, ump.description, ump.net, ump.department, ump.productid, 
                           ump.profile, i.name 
                    FROM main.upc_max_prices ump
                    LEFT JOIN walmart.items i ON ump.upc = i.upc
                    WHERE ump.profile = %s
                    ORDER BY ump.upc
                """, (profile,))
            
            results = cursor.fetchall()
        
        max_prices = []
        for row in results:
            max_prices.append({
                "upc": row['upc'],
                "max_price": float(row['max_price']) if row['max_price'] is not None else 0.0,
                "description": row['description'],
                "net": float(row['net']) if row['net'] is not None else None,
                "department": row['department'],
                "productid": row['productid'],
                "profile": row['profile'] or 'Default',
                "name": row['name'] if row['name'] else "Unknown Item"
            })
        
        return jsonify(max_prices)
        
    except Exception as e:
        log_message(f"Error getting max prices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/clear_old_items', methods=['POST'])
def clear_old_items():
    """Delete items from database older than specified days"""
    try:
        data = request.json
        days = data.get('days', 30)  # Default to 30 days if not specified
        store = data.get('store')
        
        if not isinstance(days, int) or days < 1:
            return jsonify({"message": "Invalid days parameter. Must be a positive integer.", "success": False}), 400
            
        # Calculate the cutoff timestamp (current time - days)
        cutoff_timestamp = int(time.time()) - (days * 24 * 60 * 60)
        
        # Step 1: Get the list of UPCs to be deleted from olditem table
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT upc FROM main.olditem WHERE timestamp < %s AND store = %s", (cutoff_timestamp,store))
            old_upcs = [row[0] for row in cursor.fetchall()]
            
            # Now delete the old records from olditem
            cursor.execute("DELETE FROM main.olditem WHERE timestamp < %s", (cutoff_timestamp,))
            olditem_deleted = cursor.rowcount
            conn.commit()
        
        log_message(f"Found {len(old_upcs)} unique UPCs to remove")
        
        # Step 2: Delete from other tables in the walmart schema
        items_deleted = 0
        store_items_deleted = 0
                
        if old_upcs:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # First, find all item IDs associated with these UPCs
                cursor.execute("SELECT id FROM walmart.items WHERE upc = ANY(%s)", (old_upcs,))
                item_ids = [row[0] for row in cursor.fetchall()]
                
                # Step 3: Delete from store_items using the item IDs
                if item_ids:
                    cursor.execute("DELETE FROM walmart.store_items WHERE item_id = ANY(%s)", (item_ids,))
                    store_items_deleted = cursor.rowcount
                    
                # Step 4: Finally delete the items from the items table
                cursor.execute("DELETE FROM walmart.items WHERE upc = ANY(%s)", (old_upcs,))
                items_deleted = cursor.rowcount
                
                conn.commit()
        
        log_message(f"Cleared items older than {days} days: {olditem_deleted} old items, {items_deleted} items, {store_items_deleted} store items")
        
        return jsonify({
            "message": f"Successfully removed {olditem_deleted} old items, {items_deleted} items, {store_items_deleted} store items older than {days} days for store {store}",
            "success": True,
            "olditem_deleted": olditem_deleted,
            "items_deleted": items_deleted,
            "store_items_deleted": store_items_deleted,
        })
        
    except Exception as e:
        log_message(f"Error clearing old items: {str(e)}")
        return jsonify({"message": f"Error: {str(e)}", "success": False}), 500