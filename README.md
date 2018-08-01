# AnsibleEx2
采用Celery框架代替dubbo，全python编写，完善ansible使用机制及接口二次开发

ansible2.6(版本不同，api调用方式不同)
将ansible的shell，setup，playbook模块封装，提供http/https接口，通过celery框架（或本地存储）记录所有ansible操作日志
