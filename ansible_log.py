#coding=utf-8

#pip install celery

from celery import Celery,platforms
import os

app = Celery('tasks',backend='redis://:omygad911@172.16.22.232:6379/3', broker='amqp://guest@172.16.22.252:5672/')
#backend:消息中间件类型，可无；broker：指定AMQP Broker(Advanced Message Queue Protocal，高级消息队列协议 消息中间件)
platforms.C_FORCE_ROOT = True       #用户解决root用户无法启动worker的问题

@app.task                           #对函数做celery task注解
def add(user,result , type_request):
    list = ['unreachable' , 'status','failed','skipped','success']
    for key in list:
        for k in result[key]:
            try:
                os.system('echo " " >> /tmp/' + k + '.ansible.log')
                os.system('echo `date` >> /tmp/' + k + '.ansible.log')
                cmd = 'echo [' + key + '] ' + user + ': ['+type_request+'] ==>' + str(result[key][k]) + ' >> /tmp/' + k + '.ansible.log'
                os.system(cmd)
            except:
                os.system('echo ' + str(result) + ' >> /tmp/ansible.log')
    return 'ok'