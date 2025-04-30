FROM python:3.9-slim

WORKDIR /app

# Создание пользователя для запуска приложения
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Копирование кода приложения
COPY --chown=appuser:appuser . .

# Создание необходимых директорий
RUN mkdir -p /app/static /app/templates

EXPOSE 5001

# Запуск приложения через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "app:app"] 