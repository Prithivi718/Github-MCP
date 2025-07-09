# 🔧 GitHub Automation with MCP Tools

This project provides a modular, Python-based command-line and API toolkit to interact with GitHub using **MCP (Modular Command Plugins)**. Each feature is encapsulated as a Pydantic-based model, ensuring robust data validation and clean integration.

---

## 🚀 Features Overview

Each tool is built as a modular MCP plugin using `Pydantic` classes for structure and validation:

| MCP Tool         | Description                                |
|------------------|--------------------------------------------|
| `CreateRepo`     | Create a new GitHub repository             |
| `PushRepo`       | Push local repository to GitHub            |
| `SearchRepos`    | Search public repositories by keyword      |
| `SearchUsers`    | Find GitHub users based on queries         |
| `CreateIssue`    | Create a new issue in any repository       |
| `SearchIssues`   | Search issues across GitHub                |
| `AddComment`     | Add a comment to an existing issue         |

---

## 🧱 Technology Stack

- 🐍 **Python 3.8+**
- 🗃️ **Pydantic** for input schema and model validation
- 🔗 **Claude Desktop**
- 🧰 **Custom MCP plugin framework**
- 🔐 **OAuth Token-based GitHub Auth**

---
### Requirements 🔧
- Github Token



