# 🎓 Smart Student Assistant — الخطة الكاملة للمشروع (10 مراحل)

> **قاعدة ذهبية طول المشروع:** كل مرحلة ليها برومبت واحد بس. متدّيش الـAI أكتر من مرحلة في مرة واحدة، ومتنتقلش لمرحلة جديدة إلا بعد ما تتأكد إن المرحلة الحالية شغالة 100%. ده بيوفر توكن، ويمنع الـAI من "العجن" في حاجات مش مطلوبة، وبيخليك فاهم كل سطر لما الدكتور يسألك.

---

## 📌 جدول المراحل السريع

| # | المرحلة | البند اللي تغطيه | الحالة |
|---|---------|-------------------|--------|
| 1 | Django + PostgreSQL + MVT Setup | Django (15) | ☐ |
| 2 | Models + Relationships | PostgreSQL (10) | ☐ |
| 3 | Authentication + RBAC | Security (5) | ☐ |
| 4 | Courses + Tasks CRUD | Functionality | ☐ |
| 5 | Frontend UX/UI | Frontend (10) | ☐ |
| 6 | Chat UI + Context-Aware Chat | Chatbot (10) | ☐ |
| 7 | Agentic AI + Tools | Agentic AI (15) | ☐ |
| 8 | Security + Validation Review | Security | ☐ |
| 9 | Git/GitHub + SRS | Git (10) + SRS (5) | ☐ |
| 10 | Testing + Demo + Presentation | Defense (10) | ☐ |

**قاعدة بعد كل مرحلة:** اعمل `git commit` بصيغة Conventional Commits (مثال: `feat(auth): add login flow`) قبل ما تبدأ المرحلة اللي بعدها.

---

## 🔵 المرحلة 1 — التأكد إن Django شغال (Setup فقط)

**الهدف:** التأكد إن البيئة والمشروع شغالين صح، من غير أي إضافة فعلية.

**⚠️ ممنوع في هذه المرحلة:** إنشاء Models، صفحات، أو أي Feature. البرومبت مقفول على الفحص والتصحيح البسيط فقط.

### البرومبت:
```
We are building a beginner-friendly graduation project called Smart Student Assistant.

The project must follow the provided graduation project requirements:
- Django MVT backend
- PostgreSQL database
- HTML5, CSS3, JavaScript ES6+
- Authentication and RBAC
- One-to-Many and Many-to-Many relationships
- Context-aware AI chatbot
- Real Agentic AI using Python functions/tools
- Validation and authorization before database actions
- Explicit confirmation before deletion
- Git/GitHub with Conventional Commits
- SRS documentation

Do NOT build everything at once.

For this step only:
1. Inspect the current project structure.
2. Check whether Django is installed correctly.
3. Check the Django configuration.
4. Run/check `python manage.py check`.
5. Do not make unnecessary changes.
6. If something is wrong, explain the problem and fix only what is necessary.

After finishing, tell me:
- What you checked
- What you changed
- Why you changed it
- The exact command I should run next.
```

### بعد ما الـAI يخلص (تنفذها إنت بنفسك):
```bash
python manage.py check
python manage.py runserver
```
افتح: `http://127.0.0.1:8000/`

**✅ معيار النجاح:** ظهور `System check identified no issues (0 silenced).` والسيرفر يفتح من غير Error.

**🚫 لا تنتقل للمرحلة 2 إلا بعد التأكد من ده.**

---

## 🟢 المرحلة 2 — قاعدة البيانات (Models + Relationships)

**الهدف:** بناء الـModels الأساسية فقط، بعلاقات One-to-Many و Many-to-Many.

### مخطط العلاقات المستهدف:
```
User ─────< Task
User >────< Course
Course ───< Task
```

### البرومبت:
```
Now implement the database layer only.

Requirements:
1. Use Django ORM.
2. PostgreSQL is the target database.
3. Keep the database simple and normalized.
4. Create these main entities:
   - User/Profile
   - Course
   - Task
   - ChatMessage
5. Include:
   - One-to-Many relationships
   - Many-to-Many relationship between students and courses
6. A Task must belong to its owner.
7. Use meaningful related_name values.
8. Add useful __str__ methods.
9. Do not use raw SQL.
10. Do not add unnecessary models.

Before changing files, explain the model relationships briefly.
Then implement them.

After implementation:
- Run/check migrations.
- Explain every model and relationship in beginner-friendly language.
- Tell me exactly which commands to run.
```

### بعد التنفيذ:
```bash
python manage.py makemigrations
python manage.py migrate
```

**✅ معيار النجاح:** Migrations تتعمل من غير Error، والجداول تظهر في PostgreSQL.

