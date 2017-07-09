# wikipedia-wikidata-parser
A parser that converts text in Wikipedia to statements in Wikidata using NLP techniques.

## Installation
1. Download and extract Stanford CoreNLP from https://stanfordnlp.github.io/CoreNLP/#download (Java neeeds to be installed for execution).
2. Install dependencies `pip install -r requirements.txt`.

## Execution
Run `python app.py [CORE_NLP_DIR]  [ARTICLE] [--verbose]`, where `CORE_NLP_DIR` is the installation directory of CoreNLP and the article needs to be in quotes.

When setting the flag `--verbose`, the `stdout and stderr` of the CoreNLP processor is piped to the `stdout` of the application.

## Documentation

### Algorithm
1. Generate [Semgrex patterns](https://nlp.stanford.edu/nlp/javadoc/javanlp/edu/stanford/nlp/semgraph/semgrex/SemgrexPattern.html) for each property and label/alias matching possible values for that property
2. Apply patterns on article text sentence-wise
3. Validate extracted information and reject invalid candidates
4. Build statements from valid candidates and lookup referenced Wikidata items

### Tools
To access a Wikipedia article, we use the Wikipedia Python package with the addition that it returns the page properties, including the identifer of the related Wikidata item ([see Sören's pull request](https://github.com/goldsmith/Wikipedia/pull/147)).

To perform NLP tasks, we use the [Stanford CoreNLP Toolkit](https://stanfordnlp.github.io/CoreNLP/).

### Test Data
To prove our concept, we started to parse only one Wikipedia article. We chose [Douglas Adams](https://en.wikipedia.org/wiki/Douglas_Adams) (by the way, check his identifer on Wikidata) because we assumed that an article about a person holds information which is well parsable.

We also narrowed down the number of Wikidata properties (see [wd_properties_sample](data/wd_properties_sample.json)). We picked the six properties _place of birth_, _place of death_, _date of birth_, _occupation_, _mother_, and _father_. We believe that with these properties we cover some important tasks for our tool: We have similar properties with plain values, such as _place of birth_ and _date of birth_, with _occupation_ a very general property that can have a variety of values, and with _mother_ and _father_ once again similar properties that need to be mapped to Wikidata items.

### Evaluation
To evaluate our results, we plan to match our results for a Wikipedia article with the actual statements on the related Wikidata item using Pywikibot.
