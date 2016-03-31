import os
import signal
import re
import psutil
import errno
import sys
import traceback
import time
import stat
import dicttoxml
import xmltodict

from eventlet.green import subprocess
from xml.parsers import expat

from xcatperf.common import exception

DEVNULL = open(os.devnull, 'r+')
_DEFAULT_MODE = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO


def write_to_file(path, contents):
    with open(path, 'w') as f:
        f.write(contents)


def kill_process_group(pattern):
    prog = re.compile(r'.*' + pattern + r'.*', re.IGNORECASE)
    for p in psutil.process_iter():
        try:
            p_name = get_process_name(p)
        except exception.NoPidError:
            pass

        if prog.match(p_name):
            try:
                os.kill(p.pid, signal.SIGTERM)
            except OSError as exc:
                if psutil.pid_exists(p.pid):
                    raise exception.DaemonError("Error to kill process %s." %
                                                p_name)
            except psutil.NoSuchProcess:
                pass


def process_lter(pattern):
    prog = re.compile(r'.*' + pattern + r'.*', re.IGNORECASE)
    for p in psutil.process_iter():
        try:
            if prog.match(p.name()):
                yield p
        except psutil.NoSuchProcess:
            continue


def get_mem_usage(pid):
    """return memory inforamtion of process

    :param pid: process id
    :return pmem object: pmem(rss=48201728, vms=142483456, shared=4689920,
                         text=8192, lib=0, data=43311104, dirty=0)
    """
    try:
        return psutil.Process(pid).memory_info()
    except psutil.NoSuchProcess:
        raise exception.NoPidError(pid=pid)


def get_cpu_usage(pid):
    try:
        return psutil.Process(pid).cpu_percent(interval=0.1)
    except psutil.NoSuchProcess:
        raise exception.NoPidError(pid=pid)


def delete_if_exists(path, remove=os.unlink):
    """Delete a file, but ignore file not found error.

    :param path: File to delete
    :param remove: Optional function to remove passed path
    """

    try:
        remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def ensure_tree(path, mode=_DEFAULT_MODE):
    """Create a directory (and any ancestor directories required)

    :param path: Directory to create
    :param mode: Directory creation permissions
    """
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            if not os.path.isdir(path):
                raise
        else:
            raise


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def process_exist(pid_or_process):
    pid = pid_or_process.pid if isinstance(pid_or_process,
                                           psutil.Process) else pid_or_process
    return psutil.pid_exists(pid)


def make_synchronized(func):
    import threading

    func.__lock__ = threading.Lock()

    def synced_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return synced_func


def singleton(cls):
    instances = {}

    def _singleton(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return _singleton


def get_children_process(pid, recursive=False):
    try:
        p = psutil.Process(pid)
        return p.children(recursive)
    except psutil.NoSuchProcess:
        raise exception.NoPidError(pid=pid)


def get_process_name(pid_or_process):
    try:
        p = pid_or_process if isinstance(pid_or_process,
                                         psutil.Process) else psutil.Process(
            pid_or_process)
    except psutil.NoSuchProcess:
        raise exception.NoPidError(pid=pid_or_process)
    try:
        return p.name()
    except psutil.NoSuchProcess:
        raise exception.NoPidError(pid=p.pid)


def memory_info():
    """
    svmem(total=6259159040, available=1326632960, percent=78.8,
    used=4991082496, free=1268076544, active=4760506368, inactive=53526528,
    buffers=3575808, cached=54980608)
    """
    return psutil.virtual_memory()


def cpu_percent():
    return psutil.cpu_percent()


def execute_command(cmd, **kwargs):
    try:
        subprocess.call(cmd, **kwargs)
    except subprocess.CalledProcessError:
        if kwargs['shell']:
            raise exception.CommandError(cmd=cmd)
        else:
            raise exception.CommandError(cmd=' '.join(cmd))


def import_class(import_str):
    """Returns a class from a string including module and class.

    .. versionadded:: 0.3
    copy from oslo.utils
    """
    mod_str, _sep, class_str = import_str.rpartition('.')
    __import__(mod_str)
    try:
        return getattr(sys.modules[mod_str], class_str)
    except AttributeError:
        raise ImportError('Class %s cannot be found (%s)' %
                          (class_str,
                           traceback.format_exception(*sys.exc_info())))


def import_object(import_str, *args, **kwargs):
    """Import a class and return an instance of it.

    .. versionadded:: 0.3
    copy from oslo.utils
    """
    return import_class(import_str)(*args, **kwargs)


def dict_to_xcat_xml(req):
    """ convert python dict to xml
    :param req:
    :return: xml string
    :raise: TypeError
    """
    return '%s\n' % dicttoxml.dicttoxml(req, attr_type=False, root=False)


def xml_to_dict(xml):
    """ convert xml to python dict
    :param xml:
    :return: dict
    :raise: ValueError, ExpatError
    """
    try:
        return xmltodict.parse(xml, process_namespaces=False)
    except expat.ExpatError:
        raise exception.XMLError(content=xml)


def elaspe_run(desc=''):
    def _wrap(func):
        def wrap(*args, **kwargs):
            start_time = time.time()
            func(*args, **kwargs)
            end_time = time.time()
            print "\n*** %s Elapsed time: %f ***\n" % (
                desc, end_time - start_time)

        return wrap

    return _wrap