# SRS Outline

## 1. Introduction
- Project: Smart Student Assistant
- Problem: Students need a simple place to organize courses and study tasks and interact with their own data through natural language.

## 2. Functional Requirements
- Register/login/logout
- Role-based access
- Course management
- Task management
- Context-aware AI chat
- Agent tool execution
- Confirmation before deletion

## 3. Non-Functional Requirements
- Security
- Usability
- Maintainability
- Data integrity
- Clear architecture

## 4. RBAC Matrix
| Feature | Student | Instructor | Admin |
|---|---:|---:|---:|
| Own tasks | CRUD | - | View |
| Courses | Read | CRUD | CRUD |
| AI assistant | Yes | Yes | Yes |
| Users | No | No | CRUD |

## 5. ERD
User 1---1 Profile
User M---N Course
User 1---N Task
Course 1---N Task
User 1---N ChatMessage

## 6. User Journey
Register -> Login -> Dashboard -> Manage Courses/Tasks -> Ask AI -> Agent validates -> Tool executes -> Result shown.

## 7. AI Agent Design
Persona:
- Helpful student productivity assistant.
- Uses tools for database actions.
- Never invents database information.
- Must respect authorization.
- Requires confirmation before deletion.

Tools:
1. get_my_tasks
2. add_task
3. delete_task

## 8. Git/GitHub
Use Issues, feature branches, Conventional Commits and PRs.
