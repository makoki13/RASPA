@echo off
cd C:\Python Proyectos\RASPA
call venv\Scripts\activate.bat

:: 1. Ejecutamos el bot
python main.py

:: 2. Preparamos Git (solo añadimos la carpeta de la web)
git add output_web/index.html

:: 3. LA MAGIA: Comprobamos si hay cambios reales para hacer commit
git diff --cached --quiet
if errorlevel 1 (
    echo 🌐 Cambios detectados en la web. Subiendo a GitHub...
    git commit -m "🤖 Bot: Ranking actualizado automaticamente"
    git push
) else (
    echo 💤 No hay cambios en el ranking. No se sube nada a GitHub.
)