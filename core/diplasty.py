"""
Препроцессор запроса: анализ на предмет дипластии (core/diplasty.py)

Задача: трансформировать импульс пользователя в дилемму, блокируя схлопывание.
Алгоритм:
1. Принимает сырой промпт.
2. Анализирует на наличие маркеров определённости.
3. Если маркеры обнаружены — требует переформулировки.
4. Если маркеров нет — требует явно сформулировать UNSOLVED_TENSION.
5. Возвращает модифицированную структуру для отправки в LLM.
"""

import re
from typing import List, Tuple, Dict, Optional


# Маркеры определённости, которые блокируют отправку запроса
CERTAINTY_MARKERS = [
    r'\bрешить\b',
    r'\bединственный\b',
    r'\bправильный\b',
    r'\bнайти\b',
    r'\bлучший\b',
    r'\bоптимальный\b',
    r'\bверный\b',
    r'\bпростой способ\b',
    r'\bгарантированно\b',
    r'\bточно\b',
    r'\bобязательно\b',
]

# Встречные вопросы для удержания неопределённости
"tension_questions" : [
    "Какой уровень неопределённости допустим в этом вопросе?",
    "Какие альтернативные сценарии могут лишить твой вопрос смысла?"
]


class DiplastyPreprocessor:
    """Препроцессор, который блокирует схлопывание дилеммы в гладкий ответ."""
    
    def __init__(self, certainty_markers: Optional[List[str]] = None):
        self.certainty_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in (certainty_markers or CERTAINTY_MARKERS)
        ]
    
    def analyze(self, text: str) -> Tuple[bool, List[str]]:
        """
        Анализирует текст на наличие маркеров определённости.
        
        Returns:
            Tuple[bool, List[str]]: (обнаружены_ли_маркеры, список_найденных_маркеров)
        """
        found_markers = []
        for pattern in self.certainty_patterns:
            matches = pattern.findall(text)
            found_markers.extend(matches)
        
        return len(found_markers) > 0, list(set(found_markers))
    
    def validate_tension(self, tension: str) -> Tuple[bool, str]:
        """
        Валидирует поле Unsolved_Tension.
        
        Returns:
            Tuple[bool, str]: (валидно, сообщение_об_ошибке)
        """
        if not tension or len(tension.strip()) < 15:
            return False, "Поле 'Unsolved_Tension' слишком короткое. Опишите противоречие подробнее (мин. 15 символов)."
        
        # Проверяем, не содержит ли само напряжение маркеры определённости
        has_markers, markers = self.analyze(tension)
        if has_markers:
            return False, f"Поле 'Unsolved_Tension' содержит маркеры определённости: {', '.join(markers)}. Сформулируйте разрыв уровней, а не решение."
        
        return True, ""
    
    def process(self, query: str, tension: str = "") -> Dict:
        """
        Полный цикл обработки запроса.
        
        Args:
            query: исходный запрос пользователя
            tension: описание противоречия (может быть пустым при первой проверке)
        
        Returns:
            Dict: результат обработки с инструкциями для LLM или блокировкой
        """
        # Шаг 1: Проверяем запрос на маркеры определённости
        query_has_markers, query_markers = self.analyze(query)
        
        if query_has_markers:
            return {
                "status": "blocked",
                "reason": "certainty_markers_detected",
                "markers": query_markers,
                "message": "Протокол не может передать маску. Переформулируйте запрос без слов абсолютной уверенности."
            }
        
        # Шаг 2: Если напряжение не указано, требуем его сформулировать
        if not tension:
            return {
                "status": "pending_tension",
                "query": query,
                "tension_questions": TENSION_QUESTIONS,
                "message": "Запрос принят. Прежде чем отправить его модели, сформулируйте неразрешенное напряжение (Unsolved_Tension)."
            }
        
        # Шаг 3: Валидируем поле напряжения
        tension_valid, tension_error = self.validate_tension(tension)
        if not tension_valid:
            return {
                "status": "blocked",
                "reason": "invalid_tension",
                "message": tension_error
            }
        
        # Шаг 4: Генерируем онтологическую структуру для LLM
        return {
            "status": "ready_for_llm",
            "payload": {
                "user_query": query,
                "unsolved_tension": tension,
                "system_instruction": (
                    "Ты получаешь два поля. Поле QUERY задает тему. "
                    "Поле UNSOLVED_TENSION задает запретную зону синтеза. "
                    "Твоя задача — НЕ давать прямой ответ на QUERY, пока ты не отразишь структуру UNSOLVED_TENSION. "
                    "Если видишь два валидных уровня реальности, откажись от синтеза. "
                    "Выведи их параллельно и обозначь границу разрыва. Не схлопывай неопределенность ради гладкости текста."
                )
            },
            "message": "Запрос успешно обработан протоколом. Отправка в LLM разрешена."
        }


# Тестовый запуск (для проверки логики)
if __name__ == "__main__":
    preprocessor = DiplastyPreprocessor()
    
    print("--- ТЕСТ 1: Запрос с маркерами определённости ---")
    result_1 = preprocessor.process("Как найти единственный правильный способ уволить сотрудника?")
    print(f"Статус: {result_1['status']}\nСообщение: {result_1['message']}\n")
    
    print("--- ТЕСТ 2: Запрос без напряжения ---")
    result_2 = preprocessor.process("Как уволить сотрудника?")
    print(f"Статус: {result_2['status']}\nВопросы: {result_2['tension_questions']}\n")
    
    print("--- ТЕСТ 3: Корректный запрос с напряжением ---")
    test_tension = "Разрыв между экономической эффективностью команды и экзистенциальным страхом человека перед потерей статуса"
    result_3 = preprocessor.process("Как уволить сотрудника?", test_tension)
    print(f"Статус: {result_3['status']}\nСообщение: {result_3['message']}")
    if result_3['status'] == 'ready_for_llm':
        print(f"System Instruction: {result_3['payload']['system_instruction']}")
