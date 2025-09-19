from flask import Blueprint, render_template, request, Response,jsonify
from core.search import search_by_zip_upc
from core.database import get_db_connection
from utils import get_size_kb
import csv
import io
from io import StringIO
from searchcon.search_config import SEARCH_CONFIGS

bp = Blueprint('main', __name__)




@bp.route("/", methods=["GET", "POST"])
def index():
    """Debug version with detailed logging"""
    
    
        
        

    results = None
    price = ""
    deal_filter = False

    if request.method == "POST":
                
        price = request.form.get("price", "")
        deal_filter = request.form.get("deal_filter") == "on"
        profile = request.form.get("profile")
        remove_zero_inventory = request.form.get("remove_zero_inventory") == "on"
        stores  = request.form.getlist('stores')
        upc = request.form.get("upc")
        city = request.form.get("city", "")
        state = request.form.get("state", "")
        file = request.files.get("store_ids_csv","")
        store_ids=""
        
        
        if file:
            # Read the CSV content as text
            content = file.read().decode("utf-8")
            # Convert to a CSV reader
            csv_reader = csv.reader(StringIO(content))
            next(csv_reader, None)
            
            store_ids = [int(row[0]) for row in csv_reader if row]
        
        
        if remove_zero_inventory:
            print("Processing zero inventory removal...")
            with get_db_connection() as conn:
                for store in stores:
                    if store == "walmart":
                        cursor = conn.cursor()
                        cursor.execute("""
                            DELETE FROM walmart.store_items 
                            WHERE salesfloor = 0 AND backroom = 0
                        """)
                        
                    else:
                        conf = SEARCH_CONFIGS[store]
                        cursor = conn.cursor()
                        cursor.execute(f"SET search_path TO {conf['schema']};")

                        cursor.execute("""
                            DELETE FROM store_items 
                            WHERE storestock = 0 
                        """)
                        cursor.execute("""
                            DELETE FROM store_items 
                            WHERE storestock = 0 
                        """)
                        deleted_count = cursor.rowcount
                        conn.commit()
                        print(f"Deleted {deleted_count} items with zero inventory from {store}")                                
                
                
                

        print(f"Single search params - UPC: {upc}, City: {city}, State: {state}")
        full_results = []
        for store in stores:
            search = search_by_zip_upc(store,upc, city, state, price, deal_filter,profile,store_ids)
            results = search["data"]
            results = [(store,) + t for t in results]
            full_results.append(results)
            
        results_size_kb = get_size_kb(full_results)
        print(f"Single search found: {results_size_kb} KB worth of data")
        
        # Prepare CSV export for single search
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
                "Store","Address", "City","State",  
                "Zipcode", "Store ID","Name","UPC",
                "Productid","Price","Salesfloor", "Backroom",
                "Aisles","Max Price Noted", "Description", "Net",
                "Department"
            ])

        for data in full_results:
            for row in data:
                if row[0] == "walmart":
                    writer.writerow([
                    row[0],row[1],row[2],row[3],
                    row[4],row[5],row[6],row[7],
                    row[8],row[9],row[10],row[11],
                    row[12],row[13],row[14],row[15],
                    row[16]
                    ])
                else:
                    writer.writerow([
                        row[0],row[1],row[2],row[3],
                        row[4],row[5],row[6],row[7],
                        row[8],row[9],row[10],None,
                        None,row[11],row[12],row[13],
                        row[14]  
                    ])
          
        output.seek(0)  
        # Generate filename for single search
        filename = f"search_results"
        

        filters = []
        for store in stores:
            filters.append(store)
        if upc:
            filters.append(f"UPC_{upc}")
        if city:
            filters.append(f"City_{city}")
        if state:
            filters.append(f"State_{state}")
        if price:
            filters.append(f"Price_{price}")
        if deal_filter:
            filters.append("DealsOnly")

        if filters:
            filename += "_" + "_".join(filters)

        filename += ".csv"

        print(f"Returning single search CSV: {filename}")

        return Response(
            output.getvalue(), 
            mimetype="text/csv", 
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    
    return render_template("index.html", results=results, price=price)


@bp.route("/get_states")
def get_states():
    """API endpoint to get states by store for dynamic form updates"""
    stores  = request.args.getlist('stores')
    print(f"stores: {stores}")
    if not stores:
        return jsonify([])

    try:
        all_states = None  # will hold intersection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for store in stores:
                conf = SEARCH_CONFIGS.get(store)
                schema = conf.get('schema') if conf else None
                
                if not schema:
                    continue
                
                cursor.execute(f'SET search_path TO "{schema}";')
                cursor.execute("""
                    SELECT DISTINCT s.state 
                    FROM stores s 
                    INNER JOIN store_items si ON s.id = si.store_id 
                    WHERE s.state IS NOT NULL AND s.state != ''
                    ORDER BY s.state
                """)
                states = {row[0] for row in cursor.fetchall()}  # set for easy intersection
                
                if all_states is None:
                    all_states = states
                else:
                    all_states &= states  # keep only states in all stores
        
        return jsonify(sorted(all_states)) if all_states else jsonify([])
    except Exception as e:
        print(f"Error fetching states for stores {stores}: {e}")
        return jsonify([])


@bp.route("/get_cities")
def get_cities():
    """API endpoint to get cities by state and multiple stores"""
    state = request.args.get("state")
    stores = request.args.getlist("stores")  # list of stores

    if not state or not stores:
        return jsonify([])

    try:
        all_cities = None

        with get_db_connection() as conn:
            cursor = conn.cursor()

            for store in stores:
                conf = SEARCH_CONFIGS.get(store)
                schema = conf.get('schema') if conf else None

                if not schema:
                    continue

                cursor.execute(f'SET search_path TO "{schema}";')
                cursor.execute("""
                    SELECT DISTINCT s.city
                    FROM stores s
                    INNER JOIN store_items si ON s.id = si.store_id
                    WHERE s.state = %s AND s.city IS NOT NULL AND s.city != ''
                    ORDER BY s.city
                """, (state,))
                cities = {row[0] for row in cursor.fetchall()}

                if all_cities is None:
                    all_cities = cities
                else:
                    all_cities &= cities  # intersection

        return jsonify(sorted(all_cities)) if all_cities else jsonify([])

    except Exception as e:
        print(f"Error fetching cities for {stores} in {state}: {e}")
        return jsonify([])
