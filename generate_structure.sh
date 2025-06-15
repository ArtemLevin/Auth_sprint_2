#!/bin/bash

# Имя проекта
PROJECT_DIR="auth_service"

# Создаем корневую папку проекта
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR" || exit

# Создаем структуру папок
mkdir -p alembic/versions
mkdir -p app/{api/v1,core,models,schemas,services,utils,db}
mkdir -p tests

# Создаем пустые файлы

# app/
touch app/main.py
touch app/settings.py

# app/api/v1/
touch app/api/v1/__init__.py

# app/core/
touch app/core/config.py
touch app/core/security.py
touch app/core/dependencies.py
touch app/core/logging.conf

# app/models/
touch app/models/user.py
touch app/models/role.py
touch app/models/login_history.py

# app/schemas/
touch app/schemas/auth.py
touch app/schemas/user.py
touch app/schemas/role.py

# app/services/
touch app/services/auth_service.py
touch app/services/role_service.py
touch app/services/mfa_service.py

# app/utils/
touch app/utils/cache.py
touch app/utils/create_superuser.py

# app/db/
touch app/db/base.py
touch app/db/session.py

# tests/
touch tests/__init__.py

# Конфигурационные файлы
touch .env
touch requirements.txt
touch README.md

echo "✅ Структура проекта создана в папке '$PROJECT_DIR'"