import os
import json
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API = os.getenv("DEEPSEEK_API_KEY")
URL = os.getenv("DEEPSEEK_BASE_URL")


class CriticDecision(BaseModel):
    verdict: Literal["OK", "REVISE"] = Field(description="Вердикт: OK (принять) или REVISE (отправить на доработку)")
    critique: Optional[str] = Field(description="Текст замечаний (обязательно, если REVISE)", default="")


def critic_node(state: dict):
    """
    Агент-критик.

    Принимает:
        - state['draft_artifact']: Черновик для проверки.

    Возвращает:
        - Обновленный state с ключами:
         "critic_verdict": "OK" или "REVISE".
         "critic_feedback": Замечания.

    ВАЖНО: Эта нода НЕ инкрементирует счетчик итераций. Это делает нода 'increment' в графе.
    """

    draft = state.get("draft_artifact")

    if not draft:
        return {
            "critic_verdict": "REVISE",
            "critic_feedback": "Артефакт пустой или не был сгенерирован.",
        }

    llm = ChatOpenAI(
        model="deepseek-chat",
        base_url=URL,
        api_key=DEEPSEEK_API,
        temperature=0.0
    )

    parser = PydanticOutputParser(pydantic_object=CriticDecision)

    system_prompt = """Ты - Старший Бизнес-аналитик. Твоя задача - валидировать Функциональные Требования (ФТ) проекта.

    Твоя цель: Убедиться, что требования описывают ПОВЕДЕНИЕ системы (User Story), а не реализацию.

    КРИТЕРИИ ОЦЕНКИ:
    1. ЗАПРЕЩЕНЫ технические детали: Нельзя писать про SQL, Python, REST API, JSON, эндпоинты, названия таблиц. Е��ли это есть -> REVISE.
    2. ЗАПРЕЩЕНА "вода": Фразы "сделать красиво", "быстро работать", "быть удобным" -> REVISE.
    3. НУЖНА бизнес-логика: "Пользователь нажимает кнопку...", "Система рассчитывает...", "Система отправляет уведомление..." -> это OK.
    4. Cтруктура: Проверь, что заполнены все поля (Название, Описание, Цели, Требования).

    ВАЖНО:
    - Если требование звучит как "Пользователь загружает файл резюме", это ОТЛИЧНОЕ требование. НЕ требуй указывать формат файла (.pdf/.csv) или метод API. Это задача разработчиков.
    - Ставь OK, если требования понятны заказчику и не содержат кода.

    Входные данные (JSON):
    {artifact_json}

    {format_instructions}
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt)])
    chain = prompt | llm | parser

    try:
        artifact_str = json.dumps(draft, ensure_ascii=False, indent=2)
    except:
        artifact_str = str(draft)

    try:
        decision = chain.invoke({
            "artifact_json": artifact_str,
            "format_instructions": parser.get_format_instructions()
        })

        print(f"\n[CRITIC] Verdict: {decision.verdict}")
        if decision.verdict == "REVISE":
            print(f"[CRITIC] Feedback: {decision.critique}")

        return {
            "critic_verdict": decision.verdict,
            "critic_feedback": decision.critique,
        }

    except Exception as e:
        print(f"Ошибка в critic_node: {e}")
        return {
            "critic_verdict": "REVISE",
            "critic_feedback": f"Произошла техническая ошибка при валидации: {e}",
        }