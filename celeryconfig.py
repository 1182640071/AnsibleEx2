# celeryconfig.py
# coding=utf-8

# Broker 设置 RabbitMQ
BROKER_URL = 'amqp://guest@172.16.22.252:5672/'
CELERY_RESULT_BACKEND = 'amqp://guest@172.16.22.252:5672/'

# Tasks 位于 worker.py 中
CELERY_IMPORTS = ('tasks', )

# 默认为1次/秒的任务
CELERY_ANNOTATIONS = {'tasks.add': {'rate_limit': '1/s'}}

CELERY_ROUTES = {'tasks.add': {'queue': 'ansible_log'}}

# 默认所有格式为 json
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT=['json']