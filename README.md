# wikipedia-wikidata-parser
A parser that converts text in Wikipedia to statements in Wikidata.

## Installation
Download and extract Stanford CoreNLP from  https://stanfordnlp.github.io/CoreNLP/#download.

Install dependencies `pip install -r requirements.txt` and spacy assets `python -m spacy download en`.

## Execution
Go to the Stanford CoreNLP directory and run `java -mx5g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -timeout 10000`, increase the timeout if needed.

Run `python app.py`.

## Documentation

### Algorithm (WIP)
1. Lemmatization of article and properties
2. Match lemmas, extract regarding sentence
3. Syntactically parse sentence
4. Build statements from that

### Tools
To access a Wikipedia article, we use the Wikipedia Python package with the addition that it returns the page properties, including the identifer of the related Wikidata item ([see Sören's pull request](https://github.com/goldsmith/Wikipedia/pull/147)).

To perform NLP tasks on the article, we use the [Stanford CoreNLP Toolkit](https://stanfordnlp.github.io/CoreNLP/) and [Spacy](https://spacy.io/).

### Test Data
To prove our concept, we started to parse only one Wikipedia article. We chose [Douglas Adams](https://en.wikipedia.org/wiki/Douglas_Adams) (by the way, check his identifer on Wikidata) because we assumed that an article about a person holds information which is well parsable.

We also narrowed down the number of Wikidata properties (see [wd_properties_sample](data/wd_properties_sample.json)). We picked the six properties _place of birth_, _place of death_, _date of birth_, _occupation_, _mother_, and _father_. We believe that with these properties we cover some important tasks for our tool: We have similar properties with plain values, such as _place of birth_ and _date of birth_, with _occupation_ a very general property that can have a variety of values, and with _mother_ and _father_ once again similar properties that need to be mapped to Wikidata items.

### Evaluation
To evaluate our results, we plan to match our results for a Wikipedia article with the actual statements on the related Wikidata item using Pywikibot.
