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
    """
    A class representing a critic's decision with a verdict and critique.
    
        Class Attributes:
        - verdict: The decision outcome.
        - critique: The reasoning behind the decision.
    """

    verdict: Literal["OK", "REVISE"] = Field(description="Вердикт: OK (принять) или REVISE (отправить на доработку)")
    critique: Optional[str] = Field(description="Текст замечаний (обязательно, если REVISE)", default="")


def critic_node(state: dict):
    """
    Critic agent that validates functional requirements against business analysis criteria.
    
    Evaluates draft artifacts to ensure they describe system behavior rather than implementation details,
    focusing on business logic clarity and adherence to structured requirements format.
    
    Args:
        state (dict): The current state dictionary containing the draft artifact to validate.
            Must contain key 'draft_artifact' with the requirements draft to be evaluated.
    
    Returns:
        dict: Updated state dictionary with critic evaluation results, containing:
            - "critic_verdict" (str): Evaluation verdict - "OK" if requirements meet criteria, "REVISE" if modifications needed
            - "critic_feedback" (str): Detailed feedback explaining the verdict and suggested improvements
    
    WHY: This method ensures requirements maintain proper focus on business behavior rather than technical implementation,
    preventing premature technical specification and promoting clear, actionable user stories that accurately capture system functionality.
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
    1. ЗАПРЕЩЕНЫ технические детали: Нельзя писать про SQL, Python, REST API, JSON, эндпоинты, названия таблиц. Если это есть -> REVISE.
    2. ЗАПРЕЩЕНА "вода": Фразы "сделать красиво", "быстро работать", "быть удобным" -> REVISE.
    3. НУЖНА бизнес-логика: "Пользователь нажимает кнопку...", "Система рассчитывает...", "Система отправляет уведомление..." -> это OK.
    4. Cтруктура: Проверь, что заполнены все поля (Название, Описание, Цели, Требования).

    ПРИМЕРЫ ВАЛИДАЦИИ (FEW-SHOT):

    Пример 1:
    Вход: "ФТ-1: При нажатии кнопки данные отправляются в формате JSON через POST-запрос на сервер."
    Вердикт: REVISE
    Критика: "Требование содержит технические детали реализации (JSON, POST-запрос). Перепишите как действие пользователя или системы: 'При нажатии кнопки система сохраняет введенные данные'."

    Пример 2:
    Вход: "ФТ-2: Система должна быть интуитивно понятной для любого пользователя."
    Вердикт: REVISE
    Критика: "Требование слишком размытое ('интуитивно понятной'). Замените на конкретный сценарий использования или измеримый критерий."

    Пример 3:
    Вход: "ФТ-3: Пользователь загружает отчет в формате PDF, система извлекает из него итоговую сумму."
    Вердикт: OK
    Критика: "" (Указание формата PDF допустимо, так как это бизнес-требование к входным данным, а не внутренняя реализация).

    Пример 4:
    Вход: "ФТ-4: Система рассчитывает скидку на основе истории покупок и отправляет уведомление на email."
    Вердикт: OK
    Критика: ""

    Анализируй входные требования так же строго.

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