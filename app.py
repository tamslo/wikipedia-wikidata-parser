import sys
import wikipedia
from termcolor import cprint

from clients.wikipedia import WikipediaClient
from clients.wikidata import WikidataClient
from analysis.property_profiler import PropertyProfiler
from analysis.wikidata_entity_lookup import WikidataEntityLookup
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
        self.wikidata_entity_lookup = WikidataEntityLookup()
        self.statement_extractor = StatementExtractor(self.semgrex_matcher, self.wikidata_entity_lookup)

        # Generate property profiles
        print('Building property patterns...')
        self.property_profiles = self.property_profiler.run(self.wd_properties)

    def run(self, title):
        # Get wikipedia article
        wp_article = self._get_wp_article(title)

        # Syntactically parse the entire article
        print('Parsing article...')
        content_parse_result = self.syntactical_parser.parse(wp_article.sanitized_content, dependency_type='enhanced++')

        # Filter out mentions with wrong NER tag
        entity_mentions = content_parse_result.coreferences.mentions_of(wp_article.title)
        title_parse_result = self.syntactical_parser.parse(wp_article.title, http=True)
        title_ner_tokens = [token.ner for token in title_parse_result.sentences[0].parse_tree.tokens if token.ner]
        if len(set(title_ner_tokens)) == 1:
            title_ner = title_ner_tokens[0]
            entity_mentions = [mention for mention in entity_mentions
                               if all([token.ner is None for token in mention.tokens])
                               or all([token.ner == title_ner for token in mention.tokens])]

        # Apply property patterns on text
        print('Applying property patterns to article...')
        cprint('\nRESULTS', attrs=['bold'])
        statements = []
        for property_profile in self.property_profiles:
            property_info = property_profile.info
            cprint('Property {} ({})'.format(property_info.id, property_profile.info.label), attrs=['bold'])
            for sentence in content_parse_result.sentences:
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

    def _get_wp_article(self, title):
        try:
            return self.wp_client.get_article(title)
        except wikipedia.DisambiguationError as e:
            print('{} may refer to:'.format(title))
            for option in e.options:
                print(option)
            sys.exit(1)

if __name__ == '__main__':
    # Read arguments
    if len(sys.argv) <= 1:
        print('Usage: python app.py [CORE_NLP_DIR] [ARTICLE_TITLE] [--verbose]')
    core_nlp_dir = sys.argv[1]
    article_title = sys.argv[2]
    verbose = '--verbose' in sys.argv

    # Initialize CoreNLP client
    print('Starting CoreNLP...')
    core_nlp = CoreNlpClient(core_nlp_dir, verbose=verbose)
    core_nlp.start()

    # Run app
    try:
        app = WikipediaWikidataParser(core_nlp)
        app.run(article_title)
    finally:
        core_nlp.stop()
