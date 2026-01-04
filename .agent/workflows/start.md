---
description: Start the Enterprise AI Agent server and open the frontend
---

# Start Enterprise AI Agent Application

This workflow starts the backend server and automatically opens the frontend in your browser.

## Steps

// turbo-all
1. Start the FastAPI backend server
```bash
python -m app.main
```

2. Open the frontend in your default browser
```bash
open frontend/index.html
```

## What happens:
- The backend server starts on http://localhost:8000
- The frontend webpage opens automatically in your browser
- You can access the API docs at http://localhost:8000/docs

## To stop the server:
Press `Ctrl+C` in the terminal where the server is running.
