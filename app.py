import sys
import wikipedia

from clients.wikipedia import WikipediaClient
from clients.wikidata import WikidataClient
from analysis.property_profiler import PropertyProfiler
from analysis.statement_extractor import StatementExtractor
from nlp.corenlp_client import CoreNlpClient
from nlp.syntactical_parser import SyntacticalParser
from nlp.semgrex_matcher import SemgrexMatcher


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
        self.statement_extractor = StatementExtractor(self.semgrex_matcher)

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

        # Apply property patterns on text
        for property_profile in self.property_profiles:
            property_info = property_profile.info
            print('Apply patterns of property {} ({})'.format(property_info.id, property_profile.info.label))
            for sentence in parse_result.sentences:
                # Get statements
                statements = self.statement_extractor.run(sentence,
                                                          property_profile,
                                                          entity_mentions)
                for statement in statements:
                    print('Match found: "{}" in "{}" (Quality: {})'.format(statement.value,
                                                                           sentence.text,
                                                                           statement.quality.name))
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
