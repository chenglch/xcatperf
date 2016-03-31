# -*- encoding: utf-8 -*-

from __future__ import print_function
import traceback
import six
import sys
import os

path = os.path.dirname(os.path.realpath(__file__))
path = os.path.realpath(os.path.join(path, '..'))
sys.path.append(path)

from xcatperf.shell import PerfShell

if __name__ == '__main__':
    try:
        PerfShell().main(sys.argv[1:])
    except KeyboardInterrupt:
        print("... terminating xcat-perf client", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(six.text_type(e), file=sys.stderr)
        print(traceback.format_exc())
        sys.exit(1)
