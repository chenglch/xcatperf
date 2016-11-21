xcatperf
========

xcatperf is a tool to test xcat concurrenty performance.

Setup xcat
----------
::

   wget https://xcat.org/files/go-xcat -O - >/tmp/go-xcat
   chmod +x /tmp/go-xcat
   /tmp/go-xcat

Setup nytprof dependency
------------------
::

  cd /tmp
  wget http://search.cpan.org/CPAN/authors/id/P/PE/PEREINAR/File-Which-0.05.tar.gz
  tar xvfz File-Which-0.05.tar.gz
  cd File-Which-0.05/ && perl Makefile.PL
  make && make install
  wget http://search.cpan.org/CPAN/authors/id/T/TI/TIMB/Devel-NYTProf-6.03.tar.gz
  tar xvfz Devel-NYTProf-6.03.tar.gz
  cd Devel-NYTProf-6.03/ && perl Makefile.PL
  make && make install

Run xcat with nytprof
---------------------
::

  chtab  key=enableperf site.value=1  # make sure xcat daemon is running at this step
  service xcatd stop
  export NYTPROF=start=no
  perl -dt:NYTProf /opt/xcat/sbin/xcatd -f

Test case Example
-----------------

Fetch the project ::

  git clone https://github.com/chenglch/xcatperf.git

Install the python dependency ::

  apt-get install python-pip  python-dev
  cd xcatperf
  pip install -r requirements.txt

Disable the xcat service, then start and run test with the following command,
which means running defls test case in 100 nodes environment with 3 concurrency
value. ::

   python bin/xcat-perf.py -p 3 -c 100 defls.DeflsCase

``defls.DeflsCase`` is a scenario test plugin located in xcatperf/scenario. If
we hope to generate nytperf result, try the following command ::

  python bin/xcat-perf.py -p 3 -c 100 --is-nytprof defls.DeflsCase --nytprof-dir /opt/nytprof/nytprof --http-url http://10.5.101.10:8086/

*Note:* nytprof option will generate too many files in target directory. More
command options can be found using ``python bin/xcat-perf.py --help`` command.

Configure apache2 service for nytprf
------------------------------------
::

  cp etc/xcat-nytprof.conf.example /etc/apache2/sites-available/xcat-nytprof.conf
  # edit xcat-nytprof.conf to meet your requiriment
  cd /etc/apache2/sites-enabled && ln -s ../sites-available/xcat-nytprof.conf xcat-nytprof.conf
  cd -

View the results
----------------
Open url http://10.5.101.10:8086/ to see the results for every process.
