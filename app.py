import sys
import wikipedia
from termcolor import cprint

from clients.wikipedia import WikipediaClient
from clients.wikidata import WikidataClient
from analysis.property_profiler import PropertyProfiler
from analysis.statement_extractor import StatementExtractor, StatementQuality
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
        print("Parsing article...")
        parse_result = self.syntactical_parser.parse(wp_article.sanitized_content)
        entity_mentions = parse_result.coreferences.mentions_of(wp_article.title)

        # Apply property patterns on text
        print("Applying property patterns to article...")
        cprint('\nRESULTS', attrs=['bold'])
        statements = []
        for property_profile in self.property_profiles:
            property_info = property_profile.info
            cprint('Property {} ({})'.format(property_info.id, property_profile.info.label), attrs=['bold'])
            for sentence in parse_result.sentences:
                # Get statements
                property_statements = self.statement_extractor.run(sentence,
                                                          property_profile,
                                                          entity_mentions)
                statements += property_statements

                # Print detected statements
                for statement in property_statements:
                    cprint('Found value "{}" in "{}" (Quality: {})'.format(statement.value,
                                                                           sentence.text,
                                                                           statement.quality.name),
                           'green' if statement.quality == StatementQuality.ACCURATE else 'yellow')
            print()

        # Print summary
        cprint('\nSUMMARY', attrs=['bold'])
        print('{} statements were extracted in total.'.format(len(statements)))
        for quality in set([statement.quality for statement in statements]):
            count = len([x for x in statements if x.quality == quality])
            print('{} of these have quality {}.'.format(count, quality.name))

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
        print('Usage: python app.py [CORE_NLP_DIR] [--verbose]')
    core_nlp_dir = sys.argv[1]
    verbose = len(sys.argv) >= 3 and sys.argv[2] == '--verbose'

    # Initialize CoreNLP client
    print("Starting CoreNLP...")
    core_nlp = CoreNlpClient(core_nlp_dir, verbose=verbose)
    core_nlp.start()

    # Run app
    try:
        app = WikipediaWikidataParser(core_nlp)
        app.run()
    finally:
        core_nlp.stop()
