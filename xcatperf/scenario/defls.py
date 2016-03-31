import abc
import os
import random
import six

from xcatperf import base
from xcatperf.common import exception
from xcatperf.common import utils


DEVNULL = utils.DEVNULL
TMP_OUTPUT = open("/tmp/xcat_command.log_%s" % int(os.getpid()), 'w+')


@six.add_metaclass(abc.ABCMeta)
class DeflsEnv(object):
    def __init__(self, *args, **kwargs):
        self.count = int(kwargs['count'])
        if not self.count or self.count < 1:
            raise exception.InvalidValue(
                err="The number of node hould larger than 1")

    @utils.elaspe_run('setup')
    def _setup(self):
        args = "chdef node[1-%(count)s] mgt=ipmi groups=all arch=x86_64 " \
               "os=rhels7.0 nodetype=osi profile=service netboot=kvm " \
               "installnic=mac primarynic=mac " \
               "provmethod=rhels7-x86_64-install-service " \
               "bmcpassword=abc123 bmcusername=ADMIN" % {
                   'count': str(self.count)}
        utils.execute_command(args, shell=True, stdout=DEVNULL, stderr=DEVNULL)

    @utils.elaspe_run('teardown')
    def _teardown(self):
        args = "rmdef node[1-%(count)s]" % {'count': self.count}
        utils.execute_command(args, stdout=DEVNULL, stderr=DEVNULL, shell=True)


class DeflsCase(base.BaseCase, DeflsEnv):
    def __init__(self, *args, **kwargs):
        base.BaseCase.__init__(self, *args, **kwargs)
        DeflsEnv.__init__(self, *args, **kwargs)

    def _list_nodes(self):
        args = ['lsdef']
        utils.execute_command(args, stdout=TMP_OUTPUT)

    def _list_node_detail(self):
        id = random.randint(1, self.count)
        args = ['lsdef', 'node%d' % id]
        utils.execute_command(args, stdout=TMP_OUTPUT)

    def run(self, concurrency=1):
        self._setup()
        func_list = [self._list_nodes, self._list_node_detail]
        self.spawn(concurrency, func_list)
        self._teardown()


class DeflsRawCase(base.RawCase, DeflsEnv):
    def __init__(self, *args, **kwargs):
        base.RawCase.__init__(self, *args, **kwargs)
        DeflsEnv.__init__(self, *args, **kwargs)

    def _list_nodes(self):
        request = dict()
        request['xcatrequest'] = {'command': 'lsdef', 'clienttype': 'cli'}
        self._send_request(request)

    def _list_node_detail(self):
        request = dict()
        id = random.randint(1, self.count)
        request['xcatrequest'] = {'command': 'lsdef', 'clienttype': 'cli',
                                  'arg': 'node%d' % id}
        self._send_request(request)

    def run(self, concurrency=1):
        self._setup()
        func_list = [self._list_nodes, self._list_node_detail]
        self.spawn(concurrency, func_list)
        self._teardown()


class DeflsRestCase(base.RestCase, DeflsEnv):
    def __init__(self, *args, **kwargs):
        base.RestCase.__init__(self, *args, **kwargs)
        DeflsEnv.__init__(self, *args, **kwargs)

    def _list_nodes(self):
        print self._get('nodes')

    def run(self, concurrency=1):
        self._setup()
        func_list = [self._list_nodes]
        self.spawn(concurrency, func_list)
        self._teardown()
