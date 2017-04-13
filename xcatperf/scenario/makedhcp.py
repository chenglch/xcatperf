import abc
import os
import six

from xcatperf import base
from xcatperf.common import exception
from xcatperf.common import utils

DEVNULL = utils.DEVNULL
TMP_OUTPUT = open("/tmp/xcat_command.log_%s" % int(os.getpid()), 'w+')


@six.add_metaclass(abc.ABCMeta)
class MakeDHCPEnv(object):
    """Build environment for makedhcp command"""

    def __init__(self, *args, **kwargs):
        self.count = int(kwargs['count'])
        if not self.count or self.count < 1:
            raise exception.InvalidValue(
                err="The number of node hould larger than 1")

    @utils.elaspe_run('setup')
    def _setup(self):
        """Prepare kvm nodes for the performance analysis"""
        self._registe_kvm_guest()

    def _registe_kvm_guest(self):
        i = 0
        num = [0, 0]
        # TODO(chenglch): Use template to enroll nodes
        while i < self.count:
            nodename = "nytperfguest%s" % str(i + 1)
            ip = "10.5.101.%s" % str(i + 1)
            num[0] = i / 256
            num[1] = i % 256
            mac = '42:87:0a:05:%02x:%02x' % (num[0], num[1])
            args = "chdef %(nodename)s " \
                   "arch=x86_64 " \
                   "groups=all " \
                   "ip=%(ip)s " \
                   "mgt=kvm " \
                   "mac=%(mac)s " \
                   "netboot=xnba " \
                   "serialport=0 " \
                   "serialspeed=115200 " \
                   "vmcpus=1 " \
                   "vmhost=nytperfhost " \
                   "vmnicnicmodel=virtio " \
                   "vmnics=br-eno1 " \
                   "vmstorage=dir:///install/vms" % {"nodename": nodename,
                                                     "ip": ip,
                                                     "mac": mac}
            i += 1
            utils.execute_command(args, shell=True, stdout=DEVNULL,
                                  stderr=DEVNULL)

    @utils.elaspe_run('teardown')
    def _teardown(self):
        args = "rmdef nytperfguest[1-%(count)s]" % {'count': self.count}
        utils.execute_command(args, stdout=TMP_OUTPUT, stderr=TMP_OUTPUT,
                              shell=True)


class MakeDHCPCase(base.BaseCase, MakeDHCPEnv):
    def __init__(self, *args, **kwargs):
        base.BaseCase.__init__(self, *args, **kwargs)
        MakeDHCPEnv.__init__(self, *args, **kwargs)

    def _makedhcp(self):
        args = "makedhcp  nytperfguest[1-%s]" % self.count
        utils.execute_command(args, stdout=TMP_OUTPUT, stderr=TMP_OUTPUT,
                              shell=True)

    def run(self, concurrency=1):
        #NOTE (chenglch): comment out this for test
        #self._setup()
        func_list = [self._makedhcp]
        print "Test xcat in command line mode."
        self.spawn(concurrency, func_list)
        #self._teardown()
