from utils.helpers import first


class PropertyProfiler:
    PREPOSITION_RELATION_MAPPING = {
        'by': 'nmod:agent'
    }
    DATA_TYPE_POS_MAPPING = {
        'wikibase-item': ['NN.*'],
        'quantity': ['CD'],
        'time': ['CD', 'NNP']
    }
    NP_SUBJECT_RELATIONS = ['>/nmod:poss/', '>/nmod:of/']
    NP_LABEL_ROOT_RELATIONS = ['>nsubj', '<appos']
    VP_SUBJECT_RELATIONS = ['>nsubj', '>nsubjpass', '<acl']

    def __init__(self, syntactical_parser):
        self._syntactical_parser = syntactical_parser

    def run(self, properties):
        profiles = []
        for prop in properties:
            patterns = [self._build_pattern(prop, label) for label in prop.label_aliases]
            patterns = [pattern for pattern in patterns if pattern is not None]
            profiles.append(PropertyProfile(prop, patterns))

        return profiles

    def _build_pattern(self, prop, text):
        # Build syntactical parse tree with lemmas, POS tags and dependencies
        parse_result = self._syntactical_parser.parse(text, dependency_type='enhanced++', http=True)
        parse_tree = parse_result.sentences[0].parse_tree

        # Ignore malformed labels for that a pattern cannot be created properly
        if self.is_malformed_label(parse_tree):
            return None

        # Build pattern depending type of label phrase
        value_node = self._build_value_node(prop)
        if self._is_verbal_label_phrase(parse_tree):
            return self._build_verb_pattern(value_node, parse_tree)
        if self._is_noun_label_phrase(parse_tree):
            return self._build_noun_pattern(value_node, parse_tree)

    @staticmethod
    def is_malformed_label(parse_tree):
        return any(dep.dep == 'punct' for dep in parse_tree.dependencies)

    @staticmethod
    def _is_noun_label_phrase(parse_tree):
        # Label phrase is noun phrase, if pos of root is any noun token (NN*)
        return parse_tree.root.pos.startswith('NN')

    @staticmethod
    def _is_verbal_label_phrase(parse_tree):
        # Label phrase is verbal phrase, if pos of root is VB or root has
        # cop dependency to any verbal token (VB*)
        return parse_tree.root.pos.startswith('VB') or \
               any(dep.dep == 'cop' and dep.dependent.pos.startswith('VB')
                   for dep in parse_tree.root.dependencies('governor'))

    def _build_noun_pattern(self, value_node, parse_tree):
        dep_pattern = self._build_dep_pattern(parse_tree.root, parse_tree)
        return self._compile_pattern(self.NP_SUBJECT_RELATIONS,
                                     value_node,
                                     self.NP_LABEL_ROOT_RELATIONS,
                                     dep_pattern)

    def _build_verb_pattern(self, value_node, parse_tree):
        # Check root node has any dependency to prepositions, which can be
        # included into relation name
        relation_name = 'nmod'
        governor_dependencies = parse_tree.root.dependencies('governor')
        prep_dependency = first(dep for dep in governor_dependencies
                                if dep.dependent.pos == 'IN')
        if prep_dependency:
            dependent = prep_dependency.dependent
            if dependent.word in self.PREPOSITION_RELATION_MAPPING:
                relation_name = self.PREPOSITION_RELATION_MAPPING[dependent.word]
            else:
                relation_name = '{}:{}'.format(relation_name,
                                               dependent.word.lower())

        # Build relation and dependent patterns
        relation_pattern = self._relation_pattern(relation_name, direction='<')
        dep_pattern = self._build_dep_pattern(parse_tree.root,
                                              parse_tree, ['IN'])

        return self._compile_pattern(self.VP_SUBJECT_RELATIONS,
                                     value_node,
                                     [relation_pattern],
                                     dep_pattern)

    def _build_dep_pattern(self, token, parse_tree, exclude_pos=None):
        # Set default value for exclude_pos
        exclude_pos = exclude_pos or []

        # Build pattern matching the lemma of the current node
        gov_pattern = self._lemma_pattern(token)

        # Get first dependency of current node and build pattern for relation.
        # Further dependencies are ignored so far.
        dependency = first(token.dependencies('governor'))
        if dependency is None or dependency.dependent.pos in exclude_pos:
            # If current node has no dependencies, return the node pattern
            return gov_pattern

        # If dependent node has further dependencies, follow those recursively.
        # Otherwise build patterns for dependent node
        if dependency.dependent.has_dependencies('governor'):
            dep_pattern = self._build_dep_pattern(dependency.dependent,
                                                  parse_tree)
        else:
            dep_pattern = self._lemma_pattern(dependency.dependent)

        # Construct dependency pattern
        relation_pattern = self._relation_pattern(dependency.dep)
        return '{} {} ({})'.format(gov_pattern, relation_pattern, dep_pattern)

    def _build_value_node(self, prop):
        return self._pos_pattern(self.DATA_TYPE_POS_MAPPING[prop.data_type])

    @staticmethod
    def _compile_pattern(subject_relations, value_node,
                         label_root_relations, label_pattern):
        # Build subpattern matching subject of sentence
        subject_relation_patterns = ['{} {{}}=subject'.format(relation)
                                     for relation in subject_relations]
        subject_pattern = '[{}]'.format('|'.join(subject_relation_patterns))

        # Build subpattern matching label of corresponding property
        label_relation_patterns = ['{} ({} {})'.format(relation, label_pattern,
                                                       subject_pattern)
                                   for relation in label_root_relations]
        relation_pattern = '[{}]'.format('|'.join(label_relation_patterns))

        return '{}=value {}'.format(value_node, relation_pattern)

    @staticmethod
    def _lemma_pattern(token):
        return '{{lemma: {}}}'.format(token.lemma)

    @staticmethod
    def _pos_pattern(tags):
        if isinstance(tags, str):
            tags = [tags]

        return '{{tag: /{}/}}'.format('|'.join(tags))

    @staticmethod
    def _relation_pattern(name, direction='>'):
        return '{}/{}/'.format(direction, name)


class PropertyProfile:
    def __init__(self, info, patterns):
        self._info = info
        self._patterns = patterns

    @property
    def info(self):
        return self._info

    @property
    def patterns(self):
        return self._patterns
