from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import ProjectState
from nodes_analyst import analyst_node
from nodes_critic import critic_node
from human_nodes import human_node


def critic_router(state: ProjectState) -> str:
    """
    Routes the next step after critique based on the current project state.
    
    Decides whether to continue with automated revisions or return control to human input
    based on the critique verdict and revision count.
    
    Args:
        state (ProjectState): The current project state containing critique verdict
            and revision count.
    
    Returns:
        str: The next step identifier - 'human' for human input or 'increment' for
            another automated revision cycle.
    """

    if state["critic_verdict"] == "OK":
        return "human"
    elif state["revision_count"] < 3:
        return "increment"
    else:
        return "human"


def human_router(state: ProjectState) -> str:
    """
    Routes the workflow based on whether the user has provided feedback.
    
    Determines the next step in the project workflow by checking if human feedback has been received.
    If feedback is present, the process continues to the increment phase for further refinement.
    Otherwise, the workflow terminates since no further human input is available.
    
    Args:
        state (ProjectState): The current state of the project containing user feedback status.
    
    Returns:
        str: The next step identifier - 'increment' to continue refinement or 'END' to terminate.
    """

    if state["user_has_provided_feedback"]:
        return "increment"
    else:
        return "END"


def increment_revision_count(state: ProjectState) -> dict:
    """
    Increments the revision counter to track iterations through the feedback cycle.
    
    Args:
        state (ProjectState): The current project state containing the revision count.
    
    Returns:
        dict: Updated state with the incremented revision count.
    
    WHY: To maintain an accurate count of revision cycles, enabling the system to track progress through iterative improvement loops and manage workflow state transitions.
    """

    new_count = state["revision_count"] + 1
    print(f"\n[GRAPH] Incrementing revision count: {state['revision_count']} -> {new_count}")

    return {
        "revision_count": new_count,
    }

def build_graph() -> StateGraph:
    """
    Builds a state machine graph for managing collaborative document generation workflow.
    
    The graph defines the sequence of states and transitions between different roles (analyst, critic, human) 
    to enable iterative refinement cycles where documents are created, reviewed, and improved through feedback.
    
    Args:
        None
    
    Returns:
        StateGraph: Configured state graph with nodes and edges defining the workflow transitions.
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
    Compiles a workflow graph with human interaction points for iterative refinement.
    
    The method creates an executable workflow that pauses before and after human interaction steps,
    allowing for iterative feedback cycles between automated processing and human input.
    
    Args:
        None
    
    Returns:
        CompiledGraph: A compiled workflow graph configured with checkpointing and human interaction points.
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
        project_description: The initial description of the project to be analyzed.
    
    Returns:
        ProjectState: A dictionary containing the initial state with default values for all project tracking fields.
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
    Main function to execute the system workflow.
    
    Initializes and runs the collaborative graph-based system that manages iterative
    feedback cycles between AI agents and human input. The system starts with an initial
    project state and maintains session configuration for continued execution.
    
    Args:
        project_description: Initial project description to bootstrap the system
    
    Returns:
        tuple: Contains three elements:
            - app: The compiled graph application for continued execution
            - config: Session configuration with thread identifier
            - output: Initial execution output state
    
    The function sets up the environment for iterative refinement cycles where
    the system can pause for human input and resume execution when needed.
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
