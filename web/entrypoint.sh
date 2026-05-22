#!/bin/sh
set -e

echo "===== DB 연결 대기 중... ====="
until nc -z db 5432; do
  echo "  DB 준비 중, 1초 대기..."
  sleep 1
done
echo "===== DB 연결 성공 ====="

echo "===== 마이그레이션 실행 ====="
python manage.py migrate --noinput

echo "===== 정적 파일 수집 ====="
python manage.py collectstatic --noinput

echo "===== 슈퍼유저 생성 (없을 경우) ====="
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')
    print('슈퍼유저 admin 생성 완료')
else:
    print('슈퍼유저 이미 존재')
"

echo "===== Gunicorn 시작 ====="
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:9000 \
    --workers 3 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
