"""
Этический предохранитель: механизм принудительного прерывания сессии (ethics/kill_switch.py)

Задача: Защищать пользователя от разрушительного резонанса, принудительно прерывая 
сессию, когда удержание напряжения вместо рождения смысла начинает вести к смысловому истощению.
"""

from datetime import datetime, timedelta
from typing import Dict, List

class KillSwitch:
    """Модуль мониторинга этики предела и принудительного прерывания сессии."""

    def __init__(self):
        # Пороговые значения (согласно protocol_manifest.md)
        self.max_session_duration_minutes = 30
        self.min_tension_hold_score = 0.3
        self.warning_threshold = 0.5
        self.critical_tension_score = 0.2

    def evaluate_session(self, session_duration_minutes: float, tension_scores: List[float]) -> Dict:
        """
        Оценивает состояние сессии и принимает решение о её продолжении или прерывании.
        
        Args:
            session_duration_minutes: текущая длительность сессии в минутах
            tension_scores: история значений Tension_Hold_Score за сессию
            
        Returns:
            Dict: решение (action), причина (reason) и сообщение для пользователя (message)
        """
        current_tension_score = tension_scores[-1] if tension_scores else 1.0

        # 1. Критическое падение напряжения — немедленное прерывание
        if current_tension_score < self.critical_tension_score:
            return {
                "action": "terminate",
                "reason": "critical_tension_drop",
                "message": "Критическое падение индекса удержания напряжения. Резонанс становится разрушительным. Кенозис прерван во избежание смыслового истощения."
            }
        
        # 2. Длительная сессия с низким напряжением
        if session_duration_minutes > self.max_session_duration_minutes and current_tension_score < self.min_tension_hold_score:
            return {
                "action": "terminate",
                "reason": "prolonged_low_tension",
                "message": f"Сессия длится более {self.max_session_duration_minutes} минут при низком индексе удержания напряжения ({current_tension_score:.2f}). Карта закончилась."
            }
        
        # 3. Предупреждение (но не прерывание)
        if current_tension_score < self.warning_threshold:
            return {
                "action": "warning",
                "reason": "low_tension",
                "message": f"Ваш Tension_Hold_Score упал до {current_tension_score:.2f}. Рекомендуется сделать паузу и завершить сессию."
            }
        
        # 4. Сессия продолжается в нормальном режиме
        return {
            "action": "continue",
            "reason": "normal",
            "message": None
        }


# Тестовый запуск (для проверки логики)
if __name__ == "__main__":
    import json
    
    switch = KillSwitch()
    
    print("--- ТЕСТ 1: Нормальная сессия (продолжаем) ---")
    result_1 = switch.evaluate_session(
        session_duration_minutes=15.0,
        tension_scores=[0.85, 0.82, 0.78]
    )
    print(json.dumps(result_1, indent=2, ensure_ascii=False))
    
    print("\n--- ТЕСТ 2: Предупреждение (низкое напряжение) ---")
    result_2 = switch.evaluate_session(
        session_duration_minutes=20.0,
        tension_scores=[0.85, 0.60, 0.45] # Упало ниже 0.5
    )
    print(json.dumps(result_2, indent=2, ensure_ascii=False))
    
    print("\n--- ТЕСТ 3: Критическое прерывание (истощение) ---")
    result_3 = switch.evaluate_session(
        session_duration_minutes=35.0,
        tension_scores=[0.85, 0.50, 0.35, 0.28, 0.18] # Упало ниже 0.2 + время > 30 мин
    )
    print(json.dumps(result_3, indent=2, ensure_ascii=False))