import pandas as pd
import pymysql

# --- CONFIGURATION ---
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "Aaryan15512$"
DB_NAME = "shopify"
FILE_NAME = "dead_stock.xlsx" 

def upload_data():
    conn = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, autocommit=True
    )
    cursor = conn.cursor()

    try:
        print(f"📂 Reading {FILE_NAME}...")
        df = pd.read_excel(FILE_NAME)
        
        # 1. FIX HEADERS: Remove hidden spaces (e.g., "Description " -> "Description")
        df.columns = df.columns.str.strip()
        
        print("📊 Found Columns:", list(df.columns)) # <--- CHECK THIS OUTPUT
        
        # 2. Check if 'Description' exists
        if 'Description' not in df.columns:
            print("❌ ERROR: Could not find 'Description' column!")
            print("   Available options are:", list(df.columns))
            return

        # 3. Clean Data (Replace NaN with None)
        df = df.where(pd.notnull(df), None)

        print(f"🚀 Starting upload of {len(df)} rows...")
        
        query = """
            INSERT INTO dead_stock_products 
            (code_no, title, pack_size, make, cas_no, purity, price, qty_available)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        count = 0
        for _, row in df.iterrows():
            # Use 'get' with strict names matching your Excel headers
            code = row.get("Code No")
            title = row.get("Description")  # <--- MUST MATCH EXCEL HEADER
            pack = row.get("Pkg")
            make = row.get("Make")
            cas = row.get("Cas no")
            purity = row.get("NA")
            
            cursor.execute(query, (code, title, pack, make, cas, purity, 0.00, 1))
            count += 1
            
        print(f"✅ Successfully uploaded {count} products!")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    upload_data()