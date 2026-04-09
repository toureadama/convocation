@echo off
REM ============================================================
REM Script de déploiement pour Convocation Douanes CI
REM Ce script prépare et pousse les modifications vers GitHub
REM ============================================================

echo.
echo ============================================================
echo   DEPLOIEMENT CONVOCATION DOUANES CI
echo ============================================================
echo.

REM Étape 1 : Vérifier l'état git
echo [1/5] Verification de l'etat du depot Git...
git status
echo.

REM Étape 2 : Voir les modifications
echo [2/5] Modifications pretes a etre commitees :
git diff --stat
echo.

REM Étape 3 : Vérifier la connexion à GitHub
echo [3/5] Verification de la connexion GitHub...
git remote -v
echo.

REM Étape 4 : Demander confirmation
echo ============================================================
echo   ATTENTION : Ces modifications seront poussees vers GitHub
echo   et declencheront un deploiement sur Render.
echo ============================================================
echo.
set /p CONFIRM="Voulez-vous continuer ? (o/n) : "

if /i not "%CONFIRM%"=="o" (
    echo.
    echo Deploiement annule.
    pause
    exit /b 0
)

REM Étape 5 : Commit et push
echo.
echo [4/5] Commit des modifications...
git add .
git commit -m "fix: corriger syntax error app.py et espaces URLs frontend"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR : Le commit a echoue.
    echo Verifiez qu'il y a des modifications a commiter.
    pause
    exit /b 1
)

echo.
echo [5/5] Push vers GitHub...
git push origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR : Le push a echoue.
    echo Verifiez votre connexion Internet et vos droits GitHub.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   DEPLOIEMENT REUSSI !
echo ============================================================
echo.
echo Les modifications ont ete poussees vers GitHub.
echo.
echo SURVEILLEZ LE DEPLOIEMENT SUR RENDER :
echo   - Backend  : https://dashboard.render.com
echo   - Frontend : https://dashboard.render.com
echo.
echo TESTS POST-DEPLOIEMENT :
echo   - Backend  : https://convocation-douanesci.onrender.com/health
echo   - Frontend : https://convocation-a762.onrender.com
echo.
echo ============================================================
echo.

pause
