import sys
import wikipedia

from clients.wikipedia import WikipediaClient
from clients.wikidata import WikidataClient
from analysis.property_profiler import PropertyProfiler
from analysis.statement_builder import StatementBuilder
from nlp.corenlp_client import CoreNlpClient
from nlp.syntactical_parser import SyntacticalParser
from nlp.semgrex_matcher import SemgrexMatcher, SemgrexParseException


class WikipediaWikidataParser:
    def __init__(self, core_nlp):
        # Initialize API clients
        self.wp_client = WikipediaClient()
        self.wd_client = WikidataClient('data/wd_properties_sample.json')

        # Load static resources
        self.wd_properties = self.wd_client.get_properties()

        # Initialize services
        self.syntactical_parser = SyntacticalParser(core_nlp)
        self.semgrex_matcher = SemgrexMatcher(core_nlp)
        self.property_profiler = PropertyProfiler(self.syntactical_parser)
        self.statement_builder = StatementBuilder()

        # Generate property profiles
        print("Building property patterns...")
        self.property_profiles = self.property_profiler.run(self.wd_properties)

    def run(self):
        # Get wikipedia article
        wp_article = self._get_wp_article()

        # Syntactically parse the entire article
        print("Analyzing article...")
        parse_result = self.syntactical_parser.parse(wp_article.sanitized_content)
        entity_mentions = parse_result.coreferences.mentions_of(wp_article.title)

        # Filter sentences to include only those, in which the entity of
        # the article is mentioned
        coref_sentence_indices = set(mention.sentence_index for mention in entity_mentions)

        # Apply property patterns on text
        for property_profile in self.property_profiles:
            property_info = property_profile.property_info
            print('Apply patterns of property {} ({})'.format(property_info.id, property_profile.property_info.label))
            for raw_pattern in property_profile.patterns:
                for i in coref_sentence_indices:
                    # Get indices of subject from corefs
                    subject_indices = [mention.start_index
                                       for mention in entity_mentions
                                       if mention.sentence_index == i]
                    compiled_pattern = raw_pattern.build(subject_indices)

                    # Get statements
                    statements = self._extract_statements(parse_result.sentences[i],
                                                          property_info,
                                                          compiled_pattern)
            print()

    def _get_wp_article(self):
        while True:
            # TODO title = input('Wikipedia Article? ')
            title = 'Douglas Adams'
            try:
                return self.wp_client.get_article(title)
            except wikipedia.DisambiguationError as e:
                print('{} may refer to:'.format(title))
                for option in e.options:
                    print(option)

    def _extract_statements(self, sentence, property_info, pattern):
        statements = []
        try:
            matches = self.semgrex_matcher.run(sentence.text, pattern)
            for match in matches:
                statement = self.statement_builder.run(property_info, match,
                                                       sentence)
                statements.append(statement)
                print('Match found: "{}" in "{}"'.format(statement.value,
                                                         sentence.text))
        except (TimeoutError, SemgrexParseException) as e:
            print(e)

        return statements

if __name__ == '__main__':
    # Read arguments
    if len(sys.argv) <= 1:
        print('Usage: python app.py [CORE_NLP_DIR]')
    core_nlp_dir = sys.argv[1]

    # Initialize CoreNLP client
    print("Starting CoreNLP...")
    core_nlp = CoreNlpClient(core_nlp_dir)
    core_nlp.start()

    # Run app
    try:
        app = WikipediaWikidataParser(core_nlp)
        app.run()
    finally:
        print("Shutting down CoreNLP...")
        core_nlp.stop()
