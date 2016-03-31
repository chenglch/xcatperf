import os
import socket

from xcatperf.common import utils
from eventlet.green.OpenSSL import SSL

@utils.make_synchronized
@utils.singleton
class SSLClient(object):
    def __init__(self, certfile=None, keyfile=None, ca_certs=None):
        home_dir = os.path.expanduser('~')
        self.certfile = certfile or os.path.join(home_dir,
                                                 '.xcat/client-cred.pem')
        self.keyfile = keyfile or os.path.join(home_dir,
                                               '.xcat/client-cred.pem')
        self.ca_certs = ca_certs or os.path.join(home_dir, '.xcat/ca.pem')
        self.context = SSL.Context(SSL.SSLv23_METHOD)
        self.context.use_certificate_file(self.certfile)
        self.context.use_privatekey_file(self.keyfile)
        self.context.set_verify(SSL.VERIFY_NONE, lambda *x: True)

    def get_client(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client = SSL.Connection(self.context, client)
        client.connect(('127.0.0.1', 3001))
        return client
