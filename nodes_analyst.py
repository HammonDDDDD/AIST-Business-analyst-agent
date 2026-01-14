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