**🚫 لا تنتقل للمرحلة 3 إلا بعد التأكد من ده.**

---

## 🟡 المرحلة 3 — Authentication + RBAC

**الهدف:** تسجيل دخول/خروج، وأدوار (Student / Instructor / Admin) بصلاحيات مختلفة.

### البرومبت:
```
Implement Authentication and RBAC only.

Requirements:
- Use Django's built-in authentication system.
- Do not create a custom password hashing system.
- Users must have roles:
  Student
  Instructor
  Admin
- Passwords must be securely hashed by Django.
- Protect authenticated pages with login_required.
- Add simple role-based permission checks.
- Students can manage their own tasks.
- Instructors can manage courses.
- Admin has full management access.

Keep the implementation beginner-friendly.

Do not implement the AI Agent yet.

After implementation, explain:
1. How login works.
2. How passwords are stored securely.
3. How roles work.
4. How authorization prevents users from accessing unauthorized data.
```

**✅ معيار النجاح:** تقدر تسجل Student و Instructor، وكل واحد يشوف بس اللي يخصه.

**🚫 لا تنتقل للمرحلة 4 إلا بعد التأكد من ده.**

---

## 🟠 المرحلة 4 — Courses + Tasks CRUD

**الهدف:** كل طالب يعمل Create/Read/Update/Delete لـTasks بتاعته فقط، وده أساس عمل الـAgent بعدين.

### البرومبت:
```
Implement CRUD functionality only for Courses and Tasks.

Requirements:
1. A student can Create, Read, Update, and Delete only their own tasks.
2. A student can enroll in courses (Many-to-Many).
3. An instructor can Create, Read, Update, and Delete their own courses.
4. Every query must filter by the current logged-in user (ownership check),
   e.g. Task.objects.filter(id=task_id, owner=request.user) — never a plain .get(id=...).
5. Do not allow a user to view or modify another user's tasks under any condition.
6. Use Django forms for validation of user input.
7. Do not implement the AI Assistant page yet — this stage is pure CRUD only.

After implementation, explain:
1. How ownership filtering prevents users from accessing others' data.
2. Which views/URLs were added and what each one does.
3. How to manually test that Ahmed cannot see or delete Mohamed's task.
```

**✅ معيار النجاح:** تجرب بحسابين مختلفين، وتتأكد إن كل واحد معزول عن التاني تمامًا.

**🚫 لا تنتقل للمرحلة 5 إلا بعد التأكد من ده.**

---

## 🔴 المرحلة 5 — Frontend UX/UI

**الهدف:** واجهة مستخدم منظمة وشكلها محترم (مش HTML بدائي)، بما إن البند ده وحده بـ10 نقاط.

### هيكل الصفحات المستهدف:
```
        Dashboard
             │
   ┌─────────┼─────────┐
   ↓         ↓         ↓
Courses    Tasks      AI Assistant
```
+ صفحات Login / Register.

### البرومبت:
```
Implement the frontend UI only, on top of the existing backend. Do not touch models,
authentication logic, or business logic in this step.

Requirements:
1. Use HTML5, CSS3, and JavaScript ES6+ only (no frontend framework needed).
2. Build a base template with a consistent navbar and layout.
3. Pages needed: Login, Register, Dashboard, Courses, Tasks, AI Assistant.
4. Dashboard should give quick access/links to Courses, Tasks, and AI Assistant.
5. Use clean, modern, readable styling (spacing, consistent colors, responsive basics).
6. Show clear success/error messages (e.g. Django messages framework) for form actions.
7. Do not add any JavaScript-based API calls yet — this stage is UI structure and
   styling only, not the chatbot logic.

After implementation, explain:
1. The template structure (base template + inheritance).
2. Where static files (CSS/JS) are located.
3. How to preview each page.
```

**✅ معيار النجاح:** كل الصفحات بتفتح، الشكل موحّد، والتنقل بينهم سهل.

**🚫 لا تنتقل للمرحلة 6 إلا بعد التأكد من ده.**

---

## 🤖 المرحلة 6 — Chat UI + Context-Aware Chatbot

**الهدف:** شات بواجهة بسيطة، والردود مبنية على بيانات المستخدم الحقيقية من الـDB (مش تخمين).

### الفلو المستهدف:
```
Chat UI → Django View → Agent → LLM
```

