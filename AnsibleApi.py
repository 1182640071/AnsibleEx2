#-*- coding: utf-8 -*-
'''
python api.py 8090 指定端口运行方式

pip install psycopg2-binary
pip install web.py

created by wangminglang
date 2018.7.23


对ansible的api进行封装,实现http/https接口
'''


import web,logging , os , sys
import json , psycopg2
import hashlib , base64
import random , string
from web.wsgiserver import CherryPyWSGIServer
from ansibleFunction import Runner
from celery import Celery
import ConfigParser


reload(sys)
sys.setdefaultencoding('utf8')


# CherryPyWSGIServer.ssl_certificate = "/root/ansibleTest/myserver.crt"
# CherryPyWSGIServer.ssl_private_key = "/root/ansibleTest/myserver.key"

urls = (
    '/ansible/login','AnsibleLogin',
    '/ansible/api1.0','AnsibleOne',
)

# web.config.session_parameters['cookie_name'] = 'api_session_id'
# web.config.session_parameters['cookie_domain'] = None
web.config.session_parameters['ignore_expiry'] = True
# web.config.session_parameters['ignore_change_ip'] = True
# web.config.session_parameters['secret_key'] = 'fLjUfxqXtfNoIldA0A0J'
# web.config.session_parameters['expired_message'] = 'Session expired'
web.config.session_parameters['timeout']=3600


# cookie_name - 保存session id的Cookie的名称
# cookie_domain - 保存session id的Cookie的domain信息
# timeout - session的有效时间 ，以秒为单位
# ignore_expiry - 如果为True，session就永不过期
# ignore_change_ip - 如果为False，就表明只有在访问该session的IP与创建该session的IP完全一致时，session才被允许访问。
# secret_key - 密码种子，为session加密提供一个字符串种子
# expired_message - session过期时显示的提示信息。

app = web.application(urls,globals())
if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'),initializer={'token':'','passwd':''})
    web.config._session = session
else:
    session = web.config._session


conf = ConfigParser.ConfigParser()
conf.read("ansible_server.cfg")

write_log = conf.get('base', 'write_log').strip()
remote_log = conf.get('base', 'remote_log').strip()
path_log = conf.get('base', 'path_log').strip()

db_ip = conf.get('db', 'ip').strip()
db_port = int(conf.get('db', 'port').strip())
db_user = conf.get('db', 'user').strip()
db_passwd = conf.get('db', 'passwd').strip()
db_database = conf.get('db', 'database').strip()


class AnsibleLogin:
    def GET(self):
        return 'Please Send Post Request'

    def POST(self):
        '''
        {
            "type": "login",
            "data": {
                "user": "wangml",
                "passwd":"oommg",
                "remote_user":"not_root_user"
            }
        }
        :return:
        '''
        result = {
            "res":"faild",
            "value":""
        }
        info = web.data()
        try:
            data = eval(info)
            type_request = data['type']
            if type_request != 'login':
                result['res'] = 'faild'
                result['value'] = 'the type of request error'
                return json.dumps(result)
            user = data['data']['user']
            passwd = data['data']['passwd']
            remote_user = data['data']['remote_user']
            status = self.checkUser(user , passwd)
            if status == 0:
                password = self.getPasswd(remote_user)
                session.passwd = base64.decodestring(password)
                token = ''.join(random.sample(string.ascii_letters + string.digits, 24)).upper()
                session.token = token
                result['res'] = 'ok'
                result['value'] = token
                return json.dumps(result)
            else:
                result['res'] = 'faild'
                result['value'] = 'user login faild'
                return json.dumps(result)
        except Exception as e:
            print e
            result['res'] = 'faild'
            result['value'] = 'login error'
            return json.dumps(result)


    def checkUser(self , user ,passwd ):
        '''
        用户登录认证
        :param user: 用户名
        :param passwd: 密码
        :return: 0成功  1失败
        '''
        try:
            conn = psycopg2.connect(host=db_ip,port=db_port,user=db_user,password=db_passwd,database=db_database)
        except Exception as e:
            print e
            return 1
        try:
            cur = conn.cursor()
            sql = "select passwd from ansible_users where user_name = %s"
            values = (user,)
            cur.execute(sql,values)
            rows = cur.fetchall()
            if len(rows) == 0:
                return 1
            else:
                hl = hashlib.md5()
                hl.update(passwd)
                pd = hl.hexdigest().upper()
                if pd == rows[0][0]:
                    return 0
                else:
                    return 1
        except Exception as e:
            print e
            return 1
        finally:
            conn.close()


    def getPasswd(self , remote_user ):
        '''
        获取remote_user密码
        :param remote_user:ansible远程用户
        :return:密码str(已加密)
        '''
        try:
            conn = psycopg2.connect(host=db_ip,port=db_port,user=db_user,password=db_passwd,database=db_database)
        except Exception as e:
            print e
            return 1
        try:
            cur = conn.cursor()
            sql = "select user_passwd from server_passwd where server_user = %s"
            values = (remote_user,)
            cur.execute(sql,values)
            rows = cur.fetchall()
            if len(rows) == 0:
                return ''
            else:
                return rows[0][0]
        except Exception as e:
            print e
            return ''
        finally:
            conn.close()

