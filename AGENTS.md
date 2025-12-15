# Instructions for AI Agents

## Project stack
- Python 3.11
- Flask (Blueprint-based)
- PostgreSQL + SQLAlchemy
- Celery for background jobs

## Rules
- Do not introduce new frameworks
- Do not change DB schema without migration
- Keep backward compatibility
- Prefer small, isolated changes

## Code style
- Type hints required
- Black formatting
- Explicit error handling

## Testing
- Run pytest if tests are affected
- Do not disable failing tests

## Forbidden
- No refactoring without request
- No dependency changes