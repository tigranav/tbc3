source  .venv/bin/activate
export FLASK_APP="app:create_app"
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
export POSTGRES_HOST=192.168.0.50
export POSTGRES_PORT=5433
export POSTGRES_USER=tbc
export POSTGRES_PASSWORD=tbcpass
export POSTGRES_DB=books

flask run --debug
