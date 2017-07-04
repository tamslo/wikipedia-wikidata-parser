from enum import Enum
from termcolor import colored

from nlp.semgrex_matcher import SemgrexParseException


class StatementExtractor:
    DATA_TYPE_NER_MAPPING = {
        'wikibase-item': ['PERSON', 'ORGANIZATION', 'LOCATION'],
        'quantity': ['NUMBER', 'MONEY', 'PERCENT'],
        'time': ['DATE', 'TIME']
    }

    def __init__(self, semgrex_matcher):
        self._semgrex_matcher = semgrex_matcher

    def run(self, sentence, property_profile, entity_mentions):
        statements = []
        for pattern in property_profile.patterns:
            matches = self._apply_pattern(sentence, pattern)
            statements += [self._build_statement(property_profile.info, match, entity_mentions)
                           for match in matches]

        return statements

    def _apply_pattern(self, sentence, pattern):
        try:
            matches = self._semgrex_matcher.run(sentence, pattern)
        except (TimeoutError, SemgrexParseException) as e:
            print(colored('Error: ' + e))
            return []

        return matches

    def _build_statement(self, property_info, match, entity_mentions):
        value = self._extend_value(match.named_tokens['value'][0])
        quality = self._validate_match(property_info, match, entity_mentions)

        return Statement(property_info, value, quality)

    def _validate_match(self, property_info, match, entity_mentions):
        # Check if subject is coreference of entity
        subject_token = match.named_tokens['subject'][0]
        if not any(subject_token in mention.tokens
                   for mention in entity_mentions):
            return StatementQuality.WRONG_SUBJECT

        # Check, if value matches property data type using NER
        valid_ner_tags = self.DATA_TYPE_NER_MAPPING[property_info.data_type]
        value_token = match.named_tokens['value'][0]
        if value_token.ner not in valid_ner_tags:
            return StatementQuality.WRONG_VALUE_TYPE

        return StatementQuality.ACCURATE

    @staticmethod
    def _extend_value(root_token):
        # Use normalized NER, if present
        if root_token.normalized_ner:
            return root_token.normalized_ner

        # Follow compound dependencies
        compounds = [dep.dependent
                     for dep in root_token.dependencies(role='governor')
                     if dep.dep == 'compound']

        # Build value string
        value_tokens = sorted([root_token] + compounds, key=lambda x: x.index)
        value = ' '.join(token.word for token in value_tokens)

        return value


class Statement:
    def __init__(self, property_info, value, quality):
        self._property_info = property_info
        self._value = value
        self._quality = quality

    @property
    def property_info(self):
        return self._property_info

    @property
    def value(self):
        return self._value

    @property
    def quality(self):
        return self._quality

    def __str__(self):
        return '{}: {}'.format(self.property_info.label, self.value)


class StatementQuality(Enum):
    ACCURATE = 'accurate',
    WRONG_SUBJECT = 'wrong_subject',
    WRONG_VALUE_TYPE = 'wrong_value_type'
