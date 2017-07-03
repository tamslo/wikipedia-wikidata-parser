class StatementBuilder:
    @staticmethod
    def run(property_info, match):
        # Follow compound dependencies
        compounds = [dep.dependent
                     for dep in match.tokens[0].dependencies(role='governor')
                     if dep.dep == 'compound']

        # Build value string
        value_tokens = sorted([match.tokens[0]] + compounds, key=lambda x: x.index)
        value = ' '.join(token.word for token in value_tokens)

        return Statement(property_info, value)


class Statement:
    def __init__(self, property_info, value):
        self._propety_info = property_info
        self._value = value

    @property
    def property_info(self):
        return self._propety_info

    @property
    def value(self):
        return self._value
