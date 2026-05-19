@echo off
cd /d %~dp0
call .venv\Scripts\activate
python pipeline.py
pause