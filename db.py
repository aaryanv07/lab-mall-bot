import pymysql
import os
import pymysql.cursors

def get_connection():
    # 1. Get Credentials from the Environment Variables set in your gcloud command
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_name = os.environ.get('DB_NAME')
    
    # 2. Check for Google Cloud Socket (This is what your command sets)
    unix_socket = os.environ.get('INSTANCE_UNIX_SOCKET')
    
    # 3. Localhost Fallback (for testing on your Mac)
    db_host = os.environ.get('DB_HOST', '127.0.0.1')

    # --- SCENARIO A: GOOGLE CLOUD RUN (via Socket) ---
    if unix_socket:
        print(f"🔌 Connecting via Unix Socket: {unix_socket}")
        return pymysql.connect(
            user=db_user,
            password=db_password,
            database=db_name,
            unix_socket=unix_socket,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    # --- SCENARIO B: LOCAL TESTING (via IP) ---
    else:
        print("💻 Connecting via Localhost...")
        return pymysql.connect(
            host=db_host,
            user='root',             # Update if needed for local
            password='Aaryan15512$', # Update if needed for local
            database='shopify',      # Update if needed for local
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

# import pymysql
# import pymysql.cursors

# def get_connection():
#     print("💻 Connecting to LOCAL Database (db.py)...")
    
#     return pymysql.connect(
#         host='127.0.0.1',       # Force Localhost
#         user='root',            # Your Local User
#         password='Aaryan15512$',# Your Local Password
#         database='shopify',   # ✅ Corrected DB Name (was 'shopify')
#         cursorclass=pymysql.cursors.DictCursor,
#         autocommit=True
#     )