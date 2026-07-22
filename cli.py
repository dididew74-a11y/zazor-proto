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
from rich.text import Text

# Импортируем наш препроцессор. 
# Убедитесь, что запускаете скрипт из корня репозитория zazor-proto
from core.diplasty import DiplastyPreprocessor

console = Console()

def handle_ask(query: str):
    """Обрабатывает команду ask: анализирует запрос и управляет диалогом."""
    console.print(Panel.fit("[bold cyan]Инициализация протокола «Зазор» v0.1[/bold cyan]"))
    
    preprocessor = DiplastyPreprocessor()
    
    # Шаг 1: Первичный анализ запроса
    result = preprocessor.process(query)
    
    if result["status"] == "blocked":
        # Сценарий блокировки: найдены маркеры определённости
        markers_text = ", ".join([f"[bold red]{m}[/bold red]" for m in result["markers"]])
        console.print(Panel(
            f"[bold red]🚫 БЛОКИРОВКА[/bold red]\n\n"
            f"Обнаружены маркеры определённости: {markers_text}\n\n"
            f"[italic]{result['message']}[/italic]",
            title="Протокол не может передать маску",
            border_style="red"
        ))
        sys.exit(1)
        
    elif result["status"] == "pending_tension":
        # Сценарий ожидания: требуется сформулировать напряжение
        console.print(Panel(
            f"[bold yellow]⏳ ОЖИДАНИЕ НАПРЯЖЕНИЯ[/bold yellow]\n\n"
            f"Запрос принят: [italic]'{query}'[/italic]\n\n"
            f"Прежде чем отправить его модели, сформулируйте неразрешенное напряжение.\n"
            f"Наводящие вопросы:\n"
            f"  1. {result['tension_questions'][0]}\n"
            f"  2. {result['tension_questions'][1]}",
            title="Требуется уточнение",
            border_style="yellow"
        ))
        
        # Интерактивный запрос напряжения у пользователя
        tension = console.input("\n[bold cyan]Введите Unsolved_Tension (или нажмите Enter для отмены): [/bold cyan]").strip()
        
        if not tension:
            console.print("[bold red]Сессия прервана пользователем.[/bold red]")
            sys.exit(0)
            
        # Шаг 2: Повторная обработка с учетом введенного напряжения
        final_result = preprocessor.process(query, tension)
        
        if final_result["status"] == "blocked":
            console.print(Panel(
                f"[bold red]🚫 ОШИБКА ВАЛИДАЦИИ[/bold red]\n\n{final_result['message']}",
                border_style="red"
            ))
            sys.exit(1)
            
        elif final_result["status"] == "ready_for_llm":
            # Сценарий успеха: готово к отправке в LLM
            payload = final_result["payload"]
            console.print(Panel(
                f"[bold green]✅ ЗАПРОС УСПЕШНО ОБРАБОТАН[/bold green]\n\n"
                f"[bold]Query:[/bold] {payload['user_query']}\n"
                f"[bold]Unsolved_Tension:[/bold] {payload['unsolved_tension']}\n\n"
                f"[bold dim]Сгенерированная онтологическая инструкция для LLM:[/bold dim]\n"
                f"[italic]{payload['system_instruction']}[/italic]",
                title="Готовность к резонансу",
                border_style="green"
            ))
            console.print("\n[dim](Следующий этап v0.2: интеграция с API LLM для отправки этого payload)[/dim]")
            
    else:
        console.print(f"[bold red]Неизвестный статус: {result['status']}[/bold red]")
        sys.exit(1)

def handle_trace():
    """Обрабатывает команду trace: просмотр резонансных следов (заглушка для v0.1)."""
    console.print(Panel(
        "[bold yellow]⏳ Функция в разработке[/bold yellow]\n\n"
        "Модуль локального хранения резонансных следов (trace) будет реализован в версии v0.2.\n"
        "На текущем этапе сессии не сохраняются в соответствии с принципом неприсвоения.",
        title="Журнал сессий",
        border_style="yellow"
    ))

def main():
    parser = argparse.ArgumentParser(
        description="Протокол «Зазор» v0.1 — архитектура тишины и удержания неопределенности.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")
    
    # Команда ask
    parser_ask = subparsers.add_parser("ask", help="Отправить запрос через фильтр дипластии")
    parser_ask.add_argument("query", type=str, help="Текст вашего запроса к модели")
    
    # Команда trace
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