class AnsibleOne:

    def GET(self):
        print session.token_list
        return 'Please Send Post Request'

    def POST(self):
        '''
        shell:
        {
            "type": "shell",
            "data": {
                "host": "ip1,ip2 || groupname",
                "user": "wangml",
                "sudo": "yes || no",
                "sudo_user": "root",
                "remote_user": "not_root_user",
                "token": "omygad911",
                "values": ["whoami", "uptime"]
            }
        }

        setup:
        {
          "type": "setup",
          "data": {
            "host": "ip1,ip2 || groupname",
            "user": "wangml",
            "sudo": "yes || no",
            "sudo_user": "root",
            "remote_user": "not_root_user",
            "token": "omygad911",
            "values":["ansible_nodename","ansible_mounts"]
            }
        }

        playbooks:
        {
          "type": "playbook",
          "data": {
            "user": "wangml",
            "sudo": "yes || no",
            "sudo_user": "root",
            "remote_user": "not_root_user",
            "token": "omygad911",
            "values":["tt.yml","/etc/ansible/test.yml"]
            }
        }
        :return:
        '''
        web.header('Content-Type', 'application/json;charset=UTF-8')
        data = web.data()
        info = {}
        tasks = []
        try:
            info = eval(data)
            type_request = info['type']         #操作类型
            user = info['data']['user']         #执行人
            sudo = info['data']['sudo']         #是否sudo
            become = False              #是否sudo
            become_method = ''          #sudo
            if sudo == 'yes':
                become = True
                become_method = 'sudo'
            sudo_user = info['data']['sudo_user']   #sudo用户
            remote_user = info['data']['remote_user']   #ansible连接用户
            toekn = info['data']['token']
            if session.token == toekn:
                user_passwd = session.passwd        #ansible用户密码
            else:
                return json.dumps("the token is error")
            # user_passwd = info['data']["user_passwd"]   #ansible用户密码
            values = info['data']['values']     #shell指令或者过滤信息或者playbook的yml文件
            host = ''                   #操作主机
            if type_request == 'playbook':
                host = ''
                tasks = values
            elif type_request == 'shell':
                host = info['data']['host']
                for cmd in values:
                    tasks.append(dict(action=dict(module='shell', args=cmd), register='shell_out'))
            elif type_request == 'setup':
                host = info['data']['host']
                tasks.append(dict(action=dict(module='setup'), register='shell_out'))
            else:
                return json.dumps("the type of request error")
        except Exception , e:
            print e
            return json.dumps("the type of data error")
        Aapi = Runner(sudo_user,sudo,become,become_method,sudo_user)
        if type_request == 'playbook':
            rs = Aapi.run_playbook(remote_user , user_passwd , tasks)
        elif type_request == 'setup':
            res = Aapi.run_ad_hoc(host ,remote_user , user_passwd , tasks)
            rs = self.analyse(res , values)
        else:
            rs = Aapi.run_ad_hoc(host ,remote_user , user_passwd , tasks)
        if write_log == '1':
            if remote_log == '1':
                celery = Celery()
                celery.config_from_object('celeryconfig')
                x = celery.send_task('ansible_log.add', args=[user, rs , type_request])
                # print x
                # print x.id , x.app , x.backend , x.parent , x.on_ready , x._cache , x._ignored
                # print x.get(timeout=20)   #同步调用
            else:
                self.add(user, rs , type_request)
        return json.dumps(rs)

    def add(self , user,result , type_request):
        list = ['unreachable' , 'status','failed','skipped','success']
        for key in list:
            for k in result[key]:
                try:
                    os.system('echo " " >> ' + path_log + k + '.ansible.log')
                    os.system('echo `date` >> ' + path_log + k + '.ansible.log')
                    cmd = 'echo [' + key + '] ' + user + ': ['+type_request+'] ==>' + str(result[key][k]) + ' >> ' + path_log + k + '.ansible.log'
                    os.system(cmd)
                except Exception , e:
                    print e
                    os.system('echo ' + str(result) + ' >> ' + path_log + 'ansible.log')
        return 'ok'


    def analyse(self , res , list):
        if len(list) == 0:
            return res

        result = {}
        try:
            result['status'] = res['status']
            result['failed'] = res['failed']
            result['unreachable'] = res['unreachable']
            result['skipped'] = res['skipped']
            result['success'] = {}
            for key in res['success']:
                if not result['success'].has_key(key):
                    result['success'][key] = {}
                    for k in list:
                        if res['success'][key]['ansible_facts'].has_key(k):
                            result['success'][key][k] = res['success'][key]['ansible_facts'][k]
                        else:
                            result['success'][key][k] = ''
                else:
                    for k in list:
                        if res['success'][key]['ansible_facts'].has_key(k):
                            result['success'][key][k] = res['success'][key]['ansible_facts'][k]
                        else:
                            result['success'][key][k] = ''
        except Exception , e:
            print e
            result = '{}'
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    app.run()