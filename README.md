# DashCamAnalysysWeb

mail test
    python -m smtpd -n -c DebuggingServer localhost:8025

initial db
    python manage.py createcachetable
    python manage.py migrate auth
    python manage.py migrate sessions
    python manage.py migrate
    python manage.py migrate --database ai ai_app
    
