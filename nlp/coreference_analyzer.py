import os
import json
from tempfile import NamedTemporaryFile


class CoreferenceAnalyzer:
    def __init__(self, core_nlp):
        self._core_nlp = core_nlp

    def run(self, text, algorithm='statistical'):
        with NamedTemporaryFile(mode='w') as text_file:
            # Write text to temporary file so that is can be processed by
            # CoreNLP process
            text_file.write(text)

            # Run CoreNLP as subprocess
            self._core_nlp.run_cmd({
                'annotators': 'tokenize,ssplit,pos,lemma,ner,depparse,parse,mention,coref',
                'coref.algorithm': algorithm,
                'file': text_file.name,
                'outputFormat': 'json'
            })

            # Read results
            result_file_name = os.path.join(self._core_nlp.cwd, os.path.basename(text_file.name) + '.json')
            with open(result_file_name) as result_file:
                results = json.load(result_file)
                return [Coreference.from_json(obj)
                        for obj in results['corefs'].values()]


class Coreference:
    def __init__(self, mentions):
        self._mentions = mentions

    @property
    def mentions(self):
        return self._mentions

    @staticmethod
    def from_json(arr):
        mentions = [Mention.from_json(obj) for obj in arr]
        return Coreference(mentions)


class Mention:
    def __init__(self, sentence_index, start_index, end_index, text):
        self._sentence_index = sentence_index
        self._start_index = start_index
        self._end_index = end_index
        self._text = text

    @property
    def sentence_index(self):
        return self._sentence_index

    @property
    def start_index(self):
        return self._start_index

    @property
    def end_index(self):
        return self._end_index

    @property
    def text(self):
        return self._text

    @staticmethod
    def from_json(obj):
        return Mention(obj['sentNum'] - 1,
                       obj['startIndex'] - 1,
                       obj['endIndex'] - 1,
                       obj['text'])
