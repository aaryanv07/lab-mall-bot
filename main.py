from fastapi import FastAPI, Query, Request
# from fastapi.staticfiles import StaticFiles
from db import get_connection
import time
import pymysql
from typing import List, Dict, Any, Optional

from crud import (
    get_user_product_selection,
    get_products,
    search_products_by_name,
    set_user_product_selection,
    format_single_product_for_whatsapp
)

app = FastAPI()

# ⚠️ REPLACE with your actual Cloud Run URL
BASE_URL = "https://lab-mall-service-969631280514.us-central1.run.app"
user_sessions = {}

# --- HELPER: NORMALIZE MOBILE ---
def normalize_mobile(val: Any) -> str:
    """Standardizes phone numbers to prevent mismatches (+91 vs 91)"""
    if not val:
        return ""
    return str(val).replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "").strip()

# ==========================================
# 🔍 SEARCH ENDPOINTS (UNCHANGED)
# ==========================================

@app.get("/products")
def products():
    return get_products()

@app.get("/search_products/")
def search_products(q: str = Query(...)):
    return search_products_by_name(q)

@app.post("/fulltext_search_products")
async def fulltext_search_products(request: Request):
    data = await request.json()
    
    # 1. Priority Extraction (Mobile vs Query)
    raw_user_id = data.get("mobile") or data.get("user_id")
    raw_search = data.get("choice") or data.get("q")

    # Bot fallback logic
    if data.get("query"):
        val = str(data.get("query")).strip()
        val_clean = normalize_mobile(val)
        if not raw_user_id and val_clean.isdigit() and len(val_clean) >= 10:
            raw_user_id = val
        elif not raw_search:
            raw_search = val

    user_id = normalize_mobile(raw_user_id) or "unknown_user"
    user_input = str(raw_search or "").strip()

    if not user_input or user_input.lower() == 'none':
        return {"message": "👋 Hello! Please type a chemical name to search."}

    # 2. Pagination & Search Query Logic (FIXED)
    ITEMS_PER_PAGE = 5
    session = user_sessions.get(user_id, {})
    current_offset = session.get("offset", 0)
    clean_input = user_input.lower().strip()
    
    # Check if user wants the next page
    if clean_input in ["next", "next list", "more"]:
        # Retrieve the previous search term from session
        search_query = session.get("search_query")
        if not search_query:
            return {"message": "⚠️ Session expired. Please search for the chemical again."}
        # Move to next page
        current_offset += ITEMS_PER_PAGE
    else:
        # This is a NEW search
        search_query = user_input
        current_offset = 0 # Reset offset for new search

    conn = get_connection()
    cursor = conn.cursor()

    # 3. SQL Query Construction (Using 'search_query', NOT 'user_input')
    # If we used user_input here, typing "Next" would search the DB for the word "Next"
    safe_query = "%" + search_query.replace('%', '').strip() + "%"
    fulltext_query = " ".join([f'"{q}"' for q in search_query.split()])
    
    try:
        query = f"""
        SELECT id, code_no, title, pack_size, make, hsn_code, tax_percent, price, labmall_price, cas_no
        FROM products
        WHERE MATCH(title, code_no) AGAINST (%s IN BOOLEAN MODE)
           OR (code_no LIKE %s OR title LIKE %s OR cas_no LIKE %s)
        ORDER BY (make LIKE '%%Loba%%') DESC, title ASC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (
            fulltext_query, 
            safe_query, safe_query, safe_query, 
            ITEMS_PER_PAGE, current_offset
        ))
        results = cursor.fetchall()

        # 4. Save to Cache (Corrected User ID usage)
        if results:
            cursor.execute("DELETE FROM user_search_cache WHERE mobile=%s", (user_id,))
            insert_query = "INSERT INTO user_search_cache (mobile, result_index, product_id, item_type) VALUES (%s, %s, %s, 'regular')"
            for i, p in enumerate(results, start=current_offset + 1):
                cursor.execute(insert_query, (user_id, i, p['id']))
            conn.commit()

    except Exception as e:
        print(f"Search Error: {e}")
        return {"message": "❌ Search Error. Please try again."}
    finally:
        cursor.close()
        conn.close()

    if not results:
        if current_offset > 0: return {"message": "🏁 End of list."}
        return {"message": f"🤷‍♂️ No products found for '{search_query}'."}

    # 5. Update Session (Save 'search_query' for next time)
    user_sessions[user_id] = {"offset": current_offset, "search_query": search_query}
    
    # 6. Format Response
    # The variable 'search_query' is now correctly defined above
    message_lines = [f"🔍 *Results for '{search_query}'*\n"]
    
    for i, p in enumerate(results, start=current_offset + 1):
        list_price = float(p.get('price') or 0)
        labmall_price = float(p.get('labmall_price') or 0)
        make = p.get('make', 'N/A')
        pack = p.get('pack_size', 'N/A')
        title_short = p['title'][:35] + "..." if len(p['title']) > 35 else p['title']

        # Price Display Logic
        if labmall_price > 0 and labmall_price < list_price:
            price_display = f"₹{labmall_price:,.0f} (MRP ~₹{list_price:,.0f}~)"
        elif list_price > 0:
            price_display = f"₹{list_price:,.0f}"
        else:
            price_display = "On Request"

        message_lines.append(f"{i}. *{title_short}*")
        message_lines.append(f"   📦 {pack} | {make} | 🏷️ {price_display}")
        
    message_lines.append("\n*Reply with the item number (e.g., '1') to select.*")
    
    if len(results) == ITEMS_PER_PAGE:
        message_lines.append(f"💡 Reply 'Next List' for more.")

    return {"message": "\n".join(message_lines)}

@app.post("/fulltext_search_dead_stock")
async def fulltext_search_dead_stock(request: Request):
    data = await request.json()
    raw_user_id = data.get("mobile") or data.get("user_id") or data.get("query")
    raw_search = data.get("choice") or data.get("q")
    
    if data.get("query") and not raw_user_id:
        val = normalize_mobile(data.get("query"))
        if val.isdigit() and len(val) >= 10: raw_user_id = val

    user_id = normalize_mobile(raw_user_id)
    user_input = str(raw_search or "").strip()
    
    if not user_input or user_input.lower() == 'none':
        return {"message": "🏚️ Clearance Stock Search: Please type a chemical name."}

    ITEMS_PER_PAGE = 5
    session = user_sessions.get(user_id, {})
    current_offset = session.get("offset", 0)
    
    if user_input.lower() not in ["next", "next list", "more"]:
         if session.get("search_query") != user_input:
             current_offset = 0

    conn = get_connection()
    cursor = conn.cursor()

    try:
        search_words = user_input.split()
        params = []
        title_conditions = []
        for w in search_words:
            title_conditions.append("title LIKE %s")
            params.append(f"%{w}%")
        title_clause = "(" + " OR ".join(title_conditions) + ")"
        full_where_clause = f"({title_clause} OR cas_no LIKE %s OR code_no LIKE %s)"
        
        sql = f"""
            SELECT id, title, pack_size, make, purity, cas_no 
            FROM dead_stock_products 
            WHERE {full_where_clause}
            ORDER BY (title LIKE %s) DESC, title ASC 
            LIMIT %s OFFSET %s
        """
        params.extend([f"%{user_input}%", f"%{user_input}%", f"%{user_input}%", ITEMS_PER_PAGE, current_offset])

        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()

        if results:
            cursor.execute("DELETE FROM user_search_cache WHERE mobile=%s", (user_id,))
            insert_query = "INSERT INTO user_search_cache (mobile, result_index, product_id, item_type) VALUES (%s, %s, %s, 'dead_stock')"
            for i, p in enumerate(results, 1):
                cursor.execute(insert_query, (user_id, current_offset + i, p['id']))
            conn.commit()

    except Exception as e:
        return {"message": "❌ Search failed. Please try again."}
    finally:
        cursor.close()
        conn.close()

    if not results:
        if current_offset > 0: return {"message": "🏁 End of list."}
        return {"message": f"🚫 No items found for '{user_input}'."}

    user_sessions[user_id] = {"search_query": user_input, "offset": current_offset + ITEMS_PER_PAGE}

    message_lines = [f"🏚️ *Results for '{user_input}'*\n"]
    for i, p in enumerate(results, 1):
        message_lines.append(f"{current_offset + i}. *{p['title']}*")
        message_lines.append(f"   📦 {p['pack_size']} | 🧪 {p.get('purity','N/A')}")
        message_lines.append(f"   💰 Price: *On Request*")
        message_lines.append("   " + "-"*15)
        
    return {"message": "\n".join(message_lines)}


# ==========================================
# 🛒 SELECTION ENDPOINTS (UNCHANGED)
# ==========================================

@app.post("/select-fresh")
async def select_fresh(request: Request):
    return await _handle_selection(request, required_type='regular')

@app.post("/select-dead-stock")
async def select_dead_stock(request: Request):
    return await _handle_selection(request, required_type='dead_stock')

async def _handle_selection(request: Request, required_type: str):
    data = await request.json()
    raw_user_id = data.get("mobile") or data.get("user_id") or data.get("query")
    user_id = normalize_mobile(raw_user_id)
    choice = str(data.get("choice") or data.get("q") or "").strip()

    if not choice.isdigit():
        return {"message": "🔢 Please reply with the Item Number (e.g., '1')"}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT product_id, item_type FROM user_search_cache WHERE mobile=%s AND result_index=%s", (user_id, choice))
        selection = cursor.fetchone()
        
        if not selection:
             return {"message": "⚠️ Invalid selection. Please search again."}

        cached_type = selection.get('item_type') if isinstance(selection, dict) else selection[1]
        cached_type = cached_type or 'regular'
        
        if cached_type != required_type:
            target = "Clearance Stock" if required_type == "dead_stock" else "Regular Stock"
            return {"message": f"❌ This item is not in {target}."}

        product_id = selection.get('product_id') if isinstance(selection, dict) else selection[0]

        if required_type == 'dead_stock':
            cursor.execute("SELECT * FROM dead_stock_products WHERE id=%s", (product_id,))
            product = cursor.fetchone()
            reply = (f"✅ *Selected Clearance Item:*\n🧪 {product['title']}\n📦 {product['pack_size']}\n💰 Price: *On Request*\n"
                     f"{'─' * 20}\n🛒 *Reply 'Add to Cart' to confirm.*")
        else:
            cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
            product = cursor.fetchone()
            reply = format_single_product_for_whatsapp(product)

        set_user_product_selection(user_id, product_id, required_type)
        return {"message": reply}

    finally:
        cursor.close()
        conn.close()


# =========================================================
# 🛍️ NEW SEPARATE CART ENDPOINTS
# =========================================================

# --- 1. FRESH STOCK CART ---

@app.post("/add-to-cart-fresh")
async def add_to_cart_fresh(request: Request):
    return await _handle_add_to_cart(request, table_name='cart_fresh', required_type='regular')

@app.post("/view-cart-fresh")
async def view_cart_fresh(request: Request):
    return await _handle_view_cart(request, table_name='cart_fresh', is_fresh=True)

@app.post("/remove-item-fresh")
async def remove_item_fresh(request: Request):
    return await _handle_remove_item(request, table_name='cart_fresh')

@app.post("/checkout-fresh")
async def checkout_fresh(request: Request):
    return await _handle_checkout_fresh(request)


# --- 2. DEAD STOCK CART ---

@app.post("/add-to-cart-dead-stock")
async def add_to_cart_dead_stock(request: Request):
    return await _handle_add_to_cart(request, table_name='cart_dead_stock', required_type='dead_stock')

@app.post("/view-cart-dead-stock")
async def view_cart_dead_stock(request: Request):
    return await _handle_view_cart(request, table_name='cart_dead_stock', is_fresh=False)

@app.post("/remove-item-dead-stock")
async def remove_item_dead_stock(request: Request):
    return await _handle_remove_item(request, table_name='cart_dead_stock')

@app.post("/checkout-dead-stock")
async def checkout_dead_stock(request: Request):
    return await _handle_checkout_dead(request)


# =========================================================
# ⚙️ SHARED LOGIC FUNCTIONS
# =========================================================

async def _handle_add_to_cart(request: Request, table_name: str, required_type: str):
    data = await request.json()
    raw_id = data.get("mobile") or data.get("query")
    user_id = normalize_mobile(raw_id)
    qty = int(data.get("qty", 1))

    # Get Last Selection
    selection = get_user_product_selection(user_id)
    
    if not selection or selection.get('item_type') != required_type:
        return {"message": "❌ Please select a valid product first."}

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if item exists in THIS specific cart table
        query_check = f"SELECT qty FROM {table_name} WHERE mobile=%s AND product_id=%s"
        cursor.execute(query_check, (user_id, selection['product_id']))
        row = cursor.fetchone()
        
        if row:
            new_qty = (row['qty'] if isinstance(row, dict) else row[0]) + qty
            cursor.execute(f"UPDATE {table_name} SET qty=%s WHERE mobile=%s AND product_id=%s", 
                           (new_qty, user_id, selection['product_id']))
        else:
            cursor.execute(f"INSERT INTO {table_name} (mobile, product_id, qty) VALUES (%s, %s, %s)", 
                           (user_id, selection['product_id'], qty))
        conn.commit()
        
        label = "Clearance Cart" if required_type == "dead_stock" else "Fresh Stock Cart"
        return {"message": f"✅ Added to {label}!\n👇 Reply 'View Cart' to see list."}
    
    finally:
        cursor.close()
        conn.close()

async def _handle_view_cart(request: Request, table_name: str, is_fresh: bool):
    data = await request.json()
    user_id = normalize_mobile(data.get("mobile") or data.get("query"))
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Select correct table
        prod_table = "products" if is_fresh else "dead_stock_products"
        label = "FRESH STOCK CART" if is_fresh else "CLEARANCE LIST"
        
        query = f"""
        SELECT c.qty, p.title, p.pack_size, p.price, p.labmall_price, p.tax_percent
        FROM {table_name} c
        JOIN {prod_table} p ON c.product_id = p.id
        WHERE c.mobile = %s
        ORDER BY c.added_at ASC
        """
        cursor.execute(query, (user_id,))
        items = cursor.fetchall()
        
        if not items:
            return {"message": f"🛒 Your {label.title()} is empty."}

        message = f"🛒 *{label}*\n\n"
        cart_total_excl_tax = 0.0
        cart_total_tax = 0.0
        cart_final_total = 0.0
        
        for i, item in enumerate(items, 1):
            qty = item['qty']
            tax_pct = float(item.get('tax_percent') or 0)
            
            # Price Logic
            list_price = float(item.get('price') or 0)
            labmall_price = float(item.get('labmall_price') or 0)
            
            # Determine Base Rate
            if labmall_price > 0 and labmall_price < list_price:
                base_rate = labmall_price
                rate_str = f"₹{labmall_price:,.0f} (MRP ~₹{list_price:,.0f}~)"
            else:
                base_rate = list_price
                rate_str = f"₹{list_price:,.0f}"

            if base_rate > 0:
                # Math
                line_base_amt = base_rate * qty
                line_tax_amt = line_base_amt * (tax_pct / 100)
                line_total = line_base_amt + line_tax_amt
                
                # Accumulate
                cart_total_excl_tax += line_base_amt
                cart_total_tax += line_tax_amt
                cart_final_total += line_total
                
                message += f"{i}. *{item['title']}*\n"
                message += f"   Qty: {qty} x {rate_str}\n"
                message += f"   Tax: {tax_pct:.0f}% (₹{line_tax_amt:,.2f})\n"
                message += f"   *Item Total: ₹{line_total:,.2f}*\n"
            else:
                message += f"{i}. *{item['title']}*\n   Qty: {qty} | Price: On Request\n"

        message += "─"*20 + "\n"
        
        if is_fresh and cart_final_total > 0:
            message += f"🏷️ Total (Excl. Tax): ₹{cart_total_excl_tax:,.2f}\n"
            message += f"📊 Total GST: ₹{cart_total_tax:,.2f}\n"
            message += f"💵 *Payable Amount: ₹{cart_final_total:,.2f}*\n"
        
        action = "Checkout" if is_fresh else "Submit Quote"
        message += f"\n👇 Reply '{action}' to proceed."
        return {"message": message}

    finally:
        cursor.close()
        conn.close()
async def _handle_remove_item(request: Request, table_name: str):
    data = await request.json()
    user_id = normalize_mobile(data.get("mobile"))
    item_no_str = str(data.get("item_no")).strip()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get items ordered by time to match view cart index
        cursor.execute(f"SELECT product_id FROM {table_name} WHERE mobile=%s ORDER BY added_at ASC", (user_id,))
        items = cursor.fetchall()
        
        try:
            index = int(item_no_str) - 1
            if index < 0 or index >= len(items): raise ValueError
            
            item = items[index]
            pid = item['product_id'] if isinstance(item, dict) else item[0]
            
            cursor.execute(f"DELETE FROM {table_name} WHERE mobile=%s AND product_id=%s", (user_id, pid))
            conn.commit()
            return {"message": f"✅ Item #{item_no_str} removed."}
        except ValueError:
            return {"message": "⚠️ Invalid item number."}
    finally:
        cursor.close()
        conn.close()

async def _handle_checkout_fresh(request: Request):
    data = await request.json()
    user_id = normalize_mobile(data.get("mobile") or data.get("query"))
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        SELECT c.qty, p.price, p.labmall_price, p.tax_percent
        FROM cart_fresh c JOIN products p ON c.product_id = p.id
        WHERE c.mobile = %s
        """
        cursor.execute(query, (user_id,))
        items = cursor.fetchall()
        
        if not items: return {"message": "⚠️ Your cart is empty."}

        total_payable = 0.0
        
        # Exact same math as View Cart to ensure consistency
        for item in items:
            qty = item['qty']
            tax_pct = float(item.get('tax_percent') or 0)
            
            list_price = float(item.get('price') or 0)
            labmall_price = float(item.get('labmall_price') or 0)
            
            # Use LabMall price if available and lower, else List Price
            base_rate = labmall_price if (labmall_price > 0 and labmall_price < list_price) else list_price
            
            if base_rate > 0:
                line_base = base_rate * qty
                line_tax = line_base * (tax_pct / 100)
                total_payable += (line_base + line_tax)

        order_id = f"ORD-{int(time.time())}"
        cursor.execute("INSERT INTO orders (order_id, mobile, total_amount, payment_status) VALUES (%s, %s, %s, 'PENDING')",
                       (order_id, user_id, total_payable))
        
        # Clear Cart
        cursor.execute("DELETE FROM cart_fresh WHERE mobile=%s", (user_id,))
        conn.commit()

        msg = f"✅ *Order Created!* (ID: {order_id})\n💵 *Net Payable: ₹{total_payable:,.2f}* (Inc. GST)\n👇 Scan QR to Pay."
        return {"message": msg, "media_url": f"{BASE_URL}/static/payment_qr.jpg"}
    finally:
        cursor.close()
        conn.close()

async def _handle_checkout_dead(request: Request):
    data = await request.json()
    user_id = normalize_mobile(data.get("mobile") or data.get("query"))
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT count(*) as cnt FROM cart_dead_stock WHERE mobile=%s", (user_id,))
        row = cursor.fetchone()
        count = row['cnt'] if isinstance(row, dict) else row[0]
        
        if count == 0: return {"message": "⚠️ Your list is empty."}
        
        cursor.execute("DELETE FROM cart_dead_stock WHERE mobile=%s", (user_id,))
        conn.commit()
        
        return {"message": f"📄 *Quote Request Sent!*\nItems: {count}\n📞 We will contact you shortly."}
    finally:
        cursor.close()
        conn.close()