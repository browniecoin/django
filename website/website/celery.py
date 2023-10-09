from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab
#celery -A website worker --loglevel=info
#celery -A website.celery beat --loglevel=info
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')

app = Celery('website')

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')


app.conf.beat_schedule = {
    'my-periodic-task': {
        'task': 'store.tasks.my_periodic_task',
        'schedule': crontab(minute=58, hour='1'),  # Run once an hour at the start of the hour
    },
    'my-periodic-task-balance': {
        'task': 'store.tasks.my_periodic_task_balance',
        'schedule': crontab(minute=15, hour='2'),  # Run once an hour at the start of the hour
    },
    'my-periodic-coin-stats-task': {
        'task': 'store.tasks.my_periodic_coin_stats_task',
        'schedule': crontab(minute='*/3'),
    },
}

app.autodiscover_tasks()

if __name__ == '__main__':
    app.start()
