import os
import time
import json
import requests
import subprocess
from tempfile import NamedTemporaryFile
from requests.exceptions import ConnectionError
from pycorenlp import StanfordCoreNLP


class CoreNlpClient:
    SERVER_URL = 'http://localhost:9000'
    COMMAND_PATTERN = 'java -Xmx{} -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLP {}'
    SERVER_COMMAND_PATTERN = 'java -Xmx{} -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -timeout {}'

    def __init__(self, cwd, memory='4g', timeout=15000, verbose=False):
        self._cwd = cwd
        self._memory = memory
        self._timeout = timeout
        self._verbose = verbose

        self._process = None
        self._http_client = None

    def start(self):
        command = self.SERVER_COMMAND_PATTERN.format(self._memory,
                                                     self._timeout)
        self._process = self._open_process(command, wait=False)
        self._wait_for_server()
        self._http_client = StanfordCoreNLP(self.SERVER_URL)

    def stop(self):
        self._process.kill()

    def annotate(self, text, annotators, properties=None, http=False):
        # Build properties
        properties = properties or {}
        properties = {**properties, **{'outputFormat': 'json',
                                       'annotators': ','.join(annotators)}}

        # Run annotators via HTTP request or command line execution
        if http:
            if self._http_client is None:
                raise Exception('CoreNLP client is not running!')
            return self._http_client.annotate(text, properties)
        else:
            return self._annotate_cmd(text, properties)

    def _annotate_cmd(self, text, properties):
        with NamedTemporaryFile(mode='w') as text_file:
            # Write text to temporary file so that is can be processed by
            # CoreNLP process
            text_file.write(text)
            text_file.flush()

            # Run CoreNLP as subprocess
            self._run_cmd({**properties, **{'file': text_file.name}})

            # Read results and delete result file afterwards
            result_file_name = os.path.join(self._cwd, os.path.basename(text_file.name) + '.json')
            with open(result_file_name) as result_file:
                results = json.load(result_file)
            os.remove(result_file_name)

            return results

    def semgrex(self, text, pattern, filter=False):
        if self._http_client is None:
            raise Exception('CoreNLP client is not running!')

        return self._http_client.semgrex(text, pattern=pattern, filter=filter)

    def _run_cmd(self, properties):
        arguments = ' '.join(['-{} {}'.format(key, value)
                              for key, value in properties.items()])
        command = self.COMMAND_PATTERN.format(self._memory, arguments)
        return self._open_process(command)

    def _open_process(self, command, wait=True):
        output = None if self._verbose else subprocess.DEVNULL
        process = subprocess.Popen(command, cwd=self._cwd, shell=True,
                                   stdout=output, stderr=output)
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
