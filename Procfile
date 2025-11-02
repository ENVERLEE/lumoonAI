web: python manage.py collectstatic --noinput && python manage.py migrate && python manage.py create_subscription_plans && gunicorn prompt_mate.wsgi:application --bind 0.0.0.0:$PORT

