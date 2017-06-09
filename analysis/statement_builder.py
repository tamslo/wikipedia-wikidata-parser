class StatementBuilder:
    def __init__(self, syntactical_parser):
        self._syntactical_parser = syntactical_parser

    def run(self, property_info, match, sentence):
        # Get syntactical parse tree of sentence and find token of match
        parse_tree = self._syntactical_parser.parse(sentence)[0]
        token = parse_tree.tokens[match.start_index]

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
