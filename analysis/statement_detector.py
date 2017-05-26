from spacy.attrs import LEMMA
from spacy.matcher import Matcher


class StatementDetector:
    def __init__(self, spacy, properties):
        self.spacy = spacy
        self.properties = properties
        self.property_lemmas = self._lemmatize_properties()

    def run(self, wd_article):
        # Analyze and annotate text
        annotated_text = self.spacy(wd_article.sanitized_content)

        # Match properties
        for id, pid, start, end in self._match_properties(annotated_text):
            for sentence in annotated_text.sents:
                if sentence.start <= start and sentence.end >= end:
                    # Get start and end relative to sentence
                    start = start - sentence.start
                    end = end - sentence.start

                    yield StatementMatch(self.properties[pid],
                                         start, end, sentence.text)

    def _lemmatize_properties(self):
        return {id: [self._lemmatize(label) for label in prop.label_aliases]
                for id, prop in self.properties.items()}

    def _lemmatize(self, text):
        return [token.lemma_ for token in self.spacy(text)]

    def _match_properties(self, annotated_text):
        matcher = Matcher(self.spacy.vocab)
        for pid, labels in self.property_lemmas.items():
            for lemmas in labels:
                matcher.add_pattern(pid, [{LEMMA: lemma} for lemma in lemmas],
                                    label=pid)

        return matcher(annotated_text)


class StatementMatch:
    def __init__(self, wd_property, start, end, sentence):
        self._wd_property = wd_property
        self._start = start
        self._end = end
        self._sentence = sentence

    @property
    def wd_property(self):
        return self._wd_property

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def sentence(self):
        return self._sentence
