import sys
import shlex
import logging
import threading
import subprocess
from tempfile import NamedTemporaryFile
from subprocess import PIPE

log = logging.getLogger(__name__)


class Command(object):
    """
    Enables to run subprocess commands in a different thread with TIMEOUT option.
    Based on jcollado's solution:
    http://stackoverflow.com/questions/1191374/subprocess-with-timeout/4825933#4825933
    """
    def __init__(self, command):
        if isinstance(command, str):
            command = shlex.split(command)
        self.command = command

    def run(self, timeout=None, **kwargs):
        """ Run a command then return: (status, output, error). """
        def target(**kwargs):
            try:
                self.process = subprocess.Popen(self.command, **kwargs)
                self.output, self.error = self.process.communicate()
                self.status = self.process.returncode
            except Exception:
                self.error = traceback.format_exc()
                self.status = -1
        # default stdout and stderr
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.PIPE
        # thread
        thread = threading.Thread(target=target, kwargs=kwargs)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
        return type("result", (), {
            "stdout": self.output.decode("utf-8"),
            "stderr": self.error.decode("utf-8"),
            "returncode": self.status
        })


class WeakJail:
    """
    Core Snekbox functionality, providing safe execution of Python code.
    """

    def __init__(self, python_binary: str = sys.executable):
        self.python_binary = python_binary

    def python3(self, code: str):
        with NamedTemporaryFile() as tmp:
            log.info("Executing code...")

        return Command([self.python_binary, "-Iqu", "-c", code]).run(5)
