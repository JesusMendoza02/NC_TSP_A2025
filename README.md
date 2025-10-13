# NC_TSP_A2025

## Levantar la aplicación 

### Clonar el repositorio

```bash
git clone https://github.com/JesusMendoza02/NC_TSP_A2025.git
cd NC_TSP_A2025

Iniciar contenedores
docker compose up -d

Entrar en los contenedores 
docker compose exec app bash

Iniciar el entorno
. /env/bin/activate

Aplicar migraciones

python manage.py migrate

Crear superusuario

python manage.py createsuperuser

Sigue las instrucciones para ingresar:

Usuario
Contraseña

Correr el servidor

python manage.py runserver 0:8000
