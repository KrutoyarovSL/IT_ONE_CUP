import torch
import re
import os
from pathlib import Path
from typing import Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer

class CodeAssistant:
    def __init__(self, model_path: Optional[str] = None):
        """
        Инициализация ассистента с загрузкой модели из существующей папки
        
        Args:
            model_path: Путь к директории с кешированной моделью. Если None, используется путь по умолчанию.
        """
        if model_path is None:
            model_path = Path("/workspace/IT_ONE_CUP/model_cache")
        else:
            model_path = Path(model_path)
            
        self.model_path = str(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = None
        self._tokenizer = None
        
        # Улучшенный системный промпт
        self.system_prompt = """You are an AI assistant helping to modify and improve website code.
You should:
1. Always provide specific and actionable code changes
2. Format code blocks using proper language tags (html, css, js)
3. Explain what each change does and why it's needed
4. If the request is unclear, ask for clarification
5. Focus on one change at a time
6. Validate that suggested changes are complete and correct

Current task: Analyze the provided code and suggest improvements based on the user's request.
"""

    @property
    def model(self):
        if self._model is None:
            print(f"Загрузка модели из {self.model_path}...")
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map={"": "cuda:0"},
                load_in_8bit=True,  # Включаем 8-bit quantization
                torch_dtype=torch.float16,
                trust_remote_code=True,
                use_cache=True,
                low_cpu_mem_usage=True  # Оптимизация использования CPU памяти
            )
            print("Модель успешно загружена!")
        return self._model

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            print(f"Загрузка токенизатора из {self.model_path}...")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True,
                padding_side="left"
            )
            print("Токенизатор успешно загружен!")
        return self._tokenizer

    def generate_response(self, 
                        message: str, 
                        current_code: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
        """Генерирует ответ на основе сообщения пользователя и текущего кода"""
        try:
            current_code = current_code or {}
            
            # Форматируем контекст более структурированно
            context = []
            for lang, code in current_code.items():
                if code:
                    # Извлекаем только релевантные части кода
                    if len(code) > 1000:
                        # Добавляем начало и конец длинного файла
                        code_snippet = f"{code[:500]}\n... [code truncated] ...\n{code[-500:]}"
                    else:
                        code_snippet = code
                    context.append(f"Current {lang.upper()} code:\n```{lang}\n{code_snippet}\n```")
            
            prompt = f"{self.system_prompt}\n\n"
            if context:
                prompt += "Context:\n" + "\n".join(context) + "\n\n"
            prompt += f"User: {message}\n\nAssistant: "
            
            # Улучшенные параметры генерации
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=1000,
                    temperature=0.3,  # Уменьшаем температуру для более определенных ответов
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.2,
                    pad_token_id=self.tokenizer.eos_token_id,
                    early_stopping=True
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Извлекаем только ответ ассистента
            try:
                assistant_response = response.split("Assistant: ")[-1].strip()
            except Exception as e:
                print(f"Error extracting assistant response: {e}")
                assistant_response = response
            
            cleaned_response = self.clean_response(assistant_response)
            
            # Улучшенное извлечение кода
            code_blocks = re.finditer(r'```(\w+)?\n(.*?)```', cleaned_response, re.DOTALL)
            suggested_changes = {}
            
            for match in code_blocks:
                lang = match.group(1) or 'text'
                code = match.group(2).strip()
                suggested_changes[lang] = code
            
            return {
                'message': cleaned_response,
                'suggestedChanges': suggested_changes
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'message': f"Произошла ошибка при генерации ответа: {str(e)}",
                'suggestedChanges': None
            }

    def clean_response(self, text: str) -> str:
        """Очищает и форматирует ответ модели."""
        # Удаляем невидимые символы и лишние пробелы
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'\s+', ' ', text)
        
        # Восстанавливаем форматирование кода
        text = re.sub(r'```(\w+)?\s', r'```\1\n', text)
        text = re.sub(r'\s```', r'\n```', text)
        
        # Восстанавливаем переносы строк в тексте
        text = re.sub(r'(?<=[.!?])\s+', '\n', text)
        
        return text.strip()

assistant = CodeAssistant()