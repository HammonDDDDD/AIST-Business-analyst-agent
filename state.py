from typing import TypedDict, List, Literal
from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """Одно функциональное требование"""

    id: str = Field(description="Уникальный идентификатор (ФТ-1, ФТ-2, ...)")

    description: str = Field(description="Описание требования (конкретное, проверяемое, без технических деталей)")


class ProjectArtifact(BaseModel):
    """Итоговый артефакт проекта"""

    title: str = Field(
        description="Название проекта"
    )
    description: str = Field(
        description="Краткое текстовое описание того, что это за система и для чего она нужна"
    )
    goals: List[str] = Field(
        description="1-2 четко сформулированные цели"
    )
    functional_requirements: List[Requirement] = Field(
        description="Функциональные требования (ФТ-1, ФТ-2, ...)"
    )


class ProjectState(TypedDict):
    """
    Общее состояние для всех узлов графа.

    - analyst_node обновляет: draft_artifact, revision_count
    - critic_node обновляет: critic_feedback, critic_verdict
    - human_node обновляет: user_feedback, user_has_provided_feedback
    """

    # Текстовое описание идеи проекта на естественном языке (русский, 1-3 абзаца)
    project_description: str

    # Сгенерированный артефакт
    draft_artifact: ProjectArtifact | None

    # Текстовое описание замечаний от критика
    critic_feedback: str

    # Вердикт критика
    critic_verdict: Literal["OK", "REVISE"] | None

    # Счётчик попыток доработки (максимум три)
    revision_count: int

    # Замечания пользователя (свободный текст)
    user_feedback: str

    # Флаг: пользователь оставил замечания?
    user_has_provided_feedback: bool