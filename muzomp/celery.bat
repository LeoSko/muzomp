set PATH=venv\Scripts;%PATH%
call venv\Scripts\activate.bat
call venv\Scripts\celery.exe worker -A muzomp.celery_settings:app -E --loglevel=info --pool=eventlet