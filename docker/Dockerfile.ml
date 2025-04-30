FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Копирование кода модели
COPY model.py .
COPY model_install.py .

# Создание директории для модели
RUN mkdir -p /app/model_cache && chmod 777 /app/model_cache

# Установка переменных окружения для CUDA
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

EXPOSE 8000

# Запуск модели через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "model:app"] 