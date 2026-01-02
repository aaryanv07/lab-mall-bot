import pymysql
import pymysql.cursors

# --- CONFIGURATION (Match your db.py) ---
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Aaryan15512$',  # Ensure this matches your local password
    'database': 'shopify',    # Ensure this matches your local database name
    'cursorclass': pymysql.cursors.DictCursor,
    'autocommit': True  # Force auto-save
}

def run_diagnostics():
    print("🕵️‍♂️ STARTING DATABASE DIAGNOSTICS...")
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Connection to 'chemicals' DB successful.")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return

    # TEST 1: Check if 'user_search_cache' table exists
    try:
        cursor.execute("DESCRIBE user_search_cache;")
        columns = [row['Field'] for row in cursor.fetchall()]
        print(f"✅ Table 'user_search_cache' found. Columns: {columns}")
        
        if 'item_type' not in columns:
            print("❌ CRITICAL ERROR: Column 'item_type' is MISSING in user_search_cache.")
    except Exception as e:
        print(f"❌ Table Check Failed: {e}")
        return

    # TEST 2: Check current data in cache
    print("\n📊 CHECKING CURRENT CACHE DATA:")
    cursor.execute("SELECT * FROM user_search_cache LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        print("   -> ⚠️ The cache table is EMPTY. (This explains why Select fails)")
    else:
        for r in rows:
            print(f"   -> Found Row: Mobile={r.get('mobile')} | Index={r.get('result_index')} | Type={r.get('item_type')}")

    # TEST 3: Force a Test Insert (Simulating a Search)
    print("\n🧪 ATTEMPTING TEST INSERT...")
    test_mobile = "9999999999"
    try:
        # Clear old test data
        cursor.execute("DELETE FROM user_search_cache WHERE mobile=%s", (test_mobile,))
        
        # Insert dummy data
        insert_sql = """
            INSERT INTO user_search_cache (mobile, result_index, product_id, item_type)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (test_mobile, 1, 101, 'regular'))
        print(f"   -> Insert executed for mobile {test_mobile}.")
        
        # Verify immediately
        cursor.execute("SELECT * FROM user_search_cache WHERE mobile=%s", (test_mobile,))
        result = cursor.fetchone()
        
        if result:
            print(f"✅ SUCCESS: Data was saved and retrieved! (Found ID: {result['product_id']})")
        else:
            print("❌ FAILURE: Insert executed but SELECT found nothing immediately after.")
            
    except Exception as e:
        print(f"❌ Test Insert Failed: {e}")

    conn.close()
    print("\n🏁 DIAGNOSTICS COMPLETE.")

if __name__ == "__main__":
    run_diagnostics()