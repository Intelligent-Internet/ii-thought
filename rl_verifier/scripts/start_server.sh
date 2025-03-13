export FUSION_SANDBOX_URL=http://localhost:8080

uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --workers 10