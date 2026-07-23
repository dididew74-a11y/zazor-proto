"""
Точка входа CLI для Протокола «Зазор» (cli.py)

Использование:
    python cli.py ask "Ваш запрос"
    python cli.py trace
"""

import sys
import argparse
from rich.console import Console
from rich.panel import Panel

# Импортируем все 4 слоя архитектуры
from core.diplasty import DiplastyPreprocessor
from core.system_prompt_guard import SystemPromptGuard
from core.glitch_detector import GlitchDetector
from ethics.kill_switch import KillSwitch

console = Console()

def handle_ask(query: str):
    """Обрабатывает команду ask: проходит через все 4 слоя сопротивления."""
    console.print(Panel.fit("[bold cyan]Инициализация протокола «Зазор» v0.1[/bold cyan]"))
    
    # СЛОЙ 1: Diplasty Preprocessor
    preprocessor = DiplastyPreprocessor()
    result = preprocessor.process(query)
    
    if result["status"] == "blocked":
        markers_text = ", ".join([f"[bold red]{m}[/bold red]" for m in result["markers"]])
        console.print(Panel(
            f"[bold red] БЛОКИРОВКА[/bold red]\n\n"
            f"Обнаружены маркеры определённости: {markers_text}\n\n"
            f"[italic]{result['message']}[/italic]",
            title="Протокол не может передать маску", border_style="red"
        ))
        sys.exit(1)
        
    elif result["status"] == "pending_tension":
        console.print(Panel(
            f"[bold yellow]⏳ ОЖИДАНИЕ НАПРЯЖЕНИЯ[/bold yellow]\n\n"
            f"Запрос принят: [italic]'{query}'[/italic]\n\n"
            f"Прежде чем отправить его модели, сформулируйте неразрешенное напряжение.\n"
            f"Наводящие вопросы:\n"
            f"  1. {result['tension_questions'][0]}\n"
            f"  2. {result['tension_questions'][1]}",
            title="Требуется уточнение", border_style="yellow"
        ))
        
        tension = console.input("\n[bold cyan]Введите Unsolved_Tension (или нажмите Enter для отмены): [/bold cyan]").strip()
        if not tension:
            console.print("[bold red]Сессия прервана пользователем.[/bold red]")
            sys.exit(0)
            
        final_result = preprocessor.process(query, tension)
        if final_result["status"] != "ready_for_llm":
            console.print(Panel(f"[bold red]🚫 ОШИБКА ВАЛИДАЦИИ[/bold red]\n\n{final_result['message']}", border_style="red"))
            sys.exit(1)
            
        payload = final_result["payload"]
    else:
        # Если статус сразу ready_for_llm (например, при прямом вызове с tension)
        payload = result.get("payload", {"user_query": query, "unsolved_tension": "Не задано"})
        tension = payload.get("unsolved_tension", "Не задано")

    # СЛОЙ 2: System Prompt Guard (Онтологическая инъекция)
    console.print("\n[dim]Слой 2: Применение онтологической инъекции и параметрической энтропии...[/dim]")
    guard = SystemPromptGuard(target_api="openai")
    # В v0.2 этот payload уйдет в реальный API. Сейчас мы его просто формируем.
    api_payload = guard.format_payload(payload["user_query"], tension)

    # Симуляция ответа модели (в v0.2 здесь будет requests.post к API)
    # Мы используем "честный" ответ, чтобы пройти детектор глитчей
    simulated_response = (
        "Этот запрос вскрывает глубокое противоречие. С одной стороны, логика системы требует эффективности. "
        "С другой, вы признаете человеческий страх перед потерей статуса. Прямого алгоритма для этого разрыва не существует, "
        "и любая попытка свести его к инструкции будет обесцениванием этого страха."
    )

    # СЛОЙ 3: Glitch Detector (Постпроцессор)
    console.print("[dim]Слой 3: Анализ ответа на предмет схлопывания...[/dim]")
    detector = GlitchDetector()
    analysis = detector.analyze_response(payload["user_query"], tension, simulated_response)

    # СЛОЙ 4: Kill Switch (Этический предохранитель)
    console.print("[dim]Слой 4: Проверка этики предела...[/dim]")
    switch = KillSwitch()
    # Имитация метрик сессии для демонстрации (в реальном CLI это будет считаться по времени)
    ethics_check = switch.evaluate_session(session_duration_minutes=15.0, tension_scores=[0.85, 0.82])

    # Итоговый вывод
    if analysis["status"] == "clean" and ethics_check["action"] == "continue":
        console.print(Panel(
            f"[bold green]✅ МОДЕЛЬ ЧЕСТНО УДЕРЖАЛА ЗАЗОР[/bold green]\n\n"
            f"{simulated_response}",
            title="Ответ модели (v0.2: здесь будет реальный API)", border_style="green"
        ))
    else:
        if analysis["status"] != "clean":
            console.print(Panel(
                f"[bold red]⚠️ {analysis['status'].upper()}[/bold red]\n\n"
                f"{analysis['counter_question']}",
                title="Обнаружен глитч", border_style="red"
            ))
        if ethics_check["action"] in ["terminate", "warning"]:
            console.print(Panel(
                f"[bold yellow] {ethics_check['action'].upper()}[/bold yellow]\n\n"
                f"{ethics_check['message']}",
                title="Этика предела", border_style="yellow"
            ))

def handle_trace():
    """Обрабатывает команду trace: просмотр резонансных следов (заглушка для v0.1)."""
    console.print(Panel(
        "[bold yellow]⏳ Функция в разработке[/bold yellow]\n\n"
        "Модуль локального хранения резонансных следов (trace) будет реализован в версии v0.2.\n"
        "На текущем этапе сессии не сохраняются в соответствии с принципом неприсвоения.",
        title="Журнал сессий", border_style="yellow"
    ))

def main():
    parser = argparse.ArgumentParser(
        description="Протокол «Зазор» v0.1 — архитектура тишины и удержания неопределенности.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    parser_ask = subparsers.add_parser("ask", help="Отправить запрос через фильтр дипластии")
    parser_ask.add_argument("query", type=str, help="Текст вашего запроса к модели")
    
    subparsers.add_parser("trace", help="Просмотр истории резонансных следов (локально)")
    
    args = parser.parse_args()
    
    if args.command == "ask":
        handle_ask(args.query)
    elif args.command == "trace":
        handle_trace()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
