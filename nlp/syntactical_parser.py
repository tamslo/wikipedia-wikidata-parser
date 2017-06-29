import operator


class SyntacticalParser:
    def __init__(self, core_nlp):
        self._core_nlp = core_nlp

    def parse(self, text, ner=False, dependency_type='basic'):
        annotators = 'lemma,pos,depparse'
        if ner:
            annotators += ',ner'

        annotations = self._core_nlp.http_client.annotate(text, properties={
            'annotators': annotators,
            'outputFormat': 'json'
        })['sentences']

        return [SyntacticalParseTree.from_json(sentence_tree, dependency_type)
                for sentence_tree in annotations]


class SyntacticalParseTree:
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

        return SyntacticalParseTree(root_index, tokens, dependencies)


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
