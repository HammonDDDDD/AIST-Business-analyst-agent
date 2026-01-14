from graph import compile_graph
from dotenv import load_dotenv
import json


load_dotenv()


def main():
    app = compile_graph()
    config = {"configurable": {"thread_id": "session_1"}}

    initial_state = {
        "project_description": "Хочу сервис для управления задачами в команде с уведомлениями и дедлайнами.",
        "draft_artifact": None,
        "critic_feedback": "",
        "critic_verdict": None,
        "revision_count": 0,
        "user_feedback": "",
        "user_has_provided_feedback": False,
    }

    print("=== ЗАПУСК АГЕНТНОЙ СИСТЕМЫ ===")

    # Первый проход
    app.invoke(initial_state, config=config)

    iteration = 1
    while iteration <= 3:
        print(f"\n=== ИТЕРАЦИЯ {iteration} ===")

        state = app.get_state(config)

        artifact = state.values.get('draft_artifact')
        if artifact:
            print("Название:", artifact.get('title', 'N/A'))
            print("Описание:", artifact.get('description', 'N/A'))
            print("Цели:", artifact.get('goals', []))
            print("Требования:", artifact.get('requirements', []))

            feedback = input("\nОтзыв (Enter=OK, revise=доработать): ").strip()

            if feedback.lower() == 'ok':
                app.invoke({"user_has_provided_feedback": False}, config=config)
            else:
                app.invoke({"user_has_provided_feedback": True, "user_feedback": feedback}, config=config)

            state = app.get_state(config)
            if not state.next:
                print("\n=== ПРОЕКТ УТВЕРЖДЁН ===")
                break

            iteration += 1


if __name__ == "__main__":
    main()