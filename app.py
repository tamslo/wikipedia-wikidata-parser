import re
import json
import spacy
from spacy.attrs import LEMMA
from spacy.matcher import Matcher
import wikipedia


class WikipediaWikidataParser:
    def __init__(self):
        self.nlp = spacy.load('en')

    def run(self):
        # Get wikipedia article
        wp_article = self._get_wp_article()
        content = re.sub(r"={2,}.*={2,}", "", wp_article.content)
        content = content.replace('\n', ' ').replace('\r', '')
        wp_doc = self.nlp(content)

        # Get properties
        wd_properties = self._get_wd_properties()

        # Tokenize property labels and aliases
        lemmatized_properties = {}
        for id, prop in wd_properties.items():
            lemmas = self.lemmatize(prop['label']) + [self.lemmatize(alias) for alias in prop['aliases']]
            lemmatized_properties[id] = lemmas

        # Match properties
        matcher = Matcher(self.nlp.vocab)
        for property_id, labels in lemmatized_properties.items():
            for lemmas in labels:
                matcher.add_pattern(property_id, [{LEMMA: lemma} for lemma in lemmas], label=property_id)
        for ent_id, label, start, end in matcher(wp_doc):
            for sentence in wp_doc.sents:
                if sentence.start <= start and sentence.end >= end:
                    print('Property P{} ({}) recognized:'.format(label, wd_properties[label]['label']))
                    print(sentence)
                    print()
                    break

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
        return [token.lemma_ for token in self.nlp(text)]

if __name__ == '__main__':
    app = WikipediaWikidataParser()
    app.run()
