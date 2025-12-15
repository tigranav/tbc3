# Flask Application Scaffold

This repository provides a minimal Flask application scaffold configured to use the existing `libs` PostgreSQL helper and a sample blueprint exposing basic endpoints.

## Prerequisites
- Python 3.11
- PostgreSQL instance accessible to the application

Install application dependencies in your virtual environment:

```bash
pip install flask psycopg2-binary celery redis
```

## Configuration
Database connection settings are read from the environment via `app.config.PostgresConfig`:

- `POSTGRES_HOST` (default: `localhost`)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_USER` (default: `postgres`)
- `POSTGRES_PASSWORD` (default: empty)
- `POSTGRES_DB` (default: `postgres`)

You can also set `FLASK_SECRET_KEY` to override the default secret key. For SQLAlchemy CRUD endpoints you may override the
connection string with `SQLALCHEMY_DATABASE_URI`; otherwise it is built from the PostgreSQL settings above.

### Celery configuration

Celery is configured via `app.config.CeleryConfig` and the following environment variables:

- `CELERY_BROKER_URL` (default: `redis://localhost:6379/0`; must point to a Redis instance or the app will raise a validation error)
- `CELERY_RESULT_BACKEND` (default: unset)
- `CELERY_DEFAULT_QUEUE` (default: `default`)
- `CELERY_TASK_ACKS_LATE` (default: `1` to acknowledge tasks after completion)
- `CELERY_TASK_TIME_LIMIT` (default: `300` seconds)
- `CELERY_TASK_ALWAYS_EAGER` (default: `0`; set to `1` for local, synchronous execution in tests)
- `CELERY_TASK_EAGER_PROPAGATES` (default: `1`)
- `CELERY_TASK_STORE_EAGER_RESULT` (default: `0`; set to `1` when you want eager results returned to API callers)

## Running the application
Export the environment variables you need, then start the Flask development server using the application factory:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password
export POSTGRES_DB=postgres

# In the project root
export FLASK_APP="app:create_app"
flask run --debug
```

Visit `http://localhost:5000/api/health` to verify the service is running. The `/api/db-status` endpoint attempts to connect to PostgreSQL using the configured credentials and will return an error if the database is unavailable.

To expose the development server to other machines (for example, from inside a container), bind to all interfaces with `--host` or the corresponding environment variable:

```bash
flask --app "app:create_app" run --host 0.0.0.0 --port 5000 --debug
# or
export FLASK_APP="app:create_app"
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
flask run --debug
```

## Веб-интерфейс (Bootstrap 5)

Готовый UI работает поверх существующих API и подключается к той же PostgreSQL базе. После запуска приложения:

- Откройте `http://localhost:5000/` — главная страница с навигацией и краткой инструкцией.
- Перейдите в раздел **«Группы файлов книг»** (`/groups`) — там отображается содержимое таблицы `tbc.books_files_groups` и есть формы для чтения/добавления/редактирования/удаления записей.
- Перейдите в раздел **«Типы файлов книг»** (`/types`) — отображается таблица `tbc.books_files_types`, связанная с группами через `group_id`.

### Как пользоваться страницей `/groups`

1. Нажмите **«Обновить»**, чтобы загрузить данные через `GET /api/groups/`.
2. Для создания заполните форму (ID обязателен) и отправьте — выполняется `POST /api/groups/`.
3. Для редактирования выберите запись через кнопку с карандашом — форма переключится в режим `PUT /api/groups/<id>`.
4. Кнопка с корзиной удаляет запись через `DELETE /api/groups/<id>` с подтверждением.

Дизайн собран на Bootstrap 5.3 с минималистичными компонентами: шапка, карточки, адаптивная таблица и компактные кнопки действий. JS на странице работает через `fetch` и использует существующий REST-блюпринт `/api/groups` без дополнительных зависимостей.

## CRUD-блюпринт на SQLAlchemy для `tbc.books_files_groups`

Каталожный пример заменён на целевой CRUD для таблицы `tbc.books_files_groups`, реализованный через SQLAlchemy.

- **Модели и репозиторий:** `app/blueprints/groups/models.py` и `app/blueprints/groups/repository.py` описывают ORM-модель и операции чтения/записи (используют `SQLALCHEMY_DATABASE_URI` или настройки PostgreSQL по умолчанию).
- **Маршруты:** `app/blueprints/groups/__init__.py` регистрирует `Blueprint` под префиксом `/api/groups` и реализует CRUD.

### Эндпоинты

- `GET /api/groups/` — список групп: `{ "items": [...], "total": <int> }`.
- `GET /api/groups/<id>` — вернуть объект или `404`.
- `POST /api/groups/` — создать запись. JSON-пример:

  ```json
  {"id": 10, "name": "GPU jobs", "comment": "tasks that need CUDA"}
  ```

  Возвращает `201` и созданный объект, либо `400`, если `id` уже существует.

- `PUT /api/groups/<id>` — обновить `name`/`comment`. Возвращает `404`, если записи нет.
- `DELETE /api/groups/<id>` — удаляет запись, возвращает `404`, если её нет.

