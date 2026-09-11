# Smart Student Assistant

Beginner-friendly full-stack Django project for a student productivity platform.

## Team Setup

Follow these commands in order.

### 1. Open project folder
```powershell
cd C:\path\to\Graduation-Project
```

### 2. Create a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade pip
```powershell
python -m pip install --upgrade pip
```

### 4. Install the requirements
```powershell
pip install -r requirements.txt
```

### 5. Create your environment file
```powershell
Copy-Item .env.example .env
```

Update the copied `.env` file with your PostgreSQL settings:
```env
SECRET_KEY=change-me
DEBUG=True
DB_NAME=smart_student_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
AI_API_KEY=your_ai_key
```

### 6. Create PostgreSQL database
```powershell
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U postgres -d postgres -P pager=off -w -c "CREATE DATABASE smart_student_db;"
```

### 7. Run migrations
```powershell
python manage.py migrate
```

### 8. Start the project
```powershell
python manage.py runserver 127.0.0.1:8000
```

Open the app in your browser:
```text
http://127.0.0.1:8000
```

## Project Stack
- Django (MVT)
- PostgreSQL
- HTML5 / CSS3 / JavaScript ES6+
- AI Agent with Python tools
- Django ORM
- Authentication + role-based access

## Requirement Map
See `docs/REQUIREMENTS_MAP.md`.
