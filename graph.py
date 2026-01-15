from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import ProjectState
from nodes_analyst import analyst_node
from nodes_critic import critic_node
from human_nodes import human_node


def critic_router(state: ProjectState) -> str:
    """
    ROUTER: Determine next step after critique feedback.
    
    Decides whether to continue with automated revisions or return control to human
    based on critique verdict and revision count limits.
    
    Args:
        state (ProjectState): The current project state containing critique verdict
            and revision count information.
    
    Returns:
        str: Next step identifier - "human" to return control to human, 
            "increment" to continue with automated revisions.
    """

    if state["critic_verdict"] == "OK":
        return "human"
    elif state["revision_count"] < 3:
        return "increment"
    else:
        return "human"


def human_router(state: ProjectState) -> str:
    """
    Determine the next step after human interaction based on feedback status.
    
    Args:
        state (ProjectState): The current state of the project containing user feedback information.
    
    Returns:
        str: "increment" if user has provided feedback to continue the cycle, "END" to terminate the process otherwise.
    
    Why: This method controls the flow of the iterative development process by checking whether the user has provided feedback. If feedback is present, it signals to continue with the next cycle ("increment"), allowing for further refinement. If no feedback is given, it ends the process ("END"), preventing unnecessary iterations without user input.
    """

    if state["user_has_provided_feedback"]:
        return "increment"
    else:
        return "END"


def increment_revision_count(state: ProjectState) -> dict:
    """
    Increments the revision counter to track the number of analysis iterations.
    
    This method maintains a count of how many times the project has undergone 
    analysis-review cycles, allowing the system to manage iterative development 
    processes and track progress through multiple revision stages.
    
    Args:
        state (ProjectState): The current project state containing the revision count
    
    Returns:
        dict: Updated state with the incremented revision count
    """

    new_count = state["revision_count"] + 1
    print(f"\n[GRAPH] Incrementing revision count: {state['revision_count']} -> {new_count}")

    return {
        "revision_count": new_count,
    }

def build_graph() -> StateGraph:
    """
    Builds a state graph for managing iterative project development cycles.
    
    The graph orchestrates a workflow that alternates between automated analysis and human feedback stages, allowing for continuous refinement of project artifacts through revision cycles.
    
    Args:
        None
    
    Returns:
        StateGraph: A configured state graph defining the workflow transitions between analysis, critique, human input, and revision steps.
    """

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
    """
    Compile an executable workflow graph with human interaction points.
    
    Args:
        None
    
    Returns:
        compiled_graph: A compiled workflow graph configured to pause execution before and after human interaction steps, allowing for iterative feedback integration.
        
    The method enables collaborative refinement by interrupting workflow execution at designated human interaction steps, ensuring human input can be incorporated between automated processing stages.
    """

    graph = build_graph()

    checkpointer = MemorySaver()

    compiled_graph = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human"],
        interrupt_after=["human"],
    )

    return compiled_graph


def initialize_state(project_description: str) -> ProjectState:
    """
    Initialize the initial state of the project graph.
    
    Args:
        project_description: The initial description of the project.
    
    Returns:
        ProjectState: A dictionary containing the initial state with keys for project description,
        draft artifact, critic feedback, critic verdict, revision count, user feedback,
        and user feedback status. This establishes the baseline state for iterative development cycles.
        
    Why: To establish a clean starting point for the project development process, providing
    a structured container for tracking progress through multiple iterations of analysis,
    feedback, and revision cycles.
    """

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
    """
    Main function to launch the state-based agent system.
    
    Initializes the application graph and state, then executes the initial workflow cycle.
    The system stops at human interaction points to allow for iterative feedback integration.
    
    Args:
        project_description: A string describing the project to be analyzed and developed.
    
    Returns:
        tuple: A tuple containing:
            - app: The compiled application graph for further interactions.
            - config: Configuration dictionary with thread identifier for session management.
            - output: The initial state output from the first graph execution cycle.
    """

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
    png_bytes = app.get_graph().draw_mermaid_png()

    with open("graph.png", "wb") as f:
        f.write(png_bytes)

    print("[TEST] Graph structure:")
    print(app.get_graph().draw_ascii())

    print("\n[TEST] Graph is compiled and ready for use!")
