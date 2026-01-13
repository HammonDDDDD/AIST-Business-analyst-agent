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
    verdict: Literal["OK", "REVISE"] = Field(description="Вердикт: OK или REVISE")
    critique: Optional[str] = Field(description="Текст замечаний (если REVISE)", default="")


def critic_node(state: dict):
    """
    Агент-критик.
    Принимает:
        - state['draft_artifact']: Черновик функциональных требований для проверки.
        - state['iteration_count']: Текущий счетчик итераций .
    Возвращает:
        - Обновленный state с ключами:
         "critic_verdict": "OK" или "REVISE".
         "critic_feedback": Замечания или причина решения.
         "iteration_count": Обновленный счетчик итераций.
    """

    draft = state.get("draft_artifact")
    iteration_count = state.get("iteration_count", 0)
    if not draft:
        return {
            "critic_verdict": "REVISE",
            "critic_feedback": "Артефакт пустой",
            "iteration_count": iteration_count
        }
    if iteration_count >= 3:
        return {
            "critic_verdict": "OK",
            "critic_feedback": "Лимит итераций исчерпан",
            "iteration_count": iteration_count
        }
    llm = ChatOpenAI(
        model="deepseek-chat",
        base_url=URL,
        api_key=DEEPSEEK_API,
        temperature=0.0
    )

    parser = PydanticOutputParser(pydantic_object=CriticDecision)
    system_prompt = """Ты - Старший Бизнес-аналитик. Твоя задача - валидировать Функциональные Требования (ФТ).
    Твоя цель: Убедиться, что требования описывают ПОВЕДЕНИЕ системы (User Story), а не реализацию.
    КРИТЕРИИ ОЦЕНКИ:
    1.ЗАПРЕЩЕНЫ технические детали: Нельзя писать про SQL, Python, REST API, JSON, эндпоинты, названия таблиц. Если это есть -> REVISE.
    2.ЗАПРЕЩЕНА "вода": Фразы "сделать красиво", "быстро работать", "быть удобным" -> REVISE.
    3.НУЖНА бизнес-логика: "Пользователь нажимает кнопку...", "Система рассчитывает...", "Система отправляет уведомление..." -> это OK.
    ВАЖНО:
    - Если требование звучит как "Пользователь загружает файл резюме", это ОТЛИЧНОЕ требование. НЕ требуй указывать формат файла (.pdf/.csv) или метод API. Это задача разработчиков, а не аналитиков.
    - Ставь OK, если требования понятны заказчику и не содержат кода.
    Входные данные: {artifact_json}
    {format_instructions}
    """

    prompt = ChatPromptTemplate.from_messages([("system", system_prompt)])
    chain = prompt | llm | parser

    try:
        artifact_str = json.dumps(draft, ensure_ascii=False)
    except:
        artifact_str = str(draft)

    try:
        decision = chain.invoke({
            "artifact_json": artifact_str,
            "format_instructions": parser.get_format_instructions()
        })

        new_iteration_count = iteration_count + 1 if decision.verdict == "REVISE" else iteration_count

        return {
            "critic_verdict": decision.verdict,
            "critic_feedback": decision.critique,
            "iteration_count": new_iteration_count
        }
    except Exception as e:
        return {
            "critic_verdict": "REVISE",
            "critic_feedback": f"Ошибка: {e}",
            "iteration_count": iteration_count
        }