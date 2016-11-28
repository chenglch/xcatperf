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
class NodesetEnv(object):
    """Build environment for nodeset command"""
    def __init__(self, *args, **kwargs):
        self.count = int(kwargs['count'])
        if not self.count or self.count < 1:
            raise exception.InvalidValue(
                err="The number of node hould larger than 1")

    @utils.elaspe_run('setup')
    def _setup(self):
        """Prepare kvm nodes for the performance analysis"""
        self._registe_kvm_host()
        self._registe_kvm_guest()

    def _registe_kvm_host(self):
        args = "chdef nytperfhost " \
               "groups=all " \
               "ip=10.5.102.1"
        utils.execute_command(args, shell=True, stdout=DEVNULL, stderr=DEVNULL)

    def _registe_kvm_guest(self):
        i = 0
        #TODO(chenglch): Use template to enroll nodes
        while i < self.count:
            nodename = "nytperfguest%s" % str(i + 1)
            ip = "10.5.101.%s" % str(i + 1)
            args = "chdef %(nodename)s " \
                   "arch=x86_64 " \
                   "groups=all " \
                   "ip=%(ip)s " \
                   "mgt=kvm " \
                   "netboot=xnba " \
                   "serialport=0 " \
                   "serialspeed=115200 " \
                   "vmcpus=1 " \
                   "vmhost=nytperfhost " \
                   "vmnicnicmodel=virtio " \
                   "vmnics=br-eno1 " \
                   "vmstorage=dir:///install/vms" % {"nodename": nodename,
                                                       "ip": ip}
            i+=1
            utils.execute_command(args, shell=True, stdout=DEVNULL,
                                  stderr=DEVNULL)
            args = "mkvm %(nodename)s -s 1G" % {'nodename': nodename}
            utils.execute_command(args, shell=True, stdout=DEVNULL,
                                  stderr=DEVNULL)

    @utils.elaspe_run('teardown')
    def _teardown(self):
        args = "rmvm nytperfguest[1-%(count)s] -f -p" % {'count': self.count}
        utils.execute_command(args, stdout=DEVNULL, stderr=DEVNULL, shell=True)
        args = "rmdef nytpefhost"
        utils.execute_command(args, stdout=DEVNULL, stderr=DEVNULL, shell=True)
        args = "rmdef nytperfguest[1-%(count)s]" % {'count': self.count}
        utils.execute_command(args, stdout=DEVNULL, stderr=DEVNULL, shell=True)


class NodesetCase(base.BaseCase, NodesetEnv):
    def __init__(self, *args, **kwargs):
        base.BaseCase.__init__(self, *args, **kwargs)
        NodesetEnv.__init__(self, *args, **kwargs)

    def _nodeset(self):
        args = "nodeset nytperfguest[1-%(count)s] " \
               "osimage=ubuntu16.04.1-x86_64-install-compute" % {"count": self.count}
        utils.execute_command(args, stdout=DEVNULL, stderr=DEVNULL, shell=True)

    def run(self, concurrency=1):
        self._setup()
        func_list = [self._nodeset]
        print "Test xcat in command line mode."
        self.spawn(concurrency, func_list)
        self._teardown()
