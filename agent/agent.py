"""
Консольный агент для проекта «Слово Дня» (ЛР №2).

Режимы запуска:
    python agent.py --mode ask                # шаг 1: один запрос без инструментов
    python agent.py --mode chat               # шаг 2: чат с историей
    python agent.py --mode chat --no-history  # шаг 2: проверка, что без истории модель «забывает»
    python agent.py                           # шаги 3–5: полноценный агент с инструментами
"""
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import random

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = os.getenv("MODEL", "openai/gpt-4o-mini")
MAX_STEPS = 8

# Песочница: агент видит только эту папку
WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)

SYSTEM_PROMPT = (
    "Ты помощник игры «Слово Дня» — угадывание слов по тематическим категориям. "
    "Ты работаешь с файлами проекта в папке workspace и умеешь загадывать слова "
    "и записывать результаты игр. Отвечай кратко и по-русски. "
    "Не раскрывай загаданное слово, пока пользователь сам не попросит."
)


def get_client() -> OpenAI:
    """Клиент создаётся лениво, чтобы файл можно было импортировать без ключа."""
    return OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("BASE_URL", "https://openrouter.ai/api/v1"),
    )


# ───────────────────────── Инструменты ─────────────────────────

def safe_path(rel_path: str) -> Path:
    """Превращает путь из аргументов модели в путь внутри workspace."""
    full = (WORKSPACE / rel_path).resolve()
    # Эта проверка не пускает агента за пределы песочницы (например, ../.env)
    if not full.is_relative_to(WORKSPACE.resolve()):
        raise PermissionError(f"путь '{rel_path}' выходит за пределы workspace")
    return full


def list_files(path: str = ".") -> str:
    target = safe_path(path)
    if not target.exists():
        raise FileNotFoundError(f"папка '{path}' не найдена")
    if not target.is_dir():
        raise NotADirectoryError(f"'{path}' — это файл, а не папка")
    items = sorted(
        p.name + ("/" if p.is_dir() else "") for p in target.iterdir()
    )
    return "\n".join(items) if items else "(папка пуста)"


def read_file(path: str) -> str:
    target = safe_path(path)
    if not target.exists():
        raise FileNotFoundError(f"файл '{path}' не найден")
    if not target.is_file():
        raise IsADirectoryError(f"'{path}' — это папка, а не файл")
    text = target.read_text(encoding="utf-8")
    limit = 20000
    if len(text) > limit:
        return text[:limit] + f"\n...[обрезано, всего {len(text)} символов]"
    return text


def write_file(path: str, content: str) -> str:
    target = safe_path(path)
    answer = input(f"\n[?] Агент хочет записать файл '{path}' ({len(content)} симв.). Разрешить? [y/N] ")
    if answer.strip().lower() != "y":
        # Именно эту строку получает модель при отказе — она попадёт в историю как результат инструмента
        return "ОТКАЗ: пользователь не разрешил запись. Файл не изменён."
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Файл '{path}' записан ({len(content)} символов)."


# Инструменты под проект «Слово Дня» (слова те же, что в WordBank.kt)
WORD_BANK = {
    "Столицы": ["ПАРИЖ", "ТОКИО", "РИГА", "МИНСК", "ОСЛО", "БЕРН", "КИЕВ"],
    "Животные": ["ТИГР", "ЗЕБРА", "ВОЛК", "ЛИСА", "СОВА", "РЫСЬ"],
}
RESULTS_FILE = "results.json"


def get_random_word(category: str) -> str:
    if category not in WORD_BANK:
        raise ValueError(f"неизвестная категория '{category}', доступны: {', '.join(WORD_BANK)}")
    word = random.choice(WORD_BANK[category])
    return f"Категория: {category}; слово: {word}; длина: {len(word)}"


def save_result(word: str, guessed: bool) -> str:
    target = safe_path(RESULTS_FILE)
    results = json.loads(target.read_text(encoding="utf-8")) if target.exists() else []
    results.append({
        "word": word.upper(),
        "guessed": bool(guessed),
        "time": datetime.now().isoformat(timespec="seconds"),
    })
    target.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    won = sum(1 for r in results if r["guessed"])
    return f"Результат записан. Всего игр: {len(results)}, угадано: {won}."


