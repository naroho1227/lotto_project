#!/bin/sh

echo "DB 연결 대기중"
python - << 'PYEOF'
import socket, time, sys

host, port = "db", 5432
for i in range(60):
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        print(f"DB 연결 성공")
        sys.exit(0)
    except OSError:
        print(f"대기 중")
        time.sleep(2)

print("DB 연결 실패")
sys.exit(1)
PYEOF

python manage.py migrate --noinput
python manage.py collectstatic --noinput

python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')
    print('슈퍼유저 생성 완료')
"

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:9000 \
    --workers 3
