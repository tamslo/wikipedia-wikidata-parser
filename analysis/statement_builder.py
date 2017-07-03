class StatementBuilder:
    @staticmethod
    def run(property_info, match, sentence):
        # Find token of match in syntactical parse tree
        token = sentence.parse_tree.tokens[match.start_index]

        # Follow compound dependencies
        compounds = [dep.dependent
                     for dep in token.dependencies(role='governor')
                     if dep.dep == 'compound']

        # Build value string
        value_tokens = sorted([token] + compounds, key=lambda x: x.index)
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
