from utils.helpers import first


class SemgrexMatcher:
    PARSE_ERROR_EXCEPTION_LABEL = 'edu.stanford.nlp.semgraph.semgrex.SemgrexParseException: '
    TIMEOUT_ERROR_RESULT_LABEL = 'Timeout'

    def __init__(self, core_nlp):
        self._core_nlp = core_nlp

    def run(self, sentence, pattern, filter=False):
        result = self._core_nlp.semgrex(sentence.text, pattern, filter)

        # Catch errors
        if isinstance(result, str):
            if result.startswith(self.PARSE_ERROR_EXCEPTION_LABEL):
                message = result.replace(self.PARSE_ERROR_EXCEPTION_LABEL, '')
                raise SemgrexParseException(message)
            elif result.startswith(self.TIMEOUT_ERROR_RESULT_LABEL):
                raise TimeoutError(result)
            else:
                raise Exception(result)

        # Parse matches
        matches = [SemgrexMatch.from_json(match, sentence)
                   for key, match in result['sentences'][0].items()
                   if key != 'length']

        return matches


class SemgrexParseException(Exception):
    def __init__(self, message):
        super().__init__(message)


class SemgrexMatch:
    def __init__(self, tokens, named_tokens):
        self._tokens = tokens
        self._named_tokens = named_tokens

    @property
    def tokens(self):
        return self._tokens

    @property
    def named_tokens(self):
        return self._named_tokens

    def __str__(self):
        return self.tokens.original_text

    @staticmethod
    def from_json(obj, sentence):
        # Get tokens of match and named nodes, if any
        tokens = SemgrexMatch._get_tokens_from_json(obj, sentence)
        named_tokens = {key[1:]: SemgrexMatch._get_tokens_from_json(value, sentence)
                        for key, value in obj.items()
                        if key.startswith('$')}

        return SemgrexMatch(tokens, named_tokens)

    @staticmethod
    def _get_tokens_from_json(obj, sentence):
        # Extract position from json object
        start_index = obj['begin']
        end_index = obj['end']

        return [token for token in sentence.parse_tree.tokens
                if start_index <= token.index < end_index]

