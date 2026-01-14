"""
TODO:
1. Рендер ProjectArtifact в красивый Markdown
2. Вывести Markdown в консоль/веб/Telegram
3. Прочитать input от пользователя
4. Обновить state на основе input
"""


def human_node(state):
    artifact = state.get('draft_artifact', {})
    print("\nНазвание:", artifact.get('title', 'N/A'))
    print("Описание:", artifact.get('description', 'N/A'))
    print("Цели:", artifact.get('goals', []))
    print("Требования:", artifact.get('functional_requirements', []))

    feedback = input("Отзыв (Enter=OK): ").strip()

    if not feedback or feedback.lower() == 'ok':
        return {
            "user_feedback": "APPROVED",
            "user_has_provided_feedback": False,  # ← False = END
            "status": "END"
        }
    return {
        "user_feedback": feedback,
        "user_has_provided_feedback": True,   # ← True = revise
        "status": "HUMAN_REVISE"
    }