### البرومبت:
```
Implement the chat UI and a context-aware chatbot only. Do NOT implement
tool-calling / agentic actions yet — this stage is read-only conversation.

Requirements:
1. Build a simple chat interface (message list + input box) on the AI Assistant page.
2. Create a Django view that receives the user's message.
3. Before calling the LLM, fetch the current logged-in user's real data
   (their tasks, enrolled courses) from the database.
4. Pass that real data into the LLM prompt as context, so answers are grounded
   in actual data, not guesses.
5. Save each exchange (user message + AI reply) in the ChatMessage model.
6. The chatbot should be able to correctly answer questions like "What tasks do I have?"
   using only that user's own data.
7. Do not allow the chatbot to modify the database in this step — it only reads and answers.

After implementation, explain:
1. How user data is fetched and injected into the prompt (the context-building step).
2. How chat history is stored.
3. How to test that the chatbot's answers match what's actually in the database.
```

**✅ معيار النجاح:** تسأل الشات "What tasks do I have?" ويرد ببياناتك الحقيقية بس.

**🚫 لا تنتقل للمرحلة 7 إلا بعد التأكد من ده.**

---

## 🧠 المرحلة 7 — Agentic AI + Tools (أهم مرحلة)

**الهدف:** الـAI مش بس بيرد، لازم يستخدم Tools (Python functions) عشان يعمل أكشن فعلي، مع تأكيد قبل أي حذف.

### الفلو المستهدف:
```
User Goal → LLM → Choose Tool → Python Function → Validation → Database → Result → LLM → User
```

### البرومبت:
```
Now upgrade the chatbot into a real Agentic AI with tool-calling. Build on top of
the existing context-aware chat from the previous step — do not rebuild it from scratch.

Requirements:
1. Implement these Python tool functions:
   - get_my_tasks()
   - add_task(title, ...)
   - delete_task(task_id)
2. Every tool function must:
   - Only operate on the currently logged-in user's own data.
   - Validate its inputs before touching the database.
3. The LLM must decide which tool to call based on the user's natural language message
   (e.g. "Show me my tasks" → get_my_tasks(), "Add a task called X" → add_task()).
4. For delete_task specifically: the Agent must NOT delete immediately. It must first
   ask "Are you sure you want to delete this task?" and only call delete_task() after
   the user explicitly confirms (e.g. replies "Yes").
5. After a tool runs, the result must be passed back to the LLM to generate a natural
   language response to the user (not just raw data).
6. Do not let the LLM construct or run any raw SQL or ORM queries directly — it may
   only call the predefined tool functions.

After implementation, explain:
1. How the LLM selects which tool to call.
2. How the delete confirmation flow works step by step.
3. How to manually test all three tools end to end.
```

**✅ معيار النجاح:** تجرب الثلاث سيناريوهات:
- "Show me my tasks" → يرجع مهامك.
- "Add a task called Django Project" → يضيفها.
- "Delete my Django Project task" → يسأل تأكيد الأول، وبعد "Yes" يحذف.

**🚫 لا تنتقل للمرحلة 8 إلا بعد التأكد من الثلاثة كاملين.**

---

## 🔐 المرحلة 8 — Security + Validation Review

**الهدف:** مراجعة أمنية شاملة للمشروع كله — مش إضافة Features جديدة.

### الفلو الصحيح المطلوب تأكيده:
```
User → Agent → Python Tool → Django ORM → PostgreSQL
```
(الـUser ممنوع يوصل لأي طبقة أعلى من الـAgent مباشرة، وممنوع أي SQL خام.)

### البرومبت:
```
Do not add new features. This step is a security and validation review of the
entire existing project.

Review and fix, if needed:
1. Every database query that fetches or modifies a specific record must filter
   by the current logged-in user (ownership), e.g.:
   Task.objects.filter(id=task_id, owner=request.user)
   and never a plain Task.objects.get(id=task_id).
2. Every view must check authentication (login_required) and role-based
   authorization where relevant.
3. Every Agent tool function must re-validate authorization itself, even if the
   view already checked it (defense in depth).
4. No raw SQL anywhere in the codebase.
5. All user input (forms and chat messages) must be validated before use.
6. Confirm the delete_task confirmation flow cannot be bypassed.

After the review, give me:
1. A short list of any issues found and what you fixed.
2. Confirmation that no raw SQL exists in the project.
3. Confirmation that ownership checks exist on every task/course query.
```

**✅ معيار النجاح:** تقرير واضح من الـAI بالمشاكل اللي لقاها (لو فيه) وإصلاحها.

**🚫 لا تنتقل للمرحلة 9 إلا بعد التأكد من ده.**

---

## 📚 المرحلة 9 — Git/GitHub Strategy + SRS Documentation

**الهدف:** توثيق منظم (SRS) + تاريخ Commits واضح ومتدرج، مش Commit واحد ضخم.

### هيكل المستندات المستهدف:
```
docs/
├── REQUIREMENTS_MAP.md
├── SRS_OUTLINE.md
└── GIT_STRATEGY.md
```

