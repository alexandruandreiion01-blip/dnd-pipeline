@echo off
cd /d %~dp0
call .venv\Scripts\activate
python lookup_app.py
pause