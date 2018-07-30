ansibleEx2使用说明文档

postgresql数据库
创建表
1 ansible_users  
 字段：  
    user_name varchar ansible用户名  
    passwd    varchar 用户密码（md5加密存储）  

2 server_passwd  
 字段：  
    server_user   varchar 服务器远程登录账号  
    server_passwd varchar 服务器用户密码（base64加密）  



通过web.py框架对ansible的api进行封装，提供http/https接口
       #登录，获取token
        {       
            "type": "login",
            "data": {
                "user": "wangml",
                "passwd":"oommg",
                "remote_user":"tinet_manage"
            }
        }

 {
            "type": "shell",
            "data": {
                "host": "172.16.22.252,172.16.22.232",  #或者天ansible配置文件中的组名
                "user": "wangml",
                "sudo": "yes",
                "sudo_user": "root",
                "remote_user": "tinet_manage",
                “token”: "",
                "values": ["whoami;whoami",]
            }
        }


{
          "type": "setup",
          "data": {
            "host": "172.16.22.252,172.16.22.232",      #或者天ansible配置文件中的组名
            "user": "wangml",
            "sudo": "yes",
            "sudo_user": "root",
            "remote_user": "tinet_manage",
            “token”: "",
            "values":["ansible_nodename","ansible_mounts"]
            }
        }

        {
          "type": "playbook",
          "data": {
            "user": "wangml",
            "sudo": "yes",
            "sudo_user": "root",
            "remote_user": "tinet_manage",
            “token”: "omygad911",
            "values":["/Users/wml/github/AnsibleEx2/tt.yml","/Users/wml/github/AnsibleEx2/test.yml"]
            }
        }


操作记录通过celery框架完成
producer提供日志记录服务，将用户对每个服务器的操作进行记录
