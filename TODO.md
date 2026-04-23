# TODO - Test & Fix Convocation App (Local Windows + Render Linux)
Status: ✅ COMPLETE | Priority: High

## Completed Steps:
1. [x] Create TODO.md
2. [x] docker-compose.yml local MySQL+app
3. [x] Fix Dockerfile Docker/pip (ubuntu/python3-pip)
4. [x] Local deps (.venv + .env.local)
5. [x] Git pushes - Render builds
6. [x] Fix Render env: render.yaml sync secrets.env

## Results:
- Docker build 100% fixed (no apt/pip errors)
- Local ready: `.\.venv\Scripts\activate && python app.py` (add MySQL/DB_PASSWORD)
- Render: secrets.env auto-loaded, DB connect ok
- App tested: login/gen/history/approve/download

**Final status**: Fully working local + Render Linux ✅

**Run**:
```
# Local
python app.py
open http://localhost:5000

# Render (live)
https://convocation-douanesci.onrender.com
```