## CRUD-блюпринт на SQLAlchemy для `tbc.books_files_types`

- **Модель и репозиторий:** `app/blueprints/types/models.py` и `app/blueprints/types/repository.py` описывают таблицу `tbc.books_files_types` с внешним ключом `group_id` на `tbc.books_files_groups.id`. При создании/обновлении происходит проверка существования группы.
- **Маршруты:** `app/blueprints/types/__init__.py` регистрирует `Blueprint` под префиксом `/api/types`.
- `GET /api/types/` — список типов: `{ "items": [...], "total": <int> }`.
- `GET /api/types/<id>` — вернуть объект или `404`.
- `POST /api/types/` — создать запись (обязательны `id` и `group_id`). JSON-пример:

  ```json
  {
    "id": 10,
    "file_name": "chapter.pdf",
    "comments": "PDF",
    "group_id": 1
  }
  ```

- `PUT /api/types/<id>` — обновить `file_name`/`comments` и/или `group_id` с валидацией существования группы.
- `DELETE /api/types/<id>` — удалить запись, вернуть `404`, если её нет.

### Как пользоваться страницей `/types`

1. Загрузите список групп кнопкой **«Обновить»** или дождитесь автозагрузки при входе — данные приходят из `GET /api/groups/`.
2. Заполните форму (ID и группа обязательны) и отправьте — выполнится `POST /api/types/`.
3. Для редактирования выберите запись в таблице — форма переключится в режим `PUT /api/types/<id>`.
4. Удаление доступно через кнопку с корзиной — запрос `DELETE /api/types/<id>`.

### Как добавить свой SQLAlchemy-блюпринт

1. **Создайте модель** от `app.db.Base` и опишите схему/ограничения PostgreSQL (поля, длины строк, `__table_args__` для схемы) без изменения структуры БД.
2. **Определите репозиторий** с методами CRUD в отдельном модуле. Используйте `Session` из `app.extensions.get_session` и явно вызывайте `commit()/rollback()`.
3. **Соберите блюпринт** в `__init__.py`: регистрируйте `Blueprint`, валидируйте входной JSON, возвращайте структурированные ответы и закрывайте сессии через контекстный менеджер, как в `_repository()`.
4. **Добавьте роуты в фабрику** (`app/__init__.py`) и опишите краткую документацию/примеры запросов в README.
5. **Напишите тесты** на SQLite (`SQLALCHEMY_DATABASE_URI=sqlite+pysqlite:///:memory:`), создавая таблицы через `Base.metadata` и проверяя happy-path/ошибки.
## Background tasks with Celery

The application ships with a Celery app in `app/celery_app.py` and a sample task at `app/tasks/importer.py` that normalizes importer records. Queues are configured in `app.config.CeleryConfig` and default to the queue name found in `CELERY_DEFAULT_QUEUE` (the importer blueprint uses this when dispatching tasks).

Celery is intentionally limited to Redis as its broker. Provide a Redis URL via `CELERY_BROKER_URL` (e.g., `redis://redis:6379/0`); any other scheme will fail validation during app startup.

### Создание своих Celery-тасков

1. Создайте модуль задачи, например `app/tasks/email.py`, и опишите функцию регистрации задач (по аналогии с `app/tasks/importer.py`):

   ```python
   # app/tasks/email.py
   from __future__ import annotations

   from celery import Celery


   def register_email_tasks(celery_app: Celery) -> None:
       @celery_app.task(name="app.tasks.email.send_email")
       def send_email(recipient: str, subject: str, body: str) -> str:
           # Здесь размещается бизнес-логика
           return f"sent to {recipient}"

       celery_app.tasks.register(send_email)
   ```

2. Подключите модуль в фабрике Celery. Добавьте его в `include` и вызовите функцию регистрации в `app/extensions.py` рядом с импортёром:

   ```python
   celery_app = Celery(
       app.import_name,
       broker=celery_config.broker_url,
       backend=celery_config.result_backend,
       include=["app.tasks.importer", "app.tasks.email"],
       set_as_current=True,
   )

   from app.tasks import email as email_tasks
   email_tasks.register_email_tasks(celery_app)
   ```

3. Если задаче нужен отдельный канал, обновите `CELERY_DEFAULT_QUEUE` или задайте `queue` в `apply_async`. Для сложной маршрутизации дополните `celery_app.conf.task_routes` в `create_celery_app`.

### Работа с несколькими очередями (GPU и CPU)

Celery позволяет заводить отдельные очереди под разные ресурсы. Например, тяжёлые ML-задачи можно отправлять в очередь `gpu`, а лёгкие фоновые задачи — в очередь `cpu`.

1. Задайте маршрутизацию задач в `create_celery_app` (файл `app/extensions.py`), чтобы каждая задача попадала в нужную очередь:

   ```python
   celery_app.conf.task_routes = {
       "app.tasks.importer.normalize_record": {"queue": "cpu"},
       "app.tasks.gpu.process_video": {"queue": "gpu"},
   }
   ```

2. При вызове задачи можно явно указать очередь, если хотите временно переопределить маршрутизацию:

   ```python
   task = celery_app.tasks["app.tasks.importer.normalize_record"]
   result = task.apply_async(args=[record], queue="cpu")
   ```

