# AIST-Business-analyst-agent

---

[![OSA-improved](https://img.shields.io/badge/improved%20by-OSA-yellow)](https://github.com/aimclub/OSA)

---

## Overview

This project provides an AI-powered business analyst assistant that helps users collaboratively develop project specifications. Through conversational interaction and iterative refinement cycles, it enables teams to create well-structured project requirements while filtering out technical details to maintain business focus.

---

## Table of Contents

- [Core Features](#core-features)
- [Installation](#installation)
- [Contributing](#contributing)
- [Citation](#citation)

---

## Core Features

1. **Multi-Agent Collaboration Workflow**: Orchestrates a collaborative workflow between AI agents (Analyst and Critic) with human feedback integration for iterative project artifact refinement
2. **Telegram Bot Interface**: Provides a conversational interface via Telegram for users to interact with the business analyst agent and receive project specifications
3. **Iterative Project Refinement**: Supports up to 3 revision cycles with automated critique and user feedback to progressively improve project requirements and specifications
4. **Structured Project Artifact Generation**: Generates well-structured project artifacts including title, description, goals, and functional requirements using Pydantic models for validation
5. **State Management with Checkpointing**: Maintains session state across iterations with memory-based checkpointing to preserve workflow progress and enable resumable sessions

---

## Installation

**Prerequisites:** requires Python ^3.10

Install AIST-Business-analyst-agent using one of the following methods:

**Build from source:**

1. Clone the AIST-Business-analyst-agent repository:
```sh
git clone https://github.com/HammonDDDDD/AIST-Business-analyst-agent
```

2. Navigate to the project directory:
```sh
cd AIST-Business-analyst-agent
```

3. Install the project dependencies:
```sh
pip install -r requirements.txt
```

---

## Contributing

- **[Report Issues](https://github.com/HammonDDDDD/AIST-Business-analyst-agent/issues)**: Submit bugs found or log feature requests for the project.

- **[Submit Pull Requests](https://github.com/HammonDDDDD/AIST-Business-analyst-agent/tree/master/.github/CONTRIBUTING.md)**: To learn more about making a contribution to AIST-Business-analyst-agent.

---

## Citation

If you use this software, please cite it as below.

### APA format:

    HammonDDDDD (2026). AIST-Business-analyst-agent repository [Computer software]. https://github.com/HammonDDDDD/AIST-Business-analyst-agent

### BibTeX format:

    @misc{AIST-Business-analyst-agent,
        author = {HammonDDDDD},
        title = {AIST-Business-analyst-agent repository},
        year = {2026},
        publisher = {github.com},
        journal = {github.com repository},
        howpublished = {\url{https://github.com/HammonDDDDD/AIST-Business-analyst-agent.git}},
        url = {https://github.com/HammonDDDDD/AIST-Business-analyst-agent.git}
    }
