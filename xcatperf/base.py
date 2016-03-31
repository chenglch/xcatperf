import abc
import eventlet
import errno
import os
import signal
import requests
import six
import sys
import time

from OpenSSL.SSL import ZeroReturnError
from xcatperf import client as xcat_client
from xcatperf.common import exception
from xcatperf.common import utils
from xcatperf import xcatd

@six.add_metaclass(abc.ABCMeta)
class BaseCase(object):
    def __init__(self, *args, **kwargs):
        is_nytprof = True if kwargs['is_nytprof'] else False
        nytprof_dir = kwargs['nytprof_dir'] if is_nytprof else None
        self.child_pids = []
        self.daemon = xcatd.Daemon()
        self.daemon.start(is_nytprof=is_nytprof, nytprof_dir=nytprof_dir)

        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

    def sig_handler(self, sig, frame):
        print "SIG %d catched " % sig
        for p in self.child_pids:
            os.kill(p, signal.SIGTERM)
        self.daemon.stop()
        raise

    def spawn(self, pool_size, func_list=None):
        def run_in_eventlet(func, green_size, i):
            j = 0
            threads = []
            while j < green_size:
                threads.append(eventlet.spawn(func))
                j += 1

            j = 0
            while j < green_size:
                threads[j].wait()
                j += 1

        def get_client_info():
            process_info = {}
            process_info['count'] = 0
            process_info['mem'] = 0
            process_info['virt'] = 0
            for pid in self.child_pids:
                process_list = utils.get_children_process(pid, recursive=True)
                for p in process_list:
                    try:
                        temp_mem = utils.get_mem_usage(p.pid)
                        process_info['count'] += 1
                        process_info['mem'] += temp_mem.rss
                        process_info['virt'] += temp_mem.vms
                    except exception.NoPidError:
                        pass
            return process_info

        @utils.elaspe_run('concurrent')
        def run(func, pool_size, process_size):
            for i in range(0, process_size):
                if i == 0:
                    green_size = pool_size / 3 + pool_size % 3
                else:
                    green_size = pool_size / 3

                try:
                    pid = os.fork()
                    if pid == 0:
                        signal.signal(signal.SIGTERM, signal.SIG_DFL)
                        signal.signal(signal.SIGINT, signal.SIG_DFL)
                        run_in_eventlet(func, green_size, i)
                        sys.exit(0)
                    elif pid > 0:
                        self.child_pids.append(pid)
                except OSError as ex:
                    raise exception.UnexpectedError(
                        err="Fork failed: %d (%s)" % (ex.errno, ex.strerror))

            try:
                while len(self.child_pids) > 0:
                    process_info = self.daemon.get_process_info()
                    memory_info = utils.memory_info()
                    cpu_info = utils.cpu_percent()
                    client_info = get_client_info()
                    print "system memory_total %d memory_available %d " \
                          "memory_percent %f cpu_percent %f" % (
                              memory_info.total / 1024 / 1024,
                              memory_info.available / 1024 / 2014,
                              memory_info.percent,
                              cpu_info)
                    print "xcatd process count:%d mem:%d virt:%d " \
                          "immediate count:%d plugin count:%d" % (
                              process_info['count'],
                              process_info['mem'] / (1024 * 1024),
                              process_info['virt'] / (1024 * 1024),
                              process_info['immediate'],
                              process_info['plugin'])
                    print "xcat client count:%d mem: %d virt: %d \n" % (
                        client_info['count'],
                        client_info['mem'] / (1024 * 1024),
                        client_info['virt'] / (1024 * 1024))

                    pid = os.waitpid(-1, os.WNOHANG)
                    if pid[0] > 0:
                        self.child_pids.remove(pid[0])

                    time.sleep(0.2)

            except OSError as ex:
                if ex.errno != errno.ECHILD:
                    raise exception.UnexpectedError(err="Wait child exit err")

        pool_size = pool_size or 1
        process_size = 3 if pool_size >= 3 else 1

        for func in func_list:
            run(func, pool_size, process_size)

    def stop(self):
        self.daemon.stop()

    @abc.abstractmethod
    def run(self, concurrency=1):
        """Child clss should implement this method

        :param concurrency:
        :return: None
        """
        #raise NotImplementedError()


@six.add_metaclass(abc.ABCMeta)
class RawCase(BaseCase):
    def __init__(self, *args, **kwargs):
        super(RawCase, self).__init__(*args, **kwargs)

    def _send_request(self, request):
        """Send request to xcatd

        :param request: dict param which contains command structure
        """
        client = xcat_client.SSLClient().get_client()
        xml = utils.dict_to_xcat_xml(request)
        client.send(xml)
        temp = []
        while True:
            while True:
                try:
                    s = client.read(65535)
                    temp.append(s)
                    if s.find('</xcatresponse>') != -1:  # contains
                        break
                except ZeroReturnError:
                    break

            try:
                content = ''.join(temp)
                result = utils.xml_to_dict(content)
            except exception.XMLError:
                continue
            else:
                # with open(TMP_COMMAND_FILE % os.getpid(), 'a') as f:
                # f.write(content)
                temp = []
            finally:
                if content.find('serverdone') != -1:
                    break

        client.close()


@six.add_metaclass(abc.ABCMeta)
class RestCase(BaseCase):
    def __init__(self, *args, **kwargs):
        super(RestCase, self).__init__(*args, **kwargs)
        self.user = kwargs.get('user') or 'root'
        self.password = kwargs.get('password') or 'cluster'

    def _get(self, path):
        url = 'https://127.0.0.1/xcatws/%(path)s?userName=%(user)s' \
              '&userPW=%(password)s&pretty=1' % {
                  'user': self.user, 'password': self.password, 'path': path}
        return requests.get(url, verify=False)
