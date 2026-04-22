# TODO - Test & Fix Convocation App (Local Windows + Render Linux)
Status: ✅ In Progress | Priority: High

## Logical Steps from Approved Plan:

1. [x] Create TODO.md (this file)
2. [x] Create docker-compose.yml for local MySQL + app testing (Windows)
3. [x] Fix Dockerfile: Ubuntu base + minimal deps + pywin32 disabled
4. [ ] Test local: `docker-compose up --build` → curl health/PDF gen
5. [ ] Test endpoints: Login, generate PDF, history
6. [ ] Deploy Render: Trigger build, set env vars if needed
7. [ ] Test Render Linux: Full flow (gen → approve → download PDF)
8. [ ] [FINAL] attempt_completion

**Next:** docker-compose.yml + Dockerfile fix

