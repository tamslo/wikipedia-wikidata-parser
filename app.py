import json
import spacy
import wikipedia
from pycorenlp import StanfordCoreNLP

from clients.wikipedia import WikipediaClient
from clients.wikidata import WikidataClient
from analysis.statement_detector import StatementDetector


class WikipediaWikidataParser:
    def __init__(self, core_nlp_host='localhost', core_nlp_port=9000):
        # Initialize NLP libraries
        self.spacy = spacy.load('en')
        self.core_nlp = StanfordCoreNLP('http://{}:{}'.format(core_nlp_host,
                                                              core_nlp_port))

        # Initialize API clients
        self.wp_client = WikipediaClient()
        self.wd_client = WikidataClient('data/wd_properties_sample.json')

        # Load static resources
        self.wd_properties = self.wd_client.get_properties_dict(numeric_id=True)

        # Initialize services
        self.statement_detector = StatementDetector(self.spacy,
                                                    self.wd_properties)

    def run(self):
        # Get wikipedia article
        wp_article = self._get_wp_article()

        # Find statements for properties in wikipedia article
        for statement_match in self.statement_detector.run(wp_article):
            print('Property P{} ({}) recognized:'.format(statement_match.wd_property.id,
                                                         statement_match.wd_property.label))
            print(statement_match.sentence)
            self.extract_statements(statement_match)
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

    def extract_statements(self, statement_match):
        annotated_sentence = self.core_nlp.annotate(statement_match.sentence, properties={
            'annotators': 'pos,depparse,ner',
            'outputFormat': 'json'
        })
        # Debugging
        log = open('debug_log.json', 'w')
        log.write(json.dumps(annotated_sentence))
        for index in range(statement_match.start, statement_match.end):
            tokens = annotated_sentence['sentences'][0]['tokens']
            basic_dependencies = annotated_sentence['sentences'][0]['basicDependencies']
            matching_dependencies = [dependency for dependency in basic_dependencies
                                    if dependency['governor'] == index + 1 or
                                    dependency['dependent'] == index +1]
            print(tokens[index]['word'])
            print(matching_dependencies)


# Debugging
# log = open('debug_log.json', 'w')
# log.write(json.dumps(lemmatized_properties))

if __name__ == '__main__':
    app = WikipediaWikidataParser()
    app.run()