TOOL_FUNCS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "get_random_word": get_random_word,
    "save_result": save_result,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Показать список файлов и папок в песочнице. Вызывай, чтобы узнать, какие файлы есть в проекте.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Папка относительно workspace, по умолчанию '.'"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Прочитать текстовый файл из песочницы. Вызывай, когда нужно узнать содержимое файла.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к файлу относительно workspace, например 'README.md'"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Создать или перезаписать текстовый файл в песочнице. Пользователь подтверждает запись вручную.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к файлу относительно workspace"},
                    "content": {"type": "string", "description": "Полное содержимое файла"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_random_word",
            "description": "Загадать случайное слово из категории игры «Слово Дня». Вызывай, когда пользователь хочет сыграть или просит слово.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": list(WORD_BANK.keys()),
                        "description": "Тематическая категория слов",
                    }
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_result",
            "description": "Записать результат сыгранного слова в results.json. Вызывай, когда пользователь сообщил, угадал он слово или нет.",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "Загаданное слово"},
                    "guessed": {"type": "boolean", "description": "true — слово угадано, false — нет"},
                },
                "required": ["word", "guessed"],
            },
        },
    },
]


# ───────────────────────── Агентный цикл ─────────────────────────

def execute_tool(name: str, raw_args: str) -> str:
    """Разбирает JSON-аргументы, вызывает функцию. Любая ошибка возвращается строкой, а не исключением."""
    try:
        args = json.loads(raw_args) if raw_args and raw_args.strip() else {}
        func = TOOL_FUNCS.get(name)
        if func is None:
            return f"ОШИБКА: неизвестный инструмент '{name}'"
        return str(func(**args))
    except Exception as e:  # намеренно широко: модель должна получить текст ошибки
        return f"ОШИБКА: {e}"


def assistant_to_dict(message) -> dict:
    """Превращает ответ модели в обычный словарь для списка messages."""
    result = {"role": "assistant", "content": message.content or ""}
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in message.tool_calls
        ]
    return result


def run_agent(client: OpenAI, messages: list) -> str:
    for step in range(1, MAX_STEPS + 1):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        message = response.choices[0].message
        usage = response.usage
        print(f"\n[шаг {step}] prompt_tokens={usage.prompt_tokens}, completion_tokens={usage.completion_tokens}")

        messages.append(assistant_to_dict(message))

        if not message.tool_calls:
            return message.content or ""

        for call in message.tool_calls:
            name, raw_args = call.function.name, call.function.arguments
            print(f"  -> инструмент: {name}({raw_args})")
            result = execute_tool(name, raw_args)
            shown = result if len(result) <= 200 else result[:200] + "..."
            print(f"  <- результат: {shown}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    return f"Достигнут лимит шагов (MAX_STEPS={MAX_STEPS}), задача не завершена."


# ───────────────────────── Режимы запуска ─────────────────────────

def mode_ask(client: OpenAI, question: str):
    """Шаг 1: один запрос без инструментов."""
    response = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": question}]
    )
    choice = response.choices[0]
    print("message.content:", choice.message.content)
    print("finish_reason:", choice.finish_reason)
    print("usage:", response.usage)


def mode_chat(client: OpenAI, use_history: bool):
    """Шаг 2: чат с историей, без инструментов."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Чат (пустая строка — выход)")
    while True:
        user_text = input("\nТы: ").strip()
        if not user_text:
            break
        if use_history:
            messages.append({"role": "user", "content": user_text})
            to_send = messages
        else:
            to_send = [messages[0], {"role": "user", "content": user_text}]
        response = client.chat.completions.create(model=MODEL, messages=to_send)
        answer = response.choices[0].message.content
        print("Модель:", answer)
        if use_history:
            messages.append({"role": "assistant", "content": answer})


def mode_agent(client: OpenAI):
    """Шаги 3–5: агент с инструментами."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"Агент готов. Песочница: {WORKSPACE}. Пустая строка — выход.")
    while True:
        user_text = input("\nТы: ").strip()
        if not user_text:
            break
        messages.append({"role": "user", "content": user_text})
        answer = run_agent(client, messages)
        print(f"\nАгент: {answer}")


def main():
    client = get_client()
    mode_agent(client)


if __name__ == "__main__":
    main()
