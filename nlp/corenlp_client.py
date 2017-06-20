import time
import requests
import subprocess
from requests.exceptions import ConnectionError
from pycorenlp import StanfordCoreNLP


class CoreNlpClient:
    SERVER_URL = 'http://localhost:9000'
    COMMAND_PATTERN = 'java -Xmx{} -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP {}'
    SERVER_COMMAND_PATTERN = 'java -Xmx{} -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -timeout {}'

    def __init__(self, cwd, memory='4g', timeout=10000):
        self._cwd = cwd
        self._memory = memory
        self._timeout = timeout

        self._process = None
        self._http_client = None

    @property
    def http_client(self):
        return self._http_client

    @property
    def cwd(self):
        return self._cwd

    def start(self):
        command = self.SERVER_COMMAND_PATTERN.format(self._memory,
                                                     self._timeout)
        self._process = self._open_process(command, wait=False)
        self._wait_for_server()
        self._http_client = StanfordCoreNLP(self.SERVER_URL)

    def stop(self):
        self._process.kill()

    def run_cmd(self, properties):
        arguments = ' '.join(['-{} {}'.format(key, value)
                              for key, value in properties.items()])
        command = self.COMMAND_PATTERN.format(self._memory, arguments)
        return self._open_process(command)

    def _open_process(self, command, wait=True):
        process = subprocess.Popen('exec ' + command, cwd=self._cwd,
                                   shell=True, stdout=subprocess.PIPE)
        if wait:
            process.wait()
        else:
            return process

    def _wait_for_server(self):
        ready = False
        try:
            response = requests.get(self.SERVER_URL + '/ready')
            ready = response.status_code == 200 and response.text.startswith('ready')
        except ConnectionError:
            pass

        if not ready:
            time.sleep(1)
            self._wait_for_server()
