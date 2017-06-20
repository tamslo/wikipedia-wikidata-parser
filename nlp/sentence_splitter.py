class SentenceSplitter:
    def __init__(self, core_nlp):
        self._core_nlp = core_nlp

    def run(self, text):
        annotations = self._core_nlp.http_client.annotate(text, properties={
            'annotators': 'ssplit',
            'outputFormat': 'json'
        })['sentences']

        # Extract sentences by splitting the input text on end offsets of the
        # last token of each sentence in the annotations
        offsets = [0] + [sentence['tokens'][-1]['characterOffsetEnd']
                         for sentence in annotations]
        sentences = [text[offsets[i]:offsets[i+1]]
                     for i in range(len(offsets) - 1)]

        return sentences
