#!/usr/bin/env python3
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_enums():
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        print("🔧 Convirtiendo columnas String a ENUM...")
        
        # 1. Cambiar columna role de String a ENUM
        cur.execute("""
            ALTER TABLE users 
            ALTER COLUMN role TYPE userrole 
            USING role::userrole;
        """)
        
        # 2. Cambiar columna status de String a ENUM
        cur.execute("""
            ALTER TABLE incidents 
            ALTER COLUMN status TYPE incidentstatus 
            USING status::incidentstatus;
        """)
        
        print("✅ Columnas convertidas a ENUMs")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Error convirtiendo ENUMs: {e}")
        print("💡 Las tablas funcionan con String, continuando...")

if __name__ == "__main__":
    fix_enums()