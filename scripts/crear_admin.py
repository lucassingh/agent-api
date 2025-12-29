#!/usr/bin/env python3
"""
CREAR ADMIN - SOLUCIÓN DEFINITIVA
"""
import sys
import os

# Añadir el path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from passlib.context import CryptContext

def crear_admin():
    try:
        # CONFIGURACIÓN - AJUSTA ESTO CON TUS DATOS
        DATABASE_URL = "postgresql://agent_user:agent_password@db:5432/agent_db"
        
        print("Conectando a la base de datos...")
        engine = create_engine(DATABASE_URL)
        pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
        
        with engine.begin() as conn:  # begin() hace commit automático
            # 1. Verificar si ya existe
            result = conn.execute(
                text("SELECT id, email, role FROM users WHERE email = :email"),
                {"email": "admin@agent.com"}
            )
            
            if user := result.fetchone():
                print(f"✅ Admin ya existe:")
                print(f"   ID: {user[0]}")
                print(f"   Email: {user[1]}")
                print(f"   Rol: {user[2]}")
                return
            
            # 2. Crear hash de la contraseña
            password = "Admin@1234"
            hashed_pw = pwd_context.hash(password)
            print(f"Hash creado correctamente")
            
            # 3. INSERT DIRECTO - usando 'admin' en MINÚSCULAS
            print("Creando usuario admin...")
            conn.execute(
                text("""
                    INSERT INTO users 
                    (email, name, lastname, hashed_password, role, is_verified, is_active)
                    VALUES (:email, :name, :lastname, :pw, 'admin', true, true)
                """),
                {
                    "email": "admin@agent.com",
                    "name": "Admin", 
                    "lastname": "User",
                    "pw": hashed_pw
                }
            )
            
            print("\n" + "="*50)
            print("🎉 ¡ADMIN CREADO EXITOSAMENTE!")
            print("="*50)
            print(f"Email: admin@agent.com")
            print(f"Password: {password}")
            print(f"Rol: admin (en minúsculas)")
            print("="*50)
            print("⚠️ Cambia la contraseña inmediatamente!")
            print("="*50)
            
            # 4. Verificar
            result = conn.execute(
                text("SELECT id, email, role::text, is_verified, is_active FROM users WHERE email = :email"),
                {"email": "admin@agent.com"}
            )
            user = result.fetchone()
            
            print(f"\n✅ Verificación:")
            print(f"   ID: {user[0]}")
            print(f"   Email: {user[1]}")
            print(f"   Rol: {user[2]}")
            print(f"   Verificado: {user[3]}")
            print(f"   Activo: {user[4]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    crear_admin()