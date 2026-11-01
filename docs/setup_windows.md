Setup
Backend: & "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Frontend: cd web; npm install; npm run dev
Tests: & "..\.venv\Scripts\python.exe" -m pytest -q
Frontend build: cd web; npm run build
