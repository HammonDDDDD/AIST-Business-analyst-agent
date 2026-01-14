import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
from state import ProjectArtifact

load_dotenv()

DEEPSEEK_API = os.getenv("DEEPSEEK_API_KEY")
URL = os.getenv("DEEPSEEK_BASE_URL")


def analyst_node(state: dict):
    """
    Агент-аналитик.
    Принимает:
      - state['project_description']: Исходная идея пользователя.
      - state['critic_feedback']: Замечания от критика.
      - state['user_feedback']: Замечания от человека.
    Возвращает:
      - Обновленный state с ключом 'draft_artifact'.
    """
    llm = ChatOpenAI(
        model="deepseek-chat",
        base_url=URL,
        api_key=DEEPSEEK_API,
        temperature=0.7
    )

    parser = PydanticOutputParser(pydantic_object=ProjectArtifact)

    system_prompt = """Ты - опытный Бизнес-аналитик. Твоя задача - превратить короткую идею проекта в структурированное описание.

    Твой ответ ДОЛЖЕН быть валидным JSON, соответствующим схеме:
    {format_instructions}

    Требования к заполнению:
    1. Требования (requirements) должны быть списком объектов с id (ФТ-1, ФТ-2) и описанием.
    2. Описание требований должно быть конкретным и проверяемым (User Story), без технических деталей реализации (БД, язык программирования).
    3. Цели (goals) должны быть четкими и измеримыми.

    ПРИМЕРЫ ХОРОШИХ И ПЛОХИХ ТРЕБОВАНИЙ (FEW-SHOT):

    ❌ ПЛОХО (Техническая реализация):
    "Использовать Python и библиотеку Pandas для анализа данных."
    "Данные сохраняются в таблицу users базы PostgreSQL."
    "Создать эндпоинт GET /api/v1/search."

    ✅ ХОРОШО (Бизнес-логика / User Story):
    "Система автоматически анализирует загруженный файл и выделяет ключевые метрики."
    "Система сохраняет информацию о профиле пользователя."
    "Пользователь может искать товары по названию и категории."

    ❌ ПЛОХО (Вода):
    "Интерфейс должен быть удобным и красивым."
    "Система должна работать быстро."

    ✅ ХОРОШО (Конкретика):
    "Интерфейс позволяет пользователю оформить заказ не более чем за 3 клика."
    "Время отклика системы на поисковый запрос не превышает 2 секунд."

    Следуй этому стилю при генерации ответа.
    """

    user_message = f"Идея проекта: {state.get('project_description', '')}"

    critic_feedback = state.get("critic_feedback")
    user_feedback = state.get("user_feedback")

    if critic_feedback:
        user_message += f"\n\nПРЕДЫДУЩАЯ ВЕРСИЯ БЫЛА ОТКЛОНЕНА КРИТИКОМ.\nЗамечания критика: {critic_feedback}\nИсправь артефакт с учетом этих замечаний."

    if user_feedback:
        user_message += f"\n\nКОММЕНТАРИЙ ПОЛЬЗОВАТЕЛЯ: {user_feedback}\nВнеси правки согласно пожеланиям пользователя."

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{user_message}")
    ])

    chain = prompt | llm | parser

    try:
        result_artifact = chain.invoke({
            "format_instructions": parser.get_format_instructions(),
            "user_message": user_message
        })

        return {"draft_artifact": result_artifact.model_dump()}

    except Exception as e:
        print(f"Ошибка в analyst_node: {e}")
        return {"draft_artifact": None}