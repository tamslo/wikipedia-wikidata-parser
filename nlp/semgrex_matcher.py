class SemgrexMatcher:
    PARSE_ERROR_EXCEPTION_LABEL = 'edu.stanford.nlp.semgraph.semgrex.SemgrexParseException: '

    def __init__(self, core_nlp):
        self._core_nlp = core_nlp

    def run(self, text, pattern, filter=False):
        result = self._core_nlp.http_client.semgrex(text, pattern=pattern, filter=filter)

        # Catch errors
        if isinstance(result, str):
            if result.startswith(self.PARSE_ERROR_EXCEPTION_LABEL):
                message = result.replace(self.PARSE_ERROR_EXCEPTION_LABEL, '')
                raise SemgrexParseException(message)
            else:
                raise Exception(result)

        # Parse matches
        matches = [SemgrexMatch.from_json(match)
                   for key, match in result['sentences'][0].items()
                   if key != 'length']

        return matches


class SemgrexParseException(Exception):
    def __init__(self, message):
        super().__init__(message)


class SemgrexMatch:
    def __init__(self, text, start_index, end_index):
        self._text = text
        self._start_index = start_index
        self._end_index = end_index

    @property
    def text(self):
        return self._text

    @property
    def start_index(self):
        return self._start_index

    @property
    def end_index(self):
        return self._end_index

    @staticmethod
    def from_json(obj):
        return SemgrexMatch(obj['text'],
                            obj['begin'],
                            obj['end'])