from utils.helpers import first


class PropertyProfiler:
    def __init__(self, syntactical_parser):
        self._syntactical_parser = syntactical_parser

    def run(self, properties):
        profiles = []
        for prop in properties:
            patterns = [self._build_pattern(label) for label in prop.label_aliases]
            patterns = [pattern for pattern in patterns if pattern is not None]
            profiles.append(PropertyProfile(prop, patterns))

        return profiles

    def _build_pattern(self, text):
        # Build syntactical parse tree with lemmas, POS tags and dependencies
        parse_tree = self._syntactical_parser.parse(text, dependency_type='enhanced++')[0]

        # Build pattern depending type of label phrase
        if self._is_verbal_label_phrase(parse_tree):
            return self._build_verb_pattern(parse_tree)
        if self._is_noun_label_phrase(parse_tree):
            return self._build_noun_pattern(parse_tree)

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

    def _build_noun_pattern(self, parse_tree):
        dep_pattern = self._build_dep_pattern(parse_tree.root, parse_tree)
        return '{{}} >nsubj ({})'.format(dep_pattern)

    def _build_verb_pattern(self, parse_tree):
        # Check root node has any dependency to prepositions, which can be
        # included into relation name
        relation_name = 'nmod'
        governor_dependencies = parse_tree.root.dependencies('governor')
        prep_dependency = first(dep for dep in governor_dependencies
                                if dep.dependent.pos == 'IN')
        if prep_dependency:
            dependent = prep_dependency.dependent
            relation_name = '{}:{}'.format(relation_name,
                                           dependent.word.lower())

        # Build relation and dependent patterns
        relation_pattern = self._relation_pattern(relation_name, direction='<')
        dep_pattern = self._build_dep_pattern(parse_tree.root,
                                              parse_tree, ['IN'])

        return '{{}} {} ({})'.format(relation_pattern, dep_pattern)

    def _build_dep_pattern(self, token, parse_tree, exclude_pos=None):
        # Set default value for exclude_pos
        exclude_pos = exclude_pos or []

        # Build pattern matching the lemma of the current node
        gov_pattern = self._node_pattern(token)

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
            dep_pattern = self._node_pattern(dependency.dependent)

        # Construct dependency pattern
        relation_pattern = self._relation_pattern(dependency.dep)
        return '{} {} ({})'.format(gov_pattern, relation_pattern, dep_pattern)

    @staticmethod
    def _node_pattern(token):
        return '{{lemma: {}}}'.format(token.lemma)

    @staticmethod
    def _relation_pattern(name, direction='>'):
        return '{}/{}/'.format(direction, name)


class PropertyProfile:
    def __init__(self, property_info, patterns):
        self._property_info = property_info
        self._patterns = patterns

    @property
    def property_info(self):
        return self._property_info

    @property
    def patterns(self):
        return self._patterns
