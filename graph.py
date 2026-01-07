from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import ProjectState
from nodes_analyst import analyst_node
from nodes_critic import critic_node
from nodes_human import human_node


def critic_router(state: ProjectState) -> str:
    """ ROUTER: Решить, что делать после критика """

    if state["critic_verdict"] == "OK":
        return "human"
    elif state["revision_count"] < 3:
        return "increment"
    else:
        return "human"


def human_router(state: ProjectState) -> str:
    """ ROUTER: Решить, что делать после человека """

    if state["user_has_provided_feedback"]:
        return "increment"
    else:
        return "END"


def increment_revision_count(state: ProjectState) -> dict:
    """ Инкрементирует счетчик попыток """

    new_count = state["revision_count"] + 1
    print(f"\n[GRAPH] Incrementing revision count: {state['revision_count']} -> {new_count}")

    return {
        "revision_count": new_count,
    }

def build_graph() -> StateGraph:
    """ Сборка графа состояний """

    graph = StateGraph(ProjectState)

    graph.add_node("analyst", analyst_node)
    graph.add_node("critic", critic_node)
    graph.add_node("human", human_node)
    graph.add_node("increment", increment_revision_count)

    graph.add_edge(START, "analyst")
    graph.add_edge("analyst", "critic")

    graph.add_conditional_edges(
        "critic",
        critic_router,
        {
            "human": "human",
            "increment": "increment",
        }
    )

    graph.add_edge("increment", "analyst")

    graph.add_conditional_edges(
        "human",
        human_router,
        {
            "increment": "increment",
            "END": END,
        }
    )

    return graph


def compile_graph():
    """ Компиляция графа с поддержкой Human-in-the-loop """

    graph = build_graph()

    checkpointer = MemorySaver()

    compiled_graph = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human"],
    )

    return compiled_graph


def initialize_state(project_description: str) -> ProjectState:
    """ Инициализация начального состояние графа """

    return {
        "project_description": project_description,
        "draft_artifact": None,
        "critic_feedback": "",
        "critic_verdict": None,
        "revision_count": 0,
        "user_feedback": "",
        "user_has_provided_feedback": False,
    }


def run_system(project_description: str):
    """ Главная функция для запуска всей системы """

    app = compile_graph()
    initial_state = initialize_state(project_description)

    thread_id = "session_1"

    config = {"configurable": {"thread_id": thread_id}}

    print("\n[SYSTEM] Starting graph execution...")
    output = app.invoke(initial_state, config=config)

    print("\n[SYSTEM] Graph stopped at human node (waiting for user input)")
    print("[SYSTEM] To continue, call: app.invoke(None, config=config)")

    return app, config, output

if __name__ == "__main__":
    print("\n[TEST] Building graph...")
    app = compile_graph()

    print("[TEST] Graph structure:")
    print(app.get_graph().draw_ascii())

    print("\n[TEST] Graph is compiled and ready for use!")
