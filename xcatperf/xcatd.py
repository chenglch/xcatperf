import os
import subprocess
import retrying
import platform
from xcatperf.common import utils
from xcatperf.common import exception

DEVNULL = open(os.devnull, 'r+')
XCATD_PROC_NAMES = (
    'xcatd: SSL listener', 'xcatd: DB Access', 'xcatd: UDP listener',
    'xcatd: install monitor', 'xcatd: Command log writer',
    'xcatd: Discovery worker')

ACTIVE = 'active'

XCATD_CMD = utils.which('xcatd')
if not XCATD_CMD:
    XCATD_CMD = utils.which('/opt/xcat/sbin/xcatd')
if not XCATD_CMD:
    raise exception.CommondNotFound(cmd='xcatd')

PERL_PERF_CMD = 'perl -d:NYTProf '
if platform.linux_distribution()[0] == 'Ubuntu':
    PERL_PERF_CMD = 'perl -dt:NYTProf '


@utils.make_synchronized
@utils.singleton
class Daemon(object):
    def __init__(self):
        self.pid_dict = dict()
        self.status = None

    @property
    def main_pid(self):
        if self.status != ACTIVE:
            raise exception.DaemonError("xcatd has not been started")
        return self.pid_dict[XCATD_PROC_NAMES[0]]

    def start(self, is_nytprof=False, nytprof_dir=None):
        self.stop()
        if is_nytprof:
            if nytprof_dir:
                utils.ensure_tree(nytprof_dir)
            # by default nytprf command will generate output files in the
            # working directory
            os.chdir(nytprof_dir)
        args = ""
        env = os.environ
        if is_nytprof:
            args = PERL_PERF_CMD
            env['NYTPROF'] = 'start=no'
        args += "%s -f > /dev/null 2> /dev/null &" % XCATD_CMD
        try:
            subprocess.Popen(args, env=env, shell=True)
        except (OSError, ValueError) as ex:
            raise exception.UnexpectedError(
                err=str(ex))
        is_running = self._is_running()
        if is_running:
            self._init_pid_hash()
            self.status = ACTIVE
            print "xcat is running"
        else:
            self.stop()
            raise exception.DaemonError("xcatd can not be started")

    def _is_running(self):
        def retry_if_command_error(exception):
            """Return True if we should retry (in this case when it's an IOError), False otherwise"""
            return isinstance(exception, subprocess.CalledProcessError)

        @retrying.retry(retry_on_exception=retry_if_command_error,
                        stop_max_delay=10000)
        def wait():
            subprocess.check_call('lsdef', stdout=DEVNULL, stderr=DEVNULL)

        try:
            wait()
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def _init_pid_hash(self):
        for p in utils.process_lter('xcatd'):
            p_name = utils.get_process_name(p)
            if p_name in XCATD_PROC_NAMES:
                self.pid_dict[p_name] = p.pid

    def get_process_info(self):
        process_info = {}
        process_list = utils.get_children_process(self.main_pid,
                                                  recursive=True)
        process_info['count'] = len(process_list) + 1
        temp_mem = utils.get_mem_usage(self.main_pid)
        process_info['mem'] = temp_mem.rss
        process_info['virt'] = temp_mem.vms
        # process_info['cpu'] = utils.get_cpu_usage(self.main_pid)

        for p in process_list:
            try:
                temp_mem = utils.get_mem_usage(p.pid)
                process_info['mem'] += temp_mem.rss
                process_info['virt'] += temp_mem.vms
                # process_info['cpu'] += utils.get_cpu_usage(p.pid)
            except exception.NoPidError:
                pass

        # immediate_list = [p.pid for p in
        # utils.get_children_process(
        # self.main_pid, recursive=False) if
        # p.name() not in XCATD_PROC_NAMES]
        immediate_count = 0
        plugin_count = 0
        for p in utils.get_children_process(self.main_pid):
            try:
                if utils.get_process_name(p) in XCATD_PROC_NAMES:
                    continue
            except exception.NoPidError:
                continue

            immediate_count += 1
            try:
                plugin_list = [plugin for plugin in
                               utils.get_children_process(p.pid)]
                plugin_count += len(plugin_list)
            except exception.NoPidError:
                continue

        process_info['immediate'] = immediate_count
        process_info['plugin'] = plugin_count
        return process_info


    def stop(self):
        def process_status(result):
            return result

        @retrying.retry(retry_on_result=process_status, stop_max_delay=10000)
        def wait():
            try:
                return True if utils.process_exist(self.main_pid) else False
            except exception.DaemonError:
                return False

        utils.kill_process_group('xcatd')
        wait()
        self.status = None
