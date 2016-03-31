import six


class PerfException(Exception):
    """Base Perf Exception

    To correctly use this class, inherit from it and define
    a '_msg_fmt' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    If you need to access the message from an exception you should use
    six.text_type(exc)

    """
    _msg_fmt = "An unknown exception occurred."

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if not message:
            # Check if class is using deprecated 'message' attribute.
            if (hasattr(self, 'message') and self.message):
                self._msg_fmt = self.message

            try:
                message = self._msg_fmt % kwargs

            except Exception as e:
                message = self._msg_fmt

        super(PerfException, self).__init__(message)

    def __str__(self):
        """Encode to utf-8 then wsme api can consume it as well."""
        if not six.PY3:
            return unicode(self.args[0]).encode('utf-8')

        return self.args[0]

    def __unicode__(self):
        """Return a unicode representation of the exception message."""
        return unicode(self.args[0])


class NoPidFile(PerfException):
    _msg_fmt = "Could not find pid in pid file %(pid_path)s"


class DaemonError(PerfException):
    pass


class FileNotFound(PerfException):
    _msg_fmt = "File %(file)s not found"


class CommondNotFound(PerfException):
    _msg_fmt = "Command %(cmd)s not found"


class NoPidError(PerfException):
    _msg_fmt = "process %(pid)s is not exist"


class CommandError(PerfException):
    _msg_fmt = "Error to execute command %(cmd)s"


class XMLError(PerfException):
    _msg_fmt = "Error to parse xml %(content)s"


class TimeoutError(PerfException):
    _msg_fmt = "Timeout to wait %(prog)s"


class InvalidValue(PerfException):
    _msg_fmt = "InvalidValue %(err)s"


class UnexpectedError(PerfException):
    _msg_fmt = "Unexpeted error: %(err)s"