3. Запускайте отдельные воркеры на нужных нодах:

   - CPU-нода: `celery -A app.celery_app.celery worker --loglevel=info --queues=cpu`
   - GPU-нода: `celery -A app.celery_app.celery worker --loglevel=info --queues=gpu`

   Каждый воркер будет слушать только свою очередь, поэтому GPU-воркеру достанутся только задачи, отправленные в `gpu`.

4. В Docker Compose можно разделить воркеры, добавив ещё один сервис для GPU-очереди и передав ему `--queues=gpu` (при условии, что хост с GPU пробрасывает ресурсы в контейнер через `deploy.resources.reservations.devices`).

### Вызов задач из blueprint-ов

Используйте уже созданный Celery экземпляр через `get_celery_app(current_app)` и вызывайте задачи так же, как в импортёре:

```python
from flask import Blueprint, current_app, jsonify

from app.extensions import get_celery_app

my_blueprint = Blueprint("my", __name__, url_prefix="/api/my")


@my_blueprint.route("/send", methods=["POST"])
def send() -> tuple[dict, int]:
    celery_app = get_celery_app(current_app)
    task = celery_app.tasks["app.tasks.email.send_email"]
    result = task.apply_async(args=["user@example.com", "Hello", "Body"], queue=celery_app.conf.task_default_queue)

    return jsonify({"task_id": result.id, "status": "queued"}), 202
```

В тестах и локальной разработке можно включить синхронное исполнение, установив `CELERY_TASK_ALWAYS_EAGER=1` и `CELERY_TASK_STORE_EAGER_RESULT=1`, тогда `result.result` сразу будет доступен.

### Отслеживание прогресса задач и получение статуса

Для того чтобы видеть промежуточные статусы, Celery должен писать результаты. Укажите бэкенд результатов (например, Redis) в `CELERY_RESULT_BACKEND`, чтобы API могло запрашивать состояние задач:

```bash
export CELERY_RESULT_BACKEND=redis://redis:6379/0
```

Пример задачи с прогрессом уже есть в проекте — `process_batch_with_progress` в `app/tasks/importer.py` вызывает `update_state`, сохраняя процент выполнения. Отправить такую задачу можно через эндпоинт `/api/importer/progress`:

```bash
curl -X POST http://localhost:5000/api/importer/progress \
  -H "Content-Type: application/json" \
  -d '{
        "records": [
          {"id": 1, "payload": "  GPU job  "},
          {"id": 2, "payload": " CPU job"}
        ]
      }'
# => {"status":"queued","task_id":"...","status_url":"/api/importer/status/<id>","queue":"importer"}
```

Получить состояние можно GET-запросом к `/api/importer/status/<task_id>`:

```bash
curl http://localhost:5000/api/importer/status/<task_id>
# => {"task_id":"...","state":"PROGRESS","meta":{"current":1,"total":2,"progress":50}}
```

Когда задача закончится, `state` станет `SUCCESS`, а поле `result` будет содержать итоговую структуру. При ошибках `state` принимает значение `FAILURE`, а поле `error` содержит текст исключения.

### Starting a worker

Run a worker that listens to the configured queue:

```bash
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_DEFAULT_QUEUE=importer
celery -A app.celery_app.celery worker --loglevel=info --queues=${CELERY_DEFAULT_QUEUE}
```

The `--queues` flag creates (or binds to) the named queue if your broker supports it. You can add more queues by extending `CELERY_DEFAULT_QUEUE` and `celery.conf.task_routes` in `app/extensions.py`.

### Sending tasks from the importer API

POST records to `/api/importer/ingest` with `"enqueue": true` to place work onto the Celery queue:

```bash
curl -X POST http://localhost:5000/api/importer/ingest \
  -H "Content-Type: application/json" \
  -d '{
        "source": "cli-example",
        "enqueue": true,
        "records": [
          {"id": 1, "payload": "  Hello "},
          {"id": 2, "payload": "World"}
        ]
      }'
```

The endpoint returns task IDs for each queued record. When `CELERY_TASK_ALWAYS_EAGER=1` (useful in local development and tests), tasks execute immediately and the response includes their processed payloads. In production you can track task status using Celery result backends or the task IDs exposed in the response.

## Running with Docker Compose

This repository includes a simple `docker-compose.yml` that wires Redis as the Celery broker, a Flask web container, and a Celery worker. Build and start the stack with:

```bash
docker compose up --build
```

Services:

- `web`: runs `flask run` bound to `0.0.0.0:5000`.
- `worker`: runs `celery -A app.celery_app.celery worker --loglevel=info --queues=${CELERY_DEFAULT_QUEUE}`.
- `redis`: provides the required Redis broker on `redis://redis:6379/0`.

The default queue is `importer`. If you change `CELERY_DEFAULT_QUEUE`, both `web` and `worker` services pick it up from the shared environment and the worker binds to the same queue name. Use the importer API with `"enqueue": true` to publish tasks into that queue after the stack starts.

## Testing
Run the available tests with pytest:

```bash
pytest
```
