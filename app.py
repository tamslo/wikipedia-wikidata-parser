import wikipedia
from pycorenlp import StanfordCoreNLP

from clients.wikipedia import WikipediaClient
from clients.wikidata import WikidataClient
from analysis.property_profiler import PropertyProfiler
from analysis.property_value_extractor import PropertyValueExtractor
from nlp.syntactical_parser import SyntacticalParser
from nlp.semgrex_matcher import SemgrexMatcher, SemgrexParseException
from nlp.sentence_splitter import SentenceSplitter


class WikipediaWikidataParser:
    def __init__(self, core_nlp_host='localhost', core_nlp_port=9000):
        # Initialize CoreNLP client
        self.core_nlp = StanfordCoreNLP('http://{}:{}'.format(core_nlp_host,
                                                              core_nlp_port))

        # Initialize API clients
        self.wp_client = WikipediaClient()
        self.wd_client = WikidataClient('data/wd_properties_sample.json')

        # Load static resources
        self.wd_properties = self.wd_client.get_properties()

        # Initialize services
        self.syntactical_parser = SyntacticalParser(self.core_nlp)
        self.semgrex_matcher = SemgrexMatcher(self.core_nlp)
        self.sentence_splitter = SentenceSplitter(self.core_nlp)
        self.property_profiler = PropertyProfiler(self.syntactical_parser)
        self.property_value_extractor = PropertyValueExtractor(self.semgrex_matcher)

        # Generate property profiles
        self.property_profiles = self.property_profiler.run(self.wd_properties)

    def run(self):
        # Get wikipedia article
        wp_article = self._get_wp_article()

        # Split text into sentences to evaluate property matchers on each
        # sentence separately to prevent CoreNLP timeouts to occur
        wp_sentences = self.sentence_splitter.run(wp_article.sanitized_content)

        # Apply property patterns on text
        for property_profile in self.property_profiles:
            print('Apply patterns of property {} ({})'.format(property_profile.property_info.id, property_profile.property_info.label))
            for pattern in property_profile.patterns:
                for sentence in wp_sentences:
                    try:
                        matches = self.semgrex_matcher.run(sentence, pattern)
                        for match in matches:
                            print('Match found: {}'.format(match.text))
                    except SemgrexParseException as e:
                        print(e)

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
    app = WikipediaWikidataParser()
    app.run()
