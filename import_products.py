# import pandas as pd
# import pymysql

# # 1. Load the CSV
# # Make sure your file is actually named 'products.csv' and is in the same folder
# try:
#     df = pd.read_csv('Products.csv')
# except FileNotFoundError:
#     print("❌ Error: 'products.csv' file not found. Please export your Excel to CSV first.")
#     exit()

# # 2. Connect to DB using PyMySQL
# try:
#     conn = pymysql.connect(
#         host="localhost",
#         user="bot",
#         password="Aaryan15512$",
#         database="shopify",      # ⚠️ Check if this is 'chemicals' or 'shopify' (your error log said shopify)
#         cursorclass=pymysql.cursors.DictCursor
#     )    
#     print("✅ Connected to database successfully.")
# except Exception as e:
#     print(f"❌ Connection failed: {e}")
#     exit()

# cursor = conn.cursor()

# # 3. Iterate and Insert
# success_count = 0
# error_count = 0

# for index, row in df.iterrows():
#     try:
#         # DATA CLEANING: Handle price text logic inside Python to be safe
#         raw_price = row.get('List Price (01-04-2025)', 0)
#         try:
#             # Remove commas and convert to float. If fail, default to 0.
#             clean_price = float(str(raw_price).replace(',', '').replace('On Request', '0').strip())
#         except:
#             clean_price = 0.0

#         # SQL Query
#         sql = """
#             INSERT INTO products (code_no, title, pack_size, make, hsn_code, tax_percent, price) 
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#         """
        
#         # Prepare values (using .get() avoids crash if column name mismatches slightly)
#         val = (
#             row.get('Code No'), 
#             row.get('Description'), 
#             row.get('Pack Size'), 
#             row.get('Make'), 
#             row.get('HSN Code'), 
#             row.get('Tax %'), 
#             clean_price
#         )
        
#         cursor.execute(sql, val)
#         success_count += 1

#     except Exception as e:
#         print(f"⚠️ Error inserting row {index + 1}: {e}")
#         error_count += 1

# conn.commit()
# cursor.close()
# conn.close()

# print(f"\n🎉 Done! Imported {success_count} products. Failed: {error_count}")

import pandas as pd
import pymysql
import os

# --- CONFIGURATION ---
CSV_FILENAME = "Merged.csv"  # Name of your new file
DB_HOST = "localhost",
DB_USER = "bot",
DB_PASS = "Aaryan15512$",
DB_NAME = "shopify",      # ⚠️ Check if this is 'chemicals' or 'shopify' (your error log said shopify)

def update_database():
    print(f"🚀 Starting database update from {CSV_FILENAME}...")

    # 1. Load the CSV
    try:
        df = pd.read_csv(CSV_FILENAME)
        # Normalize headers: strip spaces to avoid "Code " vs "Code" errors
        df.columns = [c.strip() for c in df.columns]
        print(f"✅ Loaded {len(df)} rows.")
        print(f"   Columns found: {list(df.columns)}")
    except FileNotFoundError:
        print("❌ Error: CSV file not found.")
        return

    # 2. Connect to Database
    # --- ADD THESE LINES FOR DEBUGGING ---
    print("\n🔥 DEBUGGING HEADERS:")
    print(list(df.columns))
# --- END DEBUGGING ---
    try:
        conn = pymysql.connect(
            host="localhost",
            user="bot",
            password="Aaryan15512$",
            database="shopify",      # ⚠️ Check if this is 'chemicals' or 'shopify' (your error log said shopify)
            cursorclass=pymysql.cursors.DictCursor
        )
        cursor = conn.cursor()
        print("✅ Connected to database.")
    except Exception as e:
        print(f"❌ DB Connection Failed: {e}")
        return

    # 3. Insert Data
   # 3. Insert Data
   # 3. Insert Data
    # 3. Insert Data
    success_count = 0
    error_count = 0
    
    # ... (omitted print and TRUNCATE for brevity) ...

    for index, row in df.iterrows():
        try:
            # CLEANING: Handle prices that might be strings or empty
            def clean_price(val):
                # Ensure we handle the 'nan' on the last line gracefully
                if pd.isna(val) or str(val).strip() == '': return 0.0
                return float(str(val).replace(',', '').replace('On Request', '0'))

            # --- CORRECTED HEADER MAPPING ---
            # NOTE: Your CSV List Price is under 'Price', not 'Unit Rate'
            list_price = clean_price(row.get('Price')) 
            lab_price = clean_price(row.get('LABMALL PRICE')) # Exact match to your CSV header

            sql = """
                INSERT INTO products 
                (code_no, title, cas_no, hsn_code, tax_percent, pack_size, price, make, labmall_price) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            val = (
                row.get('Digit Code'),    # Maps to code_no
                row.get('Product Name'),  # Maps to title
                row.get('CAS No.'),       # Maps to cas_no
                row.get('HSN Code'),      # Maps to hsn_code
                row.get('GST'),           # Maps to tax_percent
                row.get('Packing'),       # Maps to pack_size
                list_price,               # Maps to price (List Price)
                row.get('Make'),          # Maps to make
                lab_price                 # Maps to labmall_price (NEW)
            )
            
            cursor.execute(sql, val)
            success_count += 1

        except Exception as e:
            error_count += 1
            if error_count < 5: 
                print(f"⚠️ Error row {index}: {e}")
            elif error_count == 5:
                print("... Suppressing further error messages.")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n🎉 Finished! Imported {success_count} products.")
    print(f"⚠️ Failed rows: {error_count}")

if __name__ == "__main__":
    update_database()


