from enum import Enum
from termcolor import colored

from nlp.semgrex_matcher import SemgrexParseException


class StatementExtractor:
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
        # Follow compound dependencies
        compounds = [dep.dependent
                     for dep in match.tokens[0].dependencies(role='governor')
                     if dep.dep == 'compound']

        # Build value string
        value_tokens = sorted([match.tokens[0]] + compounds, key=lambda x: x.index)
        value = ' '.join(token.word for token in value_tokens)

        # Validate quality of match
        quality = self._validate_match(property_info, match, entity_mentions)

        return Statement(property_info, value, quality)

    def _validate_match(self, property_info, match, entity_mentions):
        # Check if subject is coreference of entity
        subject_token = match.named_tokens['subject'][0]
        if not any(subject_token in mention.tokens
                   for mention in entity_mentions):
            return StatementQuality.WRONG_SUBJECT

        # TODO Check, if value matches property type using NER

        return StatementQuality.ACCURATE


class Statement:
    def __init__(self, property_info, value, quality):
        self._propety_info = property_info
        self._value = value
        self._quality = quality

    @property
    def property_info(self):
        return self._propety_info

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
