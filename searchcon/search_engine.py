from core.database import get_db_connection
from utils import log_message
from .search_config import SEARCH_CONFIGS

class UniversalSearchEngine:
    """Simple universal search engine"""
    
    def __init__(self, store_name):
        self.store_name = store_name.lower()        
        if self.store_name not in SEARCH_CONFIGS:
            raise ValueError(f"Store '{store_name}' not supported. Available: {list(SEARCH_CONFIGS.keys())}")
        
        self.config = SEARCH_CONFIGS[self.store_name]
    
    def search(self, filters=None, deal_filter=False,profile="",store_ids=""):
        """Simple search method"""
        if filters is None:
            filters = {}
        
        # Build query
        select_fields = self.config['select_fields'][:]
        from_clause = " ".join(self.config['joins'])
        where_conditions = []
        params = []
        from_clause += f" {self.config['deal_join']}"
        # Add deal filter
        if deal_filter:
            where_conditions.append(self.config['deal_condition'])
            

        
        # Add search filters
        for field_name, value in filters.items():
            if value and field_name in self.config['fields']:
                db_field, _ = self.config['fields'][field_name]
                
                # Handle different filter types
                if isinstance(value, list):
                    placeholders = ','.join(['%s' for _ in value])
                    where_conditions.append(f"{db_field} IN ({placeholders})")
                    params.extend(value)
                elif field_name in ['price', 'msrp', 'list_price']:  # Price comparison
                    where_conditions.append(f"{db_field} <= %s")
                    params.append(float(value))
                else:  # Exact match
                    where_conditions.append(f"{db_field} = %s ")
                    params.append(value)
        
        query = f"SELECT {', '.join(select_fields)} FROM {from_clause}"
        
        if profile:
            where_conditions.append("ump.profile = %s")
            params.append(profile)
        if store_ids:
            where_conditions.append("s.id = ANY(%s)")
            params.append(store_ids)
        
        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"
        
        
        print(query)
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                
            return {
                'success': True,
                'count': len(results),
                'data': results,
                'query': query,  
                'store': self.store_name
            }
            
        except Exception as e:
            log_message(f"Search error for {self.store_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'count': 0,
                'data': [],
                'store': self.store_name
            }
    