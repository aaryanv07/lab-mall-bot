import pandas as pd
import pymysql
from db import get_connection  # Re-uses your existing connection logic

def import_himedia_products():
    print("🚀 Starting Himedia Product Import...")

    # 1. Read the CSV
    try:
        df = pd.read_csv('Merged.csv')
        print(f"   -> Loaded CSV with {len(df)} total rows.")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # 2. Filter for 'Himedia' only
    # We clean whitespace and ignore case just to be safe
    df['Make_Clean'] = df['Make'].astype(str).str.strip().str.lower()
    himedia_df = df[df['Make_Clean'] == 'himedia'].copy()
    
    count = len(himedia_df)
    if count == 0:
        print("⚠️ No products with Make='Himedia' found in the CSV.")
        return
    
    print(f"   -> Found {count} 'Himedia' products to import.")

    # 3. Clean Data (Handle NaN/Empty values)
    himedia_df = himedia_df.fillna('')  # Replace NaNs with empty string
    
    # 4. Connect to Database
    conn = get_connection()
    cursor = conn.cursor()
    
    print("   -> Database connected. Inserting data...")
    
    inserted_count = 0
    skipped_count = 0

    insert_query = """
        INSERT INTO products 
        (code_no, title, cas_no, hsn_code, tax_percent, pack_size, price, make, labmall_price)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        for index, row in himedia_df.iterrows():
            # Prepare values (Extract from CSV columns)
            # CSV Cols: ['Digit Code', 'Product Name', 'CAS No.', 'HSN Code', 'GST', 'Packing', 'Price', 'Make', 'LABMALL PRICE']
            
            code_no = str(row.get('Digit Code', '')).strip()
            title = str(row.get('Product Name', '')).strip()
            cas_no = str(row.get('CAS No.', '')).strip()
            hsn_code = str(row.get('HSN Code', '')).strip()
            
            # Numeric conversion handling
            try:
                tax_percent = float(row.get('GST', 0))
            except:
                tax_percent = 0.0
                
            pack_size = str(row.get('Packing', '')).strip()
            
            try:
                price = float(row.get('Price', 0))
            except:
                price = 0.0
                
            make = str(row.get('Make', 'Himedia')).strip()
            
            try:
                labmall_price = float(row.get('LABMALL PRICE', 0))
            except:
                labmall_price = 0.0

            # Execute Insert
            try:
                cursor.execute(insert_query, (
                    code_no, title, cas_no, hsn_code, tax_percent, 
                    pack_size, price, make, labmall_price
                ))
                inserted_count += 1
            except Exception as e:
                print(f"      ⚠️ Failed to insert row {index}: {e}")
                skipped_count += 1
                
        conn.commit()
        print(f"\n✅ SUCCESS: Imported {inserted_count} Himedia products.")
        if skipped_count > 0:
            print(f"⚠️ Skipped {skipped_count} items due to errors.")
            
    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import_himedia_products()