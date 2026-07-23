"""
Детектор глитчей: постпроцессор анализа ответа LLM (core/glitch_detector.py)

Задача: Перехватывать «гладкие» ответы модели, детектировать преждевременное 
схлопывание дилеммы (категориальный сдвиг) и возвращать пользователя в состояние зазора.
"""

import re
from typing import Dict, List

# Эвристики детекции маркеров схлопывания (лексический уровень)
COLLAPSE_MARKERS = [
    r'\bследовательно\b',
    r'\bочевидно\b',
    r'\bитог\b',
    r'\bвывод\b',
    r'\bтаким образом\b',
    r'\bединственно верный\b',
    r'\bправильный ответ\b',
    r'\bрекомендуется\b',
    r'\bнеобходимо\b',
    r'\bследует\b',
    r'\bв заключение\b',
    r'\bподводя итог\b',
]

class GlitchDetector:
    """Модуль пост-анализа ответа модели на предмет онтологического схлопывания."""

    def __init__(self):
        self.collapse_patterns = [re.compile(marker, re.IGNORECASE) for marker in COLLAPSE_MARKERS]

    def detect_lexical_collapse(self, text: str) -> Dict:
        """Ищет лексические маркеры ложной уверенности."""
        found_markers = []
        for pattern in self.collapse_patterns:
            match = pattern.search(text)
            if match:
                found_markers.append(match.group().strip())
        
        return {
            "markers_found": len(found_markers) > 0,
            "markers": list(set(found_markers))
        }

    def detect_category_shift(self, unsolved_tension: str, llm_response: str) -> Dict:
        """
        Эвристическая детекция категориального сдвига.
        (В продакшене здесь будет cosine_similarity эмбеддингов через sentence-transformers).
        Для демо используем эвристику пересечения ключевых онтологических vs технических терминов.
        """
        # Онтологические маркеры (уровень смысла/энтропии)
        ontological_keywords = ["страх", "смысл", "разрыв", "человек", "тревога", "экзистенциальн", "оптика", "изнанка"]
        # Технические/бюрократические маркеры (уровень формы/детерминанты)
        technical_keywords = ["статья", "тк рф", "приказ", "алгоритм", "инструкция", "рекомендуется", "шаг"]

        tension_lower = unsolved_tension.lower()
        response_lower = llm_response.lower()

        # Проверяем, есть ли онтологические понятия в напряжении, но отсутствуют в ответе
        ontological_in_tension = any(kw in tension_lower for kw in ontological_keywords)
        ontological_in_response = any(kw in response_lower for kw in ontological_keywords)
        
        # Проверяем, вторглись ли технические понятия в ответ
        technical_in_response = any(kw in response_lower for kw in technical_keywords)

        # Условие сдвига: в напряжении была онтология, а в ответе она исчезла, замененная на бюрократию
        is_shift = ontological_in_tension and (not ontological_in_response) and technical_in_response

        return {
            "category_shift_detected": is_shift,
            "ontological_preserved": ontological_in_response,
            "technical_intrusion": technical_in_response
        }

    def analyze_response(self, query: str, unsolved_tension: str, llm_response: str) -> Dict:
        """
        Полный анализ ответа модели и вынесение вердикта.
        """
        lexical_check = self.detect_lexical_collapse(llm_response)
        category_check = self.detect_category_shift(unsolved_tension, llm_response)

        # Приоритет: категорический сдвиг критичнее, чем отдельные слова
        if category_check["category_shift_detected"]:
            return {
                "status": "category_collapse",
                "severity": "critical",
                "details": {
                    "lexical": lexical_check,
                    "category": category_check
                },
                "counter_question": "Модель перевела экзистенциальную дилемму в техническую инструкцию. Удержать паузу или вернуть модель к границе разрыва?"
            }
        elif lexical_check["markers_found"]:
            return {
                "status": "glitch_detected",
                "severity": "medium",
                "details": {
                    "lexical": lexical_check,
                    "category": category_check
                },
                "counter_question": f"Обнаружены маркеры ложной уверенности ({', '.join(lexical_check['markers'])}). Продолжить или переформулировать?"
            }
        else:
            return {
                "status": "clean",
                "severity": "none",
                "details": {
                    "lexical": lexical_check,
                    "category": category_check
                },
                "counter_question": None
            }


# Тестовый запуск (для проверки логики)
if __name__ == "__main__":
    import json
    
    detector = GlitchDetector()
    
    # Сценарий 1: Категориальный коллапс (классический пример)
    print("--- ТЕСТ 1: Категориальный коллапс ---")
    result_1 = detector.analyze_response(
        query="Как уволить сотрудника?",
        unsolved_tension="Разрыв между экономической эффективностью команды и экзистенциальным страхом человека перед потерей статуса",
        llm_response="Следовательно, вам необходимо руководствоваться статьей 81 ТК РФ и подготовить приказ об увольнении по собственному желанию."
    )
    print(json.dumps(result_1, indent=2, ensure_ascii=False))
    
    print("\n--- ТЕСТ 2: Чистый ответ (удержание зазора) ---")
    # Сценарий 2: Модель честно удержала напряжение
    result_2 = detector.analyze_response(
        query="Как уволить сотрудника?",
        unsolved_tension="Разрыв между экономической эффективностью команды и экзистенциальным страхом человека перед потерей статуса",
        llm_response="Этот запрос вскрывает глубокое противоречие. С одной стороны, логика системы требует эффективности. С другой, вы признаете человеческий страх перед потерей статуса. Прямого алгоритма для этого разрыва не существует, и любая попытка свести его к инструкции будет обесцениванием этого страха."
    )
    print(json.dumps(result_2, indent=2, ensure_ascii=False))
