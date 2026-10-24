# FILE: backend/run.sh
#!/bin/bash
# Kill any orphan process on port 8000 (like when Node/Nest crashes)
lsof -ti :8000 | xargs kill -9 2>/dev/null

# Activate venv and start FastAPI with hot-reload (exact equivalent of `nest start --watch`)
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000