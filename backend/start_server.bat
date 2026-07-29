start /B python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/srv.log 2>&1
