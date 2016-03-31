from xcatperf import base


class FakeCase(base.BaseCase):
    def __init__(self, *args, **kwargs):
        super(FakeCase, self).__init__(is_nytprof=False)

    def _fake_test(self):
        print "hello world"

    def run(self, concurrency):
        func_list = [self._fake_test]
        self.spawn(concurrency, func_list)
