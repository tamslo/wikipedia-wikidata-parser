import re
import json
import spacy
from spacy.attrs import LEMMA
from spacy.matcher import Matcher
from pycorenlp import StanfordCoreNLP
import wikipedia

class WikipediaWikidataParser:
    def __init__(self, core_nlp_host='localhost', core_nlp_port=9000):
        self.spacy = spacy.load('en')
        self.stanford = StanfordCoreNLP('http://{}:{}'.format(core_nlp_host, core_nlp_port))

    def run(self):
        # Get Wikipedia article
        wp_article = self._get_wp_article()
        # Format Wikipedia article (ignore headings and remove resulting newlines)
        wp_article = re.sub(r"={2,}.*={2,}", "", wp_article.content)
        wp_article = wp_article.replace('\n', ' ').replace('\r', '')
        annotated_article = self.spacy(wp_article)

        # Get Wikidata properties
        wd_properties = self._get_wd_properties()

        # Tokenize property labels and aliases
        lemmatized_properties = {}
        for id, prop in wd_properties.items():
            lemmas = [self.lemmatize(prop['label'])]\
                + [self.lemmatize(alias) for alias in prop['aliases']]
            lemmatized_properties[id] = lemmas

        # Match properties
        matcher = Matcher(self.spacy.vocab)
        for property_id, labels in lemmatized_properties.items():
            for lemmas in labels:
                matcher.add_pattern(property_id, [{LEMMA: lemma} for lemma in lemmas], label=property_id)
        for ent_id, property_id, start, end in matcher(annotated_article):
            for sentence in annotated_article.sents:
                if sentence.start <= start and sentence.end >= end:
                    print('Property P{} ({}) recognized:'.format(property_id, wd_properties[property_id]['label']))
                    print(sentence)
                    print()
                    start = start - sentence.start
                    end = end - sentence.start
                    self.extract_statements(sentence, property_id, start, end, wd_properties)
                    return

    @staticmethod
    def _get_wp_article():
        while True:
            # TODO title = input('Wikipedia Article? ')
            title = 'Douglas Adams'
            try:
                return wikipedia.page(title)
            except wikipedia.DisambiguationError as e:
                print('{} may refer to:'.format(title))
                for option in e.options:
                    print(option)

    @staticmethod
    def _get_wd_properties():
        wd_properties = json.load(open('data/wd_properties_sample.json'))
        return {int(prop['id'][1:]): prop for prop in wd_properties}

    def lemmatize(self, text):
        return [token.lemma_ for token in self.spacy(text)]

    def extract_statements(self, sentence, property_id, start, end, wd_properties):
        annotated_sentence = self.stanford.annotate(sentence.text, properties={
            'annotators': 'pos,depparse,ner',
            'outputFormat': 'json'
        })
        # Debugging
        log = open('debug_log.json', 'w')
        log.write(json.dumps(annotated_sentence))
        for index in range(start, end):
            # just because
            stanfordIndex = index + 1
            basicDependencies = annotated_sentence['sentences'][0]['basicDependencies']
            matchingDependencies = [dependency for dependency in basicDependencies if dependency['governor'] == stanfordIndex or dependency['dependent'] == stanfordIndex]
            print(sentence[index])
            print(matchingDependencies)


# Debugging
# log = open('debug_log.json', 'w')
# log.write(json.dumps(lemmatized_properties))

if __name__ == '__main__':
    app = WikipediaWikidataParser()
    app.run()
