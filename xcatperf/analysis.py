import os
from six.moves.urllib import parse as urlparse
from xcatperf.common import utils
from xcatperf.common import exception

PERF_TRACE_LOG = '/var/log/xcat/perf.log'
PLUGIN_TOKEN = 'plugin'
IMMEDIATE_TOKEN = 'immediate'
DB_TOKEN = 'db'
NYTPROF_FILE = 'nytprof.out.%s'


class ProcessInfo(object):
    def __init__(self, pid, prog, data_file=None, modname=None):
        self.pid = pid
        self.prog = prog
        self.data_file = data_file
        self.modname = modname


class Nytprof(object):
    def __init__(self):
        self.p_info_list = []
        utils.delete_if_exists(PERF_TRACE_LOG)

    def _parse_perf_info(self, dir):
        if not os.access(PERF_TRACE_LOG, os.R_OK):
            raise exception.FileNotFound(file=PERF_TRACE_LOG)

        with open(PERF_TRACE_LOG) as f:
            content = f.read()

        lines = content.split('\n')
        for line in lines:
            p_info = None
            fields = line.split('\t')
            if len(fields) < 2:
                continue
            if fields[1] == IMMEDIATE_TOKEN:
                pid = fields[2]
                data_file = os.path.join(dir, NYTPROF_FILE % pid)
                p_info = ProcessInfo(fields[2], fields[3], data_file)
            if fields[1] == PLUGIN_TOKEN:
                pid = fields[2]
                data_file = os.path.join(dir, NYTPROF_FILE % pid)
                p_info = ProcessInfo(fields[2], fields[3], data_file,
                                     fields[4])
            if fields[1] == DB_TOKEN:
                pid = fields[2]
                data_file = os.path.join(dir, NYTPROF_FILE % pid)
                p_info = ProcessInfo(fields[2], fields[3], data_file)

            if p_info:
                self.p_info_list.append(p_info)

    def _build_html(self, dir, http_url):
        if not utils.which('nytprofhtml'):
            raise exception.CommondNotFound(cmd='nytprofhtml')
        if len(self.p_info_list) <= 0:
            raise exception.PerfException("No perf result")

        with open(os.path.join(dir, 'index.html'), 'w') as fd:
            fd.write('<html><ul>')
            for p in self.p_info_list:
                f = os.path.join(dir, p.data_file)
                args = ['nytprofhtml', '--file', f, '-o',
                        os.path.join(dir, p.pid)]
                utils.execute_command(args)
                line = '<li><a href=\'%s/\'>%s %s</a> </li>' % (
                    urlparse.urljoin(http_url, p.pid),
                    p.prog, p.modname or IMMEDIATE_TOKEN)
                fd.write(line)
            fd.write(('</ul></html>'))

    def build(self, dir, http_url):
        self._parse_perf_info(dir)
        self._build_html(dir, http_url)
