#!/bin/sh

echo "Aguardando o MySQL iniciar..."
while ! nc -z db 3306; do
  sleep 2
done
echo "MySQL iniciado!"

# Garante que o diretório de trabalho está certo
cd /app

# Gera e aplica migrations
python manage.py makemigrations
python manage.py migrate

echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

# Cria o superusuário automaticamente se não existir
echo "Verificando superusuário..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superusuário criado: admin / admin")
else:
    print("Superusuário já existe.")
EOF

# Inicia o servidor Django
exec python manage.py runserver 0.0.0.0:8000
