import os
import json
import operator
from tempfile import NamedTemporaryFile


class SyntacticalParser:
    ANNOTATORS = ['tokenize', 'ssplit', 'pos', 'lemma', 'ner',
                  'parse', 'depparse', 'dcoref']

    def __init__(self, core_nlp):
        self._core_nlp = core_nlp

    def parse(self, text, dependency_type='basic', http=False):
        result = self._core_nlp.annotate(text, self.ANNOTATORS, http=http)

        return SyntacticParsingResult.from_json(result, text, dependency_type)


class SyntacticParsingResult:
    def __init__(self, sentences, coreferences):
        self._sentences = sentences
        self._coreferences = coreferences

    @property
    def sentences(self):
        return self._sentences

    @property
    def coreferences(self):
        return self._coreferences

    @staticmethod
    def from_json(obj, document, dependency_type):
        sentences = [Sentence.from_json(sentence, document, dependency_type)
                       for sentence in obj['sentences']]
        coreferences = CoreferenceCollection.from_json(obj['corefs'], sentences)

        return SyntacticParsingResult(sentences, coreferences)


class Sentence:
    def __init__(self, text, parse_tree):
        self._text = text
        self._parse_tree = parse_tree

    @property
    def text(self):
        return self._text

    @property
    def parse_tree(self):
        return self._parse_tree

    def __str__(self):
        return self.text

    @staticmethod
    def from_json(obj, document, dependency_type):
        start = obj['tokens'][0]['characterOffsetBegin']
        end = obj['tokens'][-1]['characterOffsetEnd']

        return Sentence(document[start:end],
                        ParseTree.from_json(obj, dependency_type))


class ParseTree:
    def __init__(self, root_index=None, tokens=None, dependencies=None):
        self._root_index = root_index
        self._tokens = tokens or []
        self._dependencies = dependencies or []

        # Register tree at tokens and dependencies
        for entity in self.tokens + self.dependencies:
            entity._tree = self

        # Sort tokens by index
        self._tokens = sorted(self._tokens, key=operator.attrgetter('index'))

    @property
    def root(self):
        return self.tokens[self._root_index]

    @property
    def tokens(self):
        return self._tokens

    @property
    def dependencies(self):
        return self._dependencies

    @staticmethod
    def from_json(obj, dependency_type='basic'):
        tokens = [Token.from_json(None, token_obj)
                  for token_obj in obj['tokens']]

        dependency_type = {
            'basic': 'basicDependencies',
            'enhanced': 'enhancedDependencies',
            'enhanced++': 'enhancedPlusPlusDependencies'
        }[dependency_type]
        dependencies = [Dependency.from_json(None, dependency_obj)
                        for dependency_obj in obj[dependency_type]
                        if dependency_obj['dep'] != 'ROOT']
        root_index = next(dependency_obj['dependent'] - 1
                          for dependency_obj in obj[dependency_type]
                          if dependency_obj['dep'] == 'ROOT')

        return ParseTree(root_index, tokens, dependencies)


class Token:
    def __init__(self, tree, index, original_text, word, lemma, pos, ner):
        self._tree = tree
        self._index = index
        self._original_text = original_text
        self._word = word
        self._lemma = lemma
        self._pos = pos
        self._ner = ner

    @property
    def index(self):
        return self._index

    @property
    def original_text(self):
        return self._original_text

    @property
    def word(self):
        return self._word

    @property
    def lemma(self):
        return self._lemma

    @property
    def pos(self):
        return self._pos

    @property
    def ner(self):
        return self._ner

    def has_dependencies(self, role=None):
        try:
            next(self.dependencies(role))
        except StopIteration:
            return False

    def dependencies(self, role=None):
        for dependency in self._tree.dependencies:
            is_governor = dependency.governor == self
            is_dependent = dependency.dependent == self
            if role is None and (is_governor or is_dependent) or \
               role == 'governor' and is_governor or \
               role == 'dependent' and is_dependent:
                yield dependency

    def __str__(self):
        return self.original_text

    @staticmethod
    def from_json(tree, obj):
        ner = None
        if 'ner' in obj and obj['ner'] != '0':
            ner = obj['ner']

        return Token(tree,
                     obj['index'] - 1,
                     obj['originalText'],
                     obj['word'],
                     obj['lemma'],
                     obj['pos'],
                     ner)


class Dependency:
    def __init__(self, tree, governor_index, dependent_index, dep):
        self._tree = tree
        self._governor_index = governor_index
        self._dependent_index = dependent_index
        self._dep = dep

    @property
    def governor(self):
        return self._tree.tokens[self._governor_index]

    @property
    def dependent(self):
        return self._tree.tokens[self._dependent_index]

    @property
    def dep(self):
        return self._dep

    def __str__(self):
        return self.dep

    @staticmethod
    def from_json(tree, obj):
        return Dependency(tree,
                          obj['governor'] - 1,
                          obj['dependent'] - 1,
                          obj['dep'])


class CoreferenceCollection:
    def __init__(self, coreferences):
        self._coreferences = coreferences

    def mentions_of(self, entity):
        corefs = [coref for coref in self._coreferences
                  if any(mention.text in entity or entity in mention.text
                         for mention in coref.mentions)]
        return [mention for coref in corefs for mention in coref.mentions]

    def __iter__(self):
        return iter(self._coreferences)

    def __str__(self):
        return '[{}]'.format(', '.join(self._coreferences))

    @staticmethod
    def from_json(obj, sentences):
        return CoreferenceCollection([Coreference.from_json(x, sentences)
                                      for x in obj.values()])


class Coreference:
    def __init__(self, mentions):
        self._mentions = mentions

    @property
    def mentions(self):
        return self._mentions

    def __str__(self):
        if self.mentions:
            return str(self.mentions[0])

    @staticmethod
    def from_json(arr, sentences):
        mentions = [Mention.from_json(obj, sentences) for obj in arr]
        return Coreference(mentions)


class Mention:
    def __init__(self, sentence, tokens):
        self._sentence = sentence
        self._tokens = tokens

    @property
    def sentence(self):
        return self._sentence

    @property
    def tokens(self):
        return self._tokens

    @property
    def text(self):
        return ' '.join([token.original_text for token in self.tokens])

    def __str__(self):
        return self.text

    @staticmethod
    def from_json(obj, sentences):
        # Extract properties from json object
        start_index = obj['startIndex'] - 1
        end_index = obj['endIndex'] - 1
        sentence_index = obj['sentNum'] - 1

        # Get sentence and tokens of mention
        sentence = sentences[sentence_index]
        tokens = [token for token in sentence.parse_tree.tokens
                  if start_index <= token.index < end_index]

        return Mention(sentence, tokens)
