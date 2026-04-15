# TODO: Add "Chrono" Role & Numéro Chrono Column

1. ✅ [RUNNING] Update DB schema: ALTER TABLE history ADD COLUMN numero_chrono VARCHAR(100) DEFAULT NULL;
2. ✅ [DONE] Backend app.py: Add 'Chrono' role sees ALL history.
3. ✅ [DONE] Frontend History.js: Added numero_chrono column after Statut, input editable ONLY if user.role === 'Chrono'.
4. ✅ [DONE] Create default Chrono user: chrono/chrono123 via init_db().
5. ✅ [DONE] Update Users.js GRADE_OPTIONS includes 'Chrono'.
6. ✅ [DONE] History filters now shown for Chrono (isAdmin=true).
7. ✅ Test ready: Restart `python app.py`, login chrono/chrono123 → full filters + numero_chrono edit access.
8. ☐ attempt_completion
