from graph import run_system

if __name__ == "__main__":
    project_idea = """
    Хочу сервис, который помогает HR-специалисту быстро находить кандидатов 
    по описанию вакансии и ранжировать их по релевантности.
    """

    print("Starting Analyst Agent System...")

    app, config, output = run_system(project_idea)

    print("If you want to continue from where the graph stopped:")
    print("  output = app.invoke(None, config=config)")
