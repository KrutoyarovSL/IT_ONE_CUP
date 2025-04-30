#!/usr/bin/env python3
import os
import torch
import sys
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download

# Конфигурация
MODEL_NAME = "deepseek-ai/deepseek-coder-33b-instruct"
MODEL_CACHE = Path("/workspace/IT_ONE_CUP/model_cache")  # Фиксированный путь к кешу модели
FORCE_DOWNLOAD = False  # True для принудительного перезакачивания

def setup_environment():
    """Инициализация окружения"""
    try:
        MODEL_CACHE.mkdir(parents=True, exist_ok=True)
        print(f"Рабочая директория: {os.getcwd()}")
        print(f"Кеш модели: {MODEL_CACHE}")
    except Exception as e:
        print(f"Ошибка при создании директории кеша: {e}")
        sys.exit(1)

def check_model_files():
    """Проверяет наличие всех необходимых файлов модели"""
    required_files = {
        "config.json",
        "model.safetensors",
        "tokenizer_config.json",
        "generation_config.json"
    }
    
    if not MODEL_CACHE.exists():
        return False
    
    found_files = set()
    for file in MODEL_CACHE.rglob("*"):
        if file.is_file():
            found_files.add(file.name)
    
    return required_files.issubset(found_files)

def download_model():
    """Скачивает модель с проверкой кеша"""
    setup_environment()
    
    if not FORCE_DOWNLOAD and check_model_files():
        print("Модель уже закеширована")
        return str(MODEL_CACHE)
    
    print(f"Загрузка модели {MODEL_NAME}...")
    try:
        snapshot_download(
            repo_id=MODEL_NAME,
            local_dir=str(MODEL_CACHE),
            local_dir_use_symlinks=False,
            resume_download=True,
            allow_patterns=["*.json", "*.bin", "*.model", "*.safetensors"],
            cache_dir=str(MODEL_CACHE)
        )
        print("Загрузка завершена")
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        sys.exit(1)
    
    return str(MODEL_CACHE)

def load_model():
    """Загружает модель в полном формате"""
    model_path = download_model()
    
    try:
        print("Загрузка токенизатора...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            padding_side="left"
        )
        
        print("Загрузка модели в полном формате...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.float16,  # Используем float16 для экономии памяти
            trust_remote_code=True,
            use_cache=True
        )
        
        print("Модель успешно загружена!")
        return model, tokenizer
    except Exception as e:
        print(f"Ошибка при загрузке модели: {e}")
        sys.exit(1)

if __name__ == "__main__":
    model, tokenizer = load_model()
    
    # Тестовый запрос
    prompt = "Напиши код на Python для бинарного поиска"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True
    )
    
    print("\nРезультат:\n", tokenizer.decode(outputs[0], skip_special_tokens=True))