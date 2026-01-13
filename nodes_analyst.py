import os
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from dotenv import load_dotenv
load_dotenv()

DEEPSEEK_API = os.getenv("DEEPSEEK_API_KEY")
URL = os.getenv("DEEPSEEK_BASE_URL")
class ProjectArtifact(BaseModel):
    project_name: str = Field(description="Название проекта")
    description: str = Field(description="Краткое описание проекта и его назначения")
    goals: List[str] = Field(description="Список из 1-2 целей проекта")
    functional_requirements: List[str] = Field(description="Список функциональных требований (ФТ-1, ФТ-2...)")

def analyst_node(state: dict):
    """
    Агент-аналитик.
    Принимает:
      - state['project_idea']: Исходная идея пользователя.
      - state['critic_feedback']: Замечания от критика, если это не первая итерация.
      - state['human_feedback']: Замечания от человека.
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
    Требования к функциональным требованиям:
    - Они должны быть конкретными и проверяемыми.
    - Не используй технические детали (какой язык программирования, база данных), описывай логику пользователя.
    """
    user_message = f"Идея проекта: {state.get('project_idea', '')}"

    critic_feedback = state.get("critic_feedback")
    human_feedback = state.get("human_feedback")
    if critic_feedback:
        user_message += f"\n\nПРЕДЫДУЩАЯ ВЕРСИЯ БЫЛА ОТКЛОНЕНА КРИТИКОМ.\nЗамечания критика: {critic_feedback}\nИсправь артефакт с учетом этих замечаний."

    if human_feedback:
        user_message += f"\n\nКОММЕНТАРИЙ ПОЛЬЗОВАТЕЛЯ: {human_feedback}\nВнеси правки согласно пожеланиям пользователя."
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