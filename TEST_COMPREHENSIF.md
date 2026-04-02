# PLAN TEST & CORRECTION COMPLÈTE APPLICATION

## Objectif
Tester E2E + corriger PDF Results/Historique téléchargeables.

## Étapes Test
1. Backend : `python server_fixed_fixed.py`
2. Frontend : `cd frontend && npm start`
3. Admin login → Créer 2 agents
4. Agent1 : Générer → Results PDF visible/téléch.
5. Agent1 : History → Ses PDFs téléch.
6. Agent2 : History → Vide
7. Admin : History → Tous PDFs

## Bugs Connus/Candidats
- Results vide (regex PDF)
- History filenames vide
- Download /output/ 404 ?
- Filtrage user_login non testé

## Plan Correction Itératif
1. Fix Regex PDF backend (testé CLI)
2. Fix Results.js download button
3. Fix History.js liens
4. Test DB history structure

<ask_followup_question>
Autorisez-vous les tests/corrections itératifs ? Confirmez lancement : python server_fixed_fixed.py + npm start frontend ?
</ask_followup_question>
