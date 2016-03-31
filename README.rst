xcatperf
========

xcatperf is a tool to test xcat concurrenty performance.

Example
-------

Fetch the project ::

  git clone https://github.com/chenglch/xcatperf.git

Install the python dependency ::

  apt-get install python-pip  python-dev
  cd xcatperf
  pip install -r requirements.txt

Disable the xcat service, then start and run test with the following command,
which means running defls test case in 100 nodes environment with 3 concurrency
amount. ::

   python bin/xcat-perf.py -p 3 -c 100 defls.DeflsCase

``defls.DeflsCase`` is a scenario test plugin located in xcatperf/scenario. If
we hope to generate nytperf result, try the following command ::

  python bin/xcat-perf.py -p 3 -c 100 --is-nytprof defls.DeflsCase --nytprof-dir /opt/nytprof/nytprof

*Note:* nytprof option will generate too many files in target directory. More
command options can be found using ``python bin/xcat-perf.py --help`` command.