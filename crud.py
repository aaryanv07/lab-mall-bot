# crud.py
from db import get_connection
from typing import Dict, Any

def get_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def search_products_by_name(query):
    conn = get_connection()
    cursor = conn.cursor()
    search_term = f"%{query}%"
    cursor.execute("SELECT * FROM products WHERE title LIKE %s", (search_term,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# --- SESSION HELPERS ---

def set_user_product_selection(mobile, product_id, item_type='regular'):
    """
    Saves the user's selected product AND its type (regular vs dead_stock)
    to the user_state table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        INSERT INTO user_state (mobile, selected_product_id, item_type) 
        VALUES (%s, %s, %s) 
        ON DUPLICATE KEY UPDATE selected_product_id = %s, item_type = %s
        """
        cursor.execute(query, (mobile, product_id, item_type, product_id, item_type))
        conn.commit()
    except Exception as e:
        print(f"Error saving state: {e}")
    finally:
        cursor.close()
        conn.close()

def get_user_product_selection(mobile):
    """
    Retrieves the selected product ID AND item_type.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT selected_product_id, item_type FROM user_state WHERE mobile = %s", (mobile,))
        row = cursor.fetchone()
        
        if row:
            if isinstance(row, dict):
                return {
                    "product_id": row['selected_product_id'],
                    "item_type": row.get('item_type', 'regular')
                }
            else:
                return {
                    "product_id": row[0],
                    "item_type": row[1] if len(row) > 1 else 'regular'
                }
    except Exception as e:
        print(f"DEBUG: Error fetching state: {e}")
    finally:
        cursor.close()
        conn.close()
    return None

# --- FORMATTING FUNCTIONS ---

# crud.py

# crud.py

def format_single_product_for_whatsapp(p: Dict[str, Any]) -> str:
    if not isinstance(p, dict):
        return "⚠️ Error: Product data format mismatch."

    product_name = p.get('title', 'N/A')
    pack_size = p.get('pack_size', 'N/A')
    code_no = p.get('code_no', 'N/A')
    hsn_code = p.get('hsn_code', 'N/A')
    cas_no = p.get('cas_no', 'N/A')
    make = p.get('make', 'N/A')
    
    # Prices
    list_price = float(p.get('price') or 0)
    labmall_price = float(p.get('labmall_price') or 0)
    tax_percent = float(p.get('tax_percent') or 0)

    # --- PRICE DISPLAY LOGIC ---
    price_section = ""
    
    # 1. Base Price Logic
    if labmall_price > 0 and labmall_price < list_price:
        # Discounted Case
        price_section += f"   ❌ MRP: ~₹{list_price:,.2f}~\n"
        price_section += f"   ✅ *LabMall Price: ₹{labmall_price:,.2f}*\n"
        effective_price = labmall_price
    elif list_price > 0:
        # Standard Case
        price_section += f"   💵 Price: ₹{list_price:,.2f}\n"
        effective_price = list_price
    else:
        # POR Case
        price_section += "   💰 Price: *On Request*\n"
        effective_price = 0

    # 2. Tax Calculation (For display only)
    if effective_price > 0:
        gst_amount = effective_price * (tax_percent / 100)
        final_with_tax = effective_price + gst_amount
        price_section += f"   📊 GST ({tax_percent:.0f}%): ₹{gst_amount:,.2f}\n"
        price_section += f"   🏷️ *Final Unit Price: ₹{final_with_tax:,.2f}* (Incl. Tax)"

    message = [
        f"✅ *Selected Item:* {product_name}",
        "─"*25,
        f"   📦 Pack: {pack_size} | Make: {make}",
        f"   🏷️ Code: {code_no} | HSN: {hsn_code}",
    ]
    
    if cas_no and str(cas_no).strip().lower() not in ['nan', 'none', '', 'n/a']:
        message.append(f"   🧪 CAS: {cas_no}")
        
    message.extend([
        "─"*25,
        price_section,
        "─"*25,
        "🛒 *Reply 'Add to Cart' to confirm.*"
    ])
    
    return "\n".join(message)