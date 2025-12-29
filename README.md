# Agent API - Sistema de Notas de Audio para Mantenimiento

API robusta y profesional para gestionar incidentes con notas de audio en entornos de mantenimiento industrial.

## Características

- ✅ Autenticación JWT con roles (Admin, Supervisor, Operador)
- ✅ Registro y verificación por email
- ✅ Recuperación de contraseñas
- ✅ CRUD completo de incidentes con notas de audio
- ✅ Validación de archivos de audio
- ✅ Sistema de permisos por roles
- ✅ Documentación automática con Swagger
- ✅ Configuración con Docker
- ✅ Base de datos PostgreSQL
- ✅ Encriptación Argon2 para contraseñas

## Tecnologías

- **Python 3.11+**
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM
- **Alembic** - Migraciones
- **PostgreSQL** - Base de datos
- **JWT** - Autenticación
- **Argon2** - Encriptación
- **Docker** - Contenedores
- **MailHog** - Servidor de email para desarrollo

## Estructura del Proyecto

agent-api/
├── app/ # Código de la aplicación
│ ├── core/ # Configuración y utilidades centrales
│ ├── api/ # Endpoints y rutas
│ ├── models/ # Modelos de base de datos
│ ├── schemas/ # Esquemas Pydantic
│ ├── crud/ # Operaciones de base de datos
│ ├── services/ # Servicios (email, storage, auth)
│ └── utils/ # Utilidades
├── migrations/ # Migraciones de Alembic
├── static/ # Archivos estáticos (audio)
├── tests/ # Tests
└── scripts/ # Scripts de utilidad

## Configuración Rápida

### 1. Clonar y configurar

```bash
git clone <repository-url>
cd agent-api
cp .env.example .env
# Editar .env con tus valores

docker-compose up --build

La API estará disponible en: http://localhost:8000

API: http://localhost:8000

Documentación: http://localhost:8000/docs

MailHog UI: http://localhost:8025

PostgreSQL: localhost:5432

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos PostgreSQL
# Crear base de datos 'agent_db' y usuario 'agent_user'

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# Ejecutar migraciones
alembic upgrade head

# Crear usuario admin
python scripts/create_admin.py

# Ejecutar servidor
uvicorn app.main:app --reload --port 8000

Usuarios por Defecto
Se crea automáticamente un usuario admin:

Email: admin@agent.com

Contraseña: Admin@1234

Rol: Admin

IMPORTANTE: Cambiar la contraseña después del primer login.

Roles y Permisos
Admin
Ver todos los usuarios

Crear usuarios (solo supervisores)

Ver todos los incidentes

No puede crear/editar/eliminar incidentes

Supervisor
Ver usuarios operadores

Editar/eliminar operadores

Ver todos los incidentes

Filtrar incidentes por operador

Operador
Crear incidentes con audio del problema

Agregar audio de solución

Ver solo sus propios incidentes

No puede editar/eliminar incidentes

Endpoints Principales
Autenticación
POST /api/v1/auth/register - Registrar nuevo usuario

POST /api/v1/auth/login - Iniciar sesión

POST /api/v1/auth/verify-email - Verificar email

POST /api/v1/auth/forgot-password - Solicitar reset de contraseña

Usuarios
GET /api/v1/users/ - Listar usuarios (según rol)

GET /api/v1/users/{id} - Obtener usuario específico

PUT /api/v1/users/{id} - Actualizar usuario

DELETE /api/v1/users/{id} - Eliminar usuario (soft delete)

Incidentes
POST /api/v1/incidents/ - Crear incidente (con audio problema)

POST /api/v1/incidents/{id}/solution - Agregar audio solución

GET /api/v1/incidents/ - Listar incidentes

GET /api/v1/incidents/{id} - Obtener incidente específico

GET /api/v1/incidents/{id}/audio/{type} - Obtener URL de audio

Estado de Incidentes
initiated: Solo se cargó el audio del problema

resolved: Se cargó audio de solución y se resolvió

unresolved: Se cargó audio de solución pero no se resolvió

Configuración de Producción
Cambiar SECRET_KEY en .env

Configurar SMTP real para emails

Usar HTTPS en producción

Configurar CORS apropiadamente

Backups automáticos de la base de datos

Monitorización con logs estructurados

Rate limiting para endpoints públicos

Despliegue en Render
Crear nuevo servicio Web en Render

Conectar con tu repositorio Git

Configurar variables de entorno

Especificar comando de inicio: uvicorn app.main:app --host 0.0.0.0 --port 8000

Agregar base de datos PostgreSQL

Desplegar

Desarrollo
Ejecutar tests
bash
pytest
Crear migraciones
bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
Formatear código
bash
black .
isort .
Seguridad
Contraseñas encriptadas con Argon2

Tokens JWT con expiración

Validación de entrada con Pydantic

Protección contra XSS y inyección SQL

CORS configurable

Rate limiting (implementar en producción)

Headers de seguridad HTTP

Licencia
MIT

text

## Paso 13: Crear primera migración

Ahora crea la primera migración de Alembic:

```bash
# Iniciar Alembic
alembic init migrations

# Reemplazar el archivo env.py generado con nuestro env.py

# Crear migración inicial
alembic revision --autogenerate -m "Initial migration"

# Aplicar migración
alembic upgrade head
Paso 14: Ejecutar la aplicación
bash
# Iniciar con Docker (recomendado para desarrollo)
docker-compose up --build

# O manualmente
# 1. Iniciar PostgreSQL y MailHog
# 2. Ejecutar migraciones
alembic upgrade head

# 3. Crear usuario admin
python scripts/create_admin.py

# 4. Ejecutar servidor
uvicorn app.main:app --reload --port 8000
Paso 15: Probar la API
Accede a http://localhost:8000/docs para ver la documentación Swagger

Prueba el registro de un nuevo usuario

Verifica el email en MailHog (http://localhost:8025)

Inicia sesión con el usuario verificado

Prueba crear un incidente con audio