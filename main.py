from graph import compile_graph
from dotenv import load_dotenv
import json


load_dotenv()


def main():
    app = compile_graph()
    config = {"configurable": {"thread_id": "session_1"}}

    initial_state = {
        "project_description": "Хочу сервис, который помогает HR-специалисту быстро находить кандидатов по описанию вакансии и ранжировать их по релевантности",
        "draft_artifact": None,
        "critic_feedback": "",
        "critic_verdict": None,
        "revision_count": 0,
        "user_feedback": "",
        "user_has_provided_feedback": False,
    }

    print("=== ЗАПУСК АГЕНТНОЙ СИСТЕМЫ ===")

    app.invoke(initial_state, config=config)

    iteration = 1
    while iteration <= 3:
        print(f"\n=== ИТЕРАЦИЯ {iteration} ===")

        state = app.get_state(config)

        artifact = state.values.get('draft_artifact')
        if artifact:
            md_text = f"# {artifact.get('title', 'Без названия')}\n\n"
            md_text += f"## Описание\n{artifact.get('description', '')}\n\n"
            md_text += "## Цели\n" + "\n".join([f"- {g}" for g in artifact.get('goals', [])]) + "\n\n"
            md_text += "## Функциональные требования\n"

            reqs = artifact.get('functional_requirements') or artifact.get('requirements') or []
            for r in reqs:
                r_id = r.get('id') if isinstance(r, dict) else getattr(r, 'id', 'N/A')
                r_desc = r.get('description') if isinstance(r, dict) else getattr(r, 'description', '')
                md_text += f"- **{r_id}**: {r_desc}\n"

            print("\n" + "=" * 40)
            print(md_text)
            print("=" * 40 + "\n")

            with open("project_result.md", "w", encoding="utf-8") as f:
                f.write(md_text)
            print("Файл 'project_result.md' успешно сохранен")

            feedback = input("\nОтзыв (OK=правок не требуется, revise=необходимо доработать): ").strip()

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