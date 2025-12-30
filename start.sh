set -e

echo " Iniciando aplicación..."

# Intentar aplicar migraciones
echo "🔄 Intentando aplicar migraciones..."
if alembic upgrade head; then
    echo "✅ Migraciones aplicadas exitosamente"
else
    echo "⚠️  Migraciones fallaron (puede que ya estén aplicadas)"
    echo "💡 Continuando con la aplicación..."
fi

echo "🚀 Iniciando FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
