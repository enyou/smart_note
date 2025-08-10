# FastAPI Project

This is a sample FastAPI project with a basic structure.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source smart_env/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 