# TODO: Supprimer utilisateurs inactifs (interactive)

## Plan approuvé:
1. ✅ **Create TODO.md** - Track progress (current step)
2. **Edit app.py** - Add two admin endpoints:
   - `GET /api/users/inactive` → List inactive users (is_active=0)
   - `DELETE /api/users/inactive` → Hard delete all inactive users
3. **Test endpoints**:
   - Login admin → GET list → DELETE → Verify
4. **attempt_completion** - Task done
