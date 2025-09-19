from searchcon.search_engine import UniversalSearchEngine
from utils import log_message


def search_by_zip_upc(store, upc="", city="", state="", price="",deal_filter=False,profile="",store_ids=""):
    """
    Simple universal search function
    """
    # Build filters dict
    filters = {}
    
    if upc:
        filters['upc'] = upc
    if city:
        filters['city'] = city
    if state:
        filters['state'] = state
    if price:
        filters['price'] = price
    

    
    # Create search engine and search
    try:
        engine = UniversalSearchEngine(store)
        print(f"STORE SELECTED : {store}")
        return engine.search(filters=filters,deal_filter=deal_filter,profile=profile,store_ids=store_ids)
    except Exception as e:
        log_message(f"Search failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'count': 0,
            'data': [],
            'store': store
        }