### البرومبت:
```
This step is documentation only — do not change any application code.

Requirements:
1. Update docs/SRS_OUTLINE.md to include, based on the actual current implementation:
   - Introduction
   - Problem statement
   - Functional requirements
   - Non-functional requirements
   - RBAC matrix (roles vs permissions)
   - Architecture overview (MVT + Agent flow)
   - ERD (entities and relationships implemented so far)
   - Key user journeys (register → login → dashboard → tasks/courses → AI assistant)
   - Agent design (tools, confirmation flow)
2. Update docs/GIT_STRATEGY.md to describe the Conventional Commits convention used
   (feat/fix/docs/chore + scope), and the branching approach if any.
3. Do not invent features that were not actually implemented — document only what exists.

After updating, summarize what was added to each doc file.
```

### قاعدة الـCommits طول المشروع (تطبقها إنت):
```
feat(auth): add user registration
feat(tasks): add task model
feat(tasks): add task creation
feat(agent): add get_my_tasks tool
docs(srs): update architecture section
```

**✅ معيار النجاح:** الـdocs متسقة مع اللي فعلاً موجود في الكود، والـGit history متدرج ومفهوم.

**🚫 لا تنتقل للمرحلة 10 إلا بعد التأكد من ده.**

---

## 🎯 المرحلة 10 — Testing + Demo + Presentation

**الهدف:** التأكد إن كل حاجة شغالة تمام، وتجهيز عرض تقديمي واضح للدكتور.

### فلو العرض المستهدف:
```
Register → Login → Dashboard → Create Course → Create Task
→ Open AI Assistant → "Show my tasks" → Agent calls Tool
→ "Add Django task" → Agent calls Tool
→ "Delete Django task" → Confirmation → Delete
```

### البرومبت:
```
This step is testing and demo preparation only — no new features.

Requirements:
1. Walk through the full user journey end to end and list any bugs or broken links found:
   Register → Login → Dashboard → Create Course → Create Task →
   AI Assistant ("show my tasks" → "add a task" → "delete a task" with confirmation).
2. Fix only bugs found during this walkthrough — do not refactor working code.
3. Suggest 2-3 pieces of demo/sample data (a couple of courses and tasks) I can create
   before the presentation, so the demo isn't empty.
4. Give me a short, step-by-step demo script (in plain language) I can follow live,
   matching the flow above, so I can narrate what's happening at each step.

After this, give me:
1. A list of anything that was broken and fixed.
2. The final demo script.
```

**✅ معيار النجاح:** تقدر تعمل الديمو كامل من غير أي Error، وعندك سكريبت تتكلم بيه أثناء العرض.

---

## 🧭 قواعد عامة لمنع الـAI من "العجن"

1. **مرحلة واحدة في كل مرة** — لا تدمج برومبتين مع بعض.
2. **ابدأ كل برومبت بتوضيح إن ده جزء من مشروع أكبر، لكن الشغل ده بس المطلوب دلوقتي** (موجود بالفعل في كل برومبت أعلاه).
3. **اطلب من الـAI يشرح قبل التنفيذ** لو التغيير كبير (موجود في مراحل 2، 6، 7).
4. **متسبش الـAI يتخطى مرحلة** — لو رجّع حاجة زيادة عن المطلوب، قوله يشيلها ويرجع للنطاق المحدد.
5. **Commit بعد كل مرحلة ناجحة**، عشان لو حصل خطأ في مرحلة تقدر ترجع بسهولة.
6. **راجع الكود اللي اتكتب بعينك** قبل الانتقال، حتى لو شكله شغال — عشان تقدر تشرحه للدكتور.

---

## 📊 مصفوفة تغطية بنود التقييم

| بند التقييم | المرحلة المسؤولة |
|---|---|
| Django (MVT) | 1 |
| PostgreSQL / Models | 2 |
| Security (Auth + RBAC) | 3، 8 |
| Functionality (CRUD) | 4 |
| Frontend | 5 |
| Chatbot (Context-Aware) | 6 |
| Agentic AI | 7 |
| Git/GitHub | 9 |
| SRS | 9 |
| Defense/Demo | 10 |

---------------------------------------------------------
The Flow
1. Register
      ↓
2. Login
      ↓
3. Dashboard
      ↓
4. Create Course
      ↓
5. Create Task
      ↓
6. Open AI Assistant
      ↓
7. "Show my tasks"
      ↓
8. Agent calls Tool
      ↓
9. "Add Django task"
      ↓
10. Agent calls Tool
      ↓
11. "Delete Django task"
      ↓
12. Confirmation
      ↓
13. Delete