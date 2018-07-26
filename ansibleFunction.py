#coding: utf-8
#!/usr/bin/env python

import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager

class ResultsCallback(CallbackBase):
    def __init__(self,*args,**kwargs):
        super(ResultsCallback,self).__init__(*args,**kwargs)
        self.task_ok = {}
        self.task_unreachable = {}
        self.task_failed = {}
        self.task_skipped = {}
        self.task_stats = {}
        # self.host_ok = {}
        # self.host_unreachable = {}
        # self.host_failed = {}

    def v2_runner_on_unreachable(self, result):
        self.task_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, *args, **kwargs):
        self.task_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, *args, **kwargs):
        self.task_failed[result._host.get_name()] = result

    def v2_runner_on_skipped(self, result, *args, **kwargs):
        self.task_skipped[result._host.get_name()] = result

    def v2_runner_on_stats(self, result, *args, **kwargs):
        self.task_stats[result._host.get_name()] = result


#chushihua
class Runner(object):

    def __init__(self, sudo_user=None,sudo=None,become=False,become_method=False,become_user=None,*args,**kwargs):
        self.loader = DataLoader()
        self.results_callback = ResultsCallback()
        self.inventory = InventoryManager(loader=self.loader,sources=['hosts.conf'])
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.passwords = None
        Options = namedtuple('Options',
                     ['connection',
                      'remote_user',
                      'ask_sudo_pass',
                      'verbosity',
                      'ack_pass',
                      'module_path',
                      'forks',
                      'become',
                      'become_method',
                      'become_user',
                      'check',
                      'listhosts',
                      'listtasks',
                      'listtags',
                      'syntax',
                      'sudo_user',
                      'sudo',
                      'diff'])
        # 初始化需要的对象
        self.options = Options(connection='smart',
                       remote_user=None,
                       ack_pass=None,
                       sudo_user=sudo_user,
                       forks=5,
                       sudo=sudo,
                       ask_sudo_pass=False,
                       verbosity=5,
                       module_path=None,
                       become=become,
                       become_method=become_method,
                       become_user=become_user,
                       check=False,
                       diff=False,
                       listhosts=None,
                       listtasks=None,
                       listtags=None,
                       syntax=None)

    def run_ad_hoc(self , host , user , passwd , task):
        self.variable_manager.extra_vars={"ansible_ssh_user":user , "ansible_ssh_pass":passwd}
        play_source = dict(
            name="Ansible Play ad-hoc",
            hosts=host,
            gather_facts='no',
            tasks = task
            # tasks=[
            #     dict(action=dict(module='shell', args='whoami'), register='shell_out'),
            #     # dict(action=dict(module='setup', filter='ansible_nodename'), register='shell_out'),
            #     #dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
            # ]
        )
        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inventory,
                variable_manager=self.variable_manager,
                loader=self.loader,
                options=self.options,
                passwords=self.passwords,
                stdout_callback=self.results_callback,
            )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        ##定义字典用于接收或者处理结果
        result_raw = {'success': {}, 'failed': {}, 'unreachable': {}, 'skipped': {}, 'status': {}}

        # 循环打印这个结果，success，failed，unreachable需要每个都定义一个
        for host, result in self.results_callback.task_ok.items():
            result_raw['success'][host] = result._result

        for host, result in self.results_callback.task_failed.items():
            result_raw['failed'][host] = result._result

        for host, result in self.results_callback.task_unreachable.items():
            result_raw['unreachable'][host] = result._result

        return result_raw

    def run_playbook(self , user , passwd , task):
        # self.variable_manager.extra_vars={"ansible_ssh_user":"root" , "ansible_ssh_pass":"omygad514"}
        self.variable_manager.extra_vars={"ansible_ssh_user":user , "ansible_ssh_pass":passwd}
        playbook = PlaybookExecutor(playbooks=task, inventory=self.inventory,
                                    variable_manager=self.variable_manager,
                                    loader=self.loader, options=self.options, passwords=self.passwords)

        playbook._tqm._stdout_callback = self.results_callback
        results = playbook.run()

        ##定义字典用于接收或者处理结果
        result_raw = {'success': {}, 'failed': {}, 'unreachable': {}, 'skipped': {}, 'status': {}}

        # 循环打印这个结果，success，failed，unreachable需要每个都定义一个
        for host, result in self.results_callback.task_ok.items():
            result_raw['success'][host] = result._result

        for host, result in self.results_callback.task_failed.items():
            result_raw['failed'][host] = result._result

        for host, result in self.results_callback.task_unreachable.items():
            result_raw['unreachable'][host] = result._result

        for host, result in self.results_callback.task_skipped.items():
            result_raw['skipped'][host] = result._result

        for host, result in self.results_callback.task_stats.items():
            result_raw['status'][host] = result._result

        return result_raw


# c = Runner()
# print c.run_ad_hoc()
# print c.run_playbook()
# print (c.run_ad_hoc(),c.run_playbook())