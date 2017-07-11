import json
import requests
import itertools
from ngram import NGram
from urllib.parse import urlencode
from utils.helpers import flatten


class WikidataEntityLookup:
    API_URL = 'https://www.wikidata.org/w/api.php'
    CHARACTERISTIC_PROPERTIES = {
        'PERSON': {
            'P21',    # sex or gender
            'P26',    # spouse
            'P27',    # country of citizenship
            'P40',    # child
            'P569',   # date of birth
            'P570',   # date of death
            'P753',   # given name
            'P1477'   # birth name
        },
        'LOCATION': {
            'P625',   # coordinate location
            'P3134',  # TripAdvisor ID
            'P3749'   # Google Maps CID
        },
        'ORGANIZATION': {
            'P112',   # founded by
            'P127',   # owned by
            'P159',   # headquarters location
            'P169',   # chief executive officer
            'P452',   # industry
            'P749',   # parent organization
            'P1037',  # manager/director
            'P1128',  # employees
            'P1320',  # OpenCorporates ID
            'P1454'   # legal form'
        }
    }

    def get(self, title, ner_tag):
        if ner_tag not in self.CHARACTERISTIC_PROPERTIES.keys():
            raise ValueError('NER tag is not supported for entity lookup.')

        # Get candidate items
        candidate_ids = flatten([self._search_items(x)
                                 for x in self._extend_title(title)], True)
        candidates = self._get_items(candidate_ids)

        # Remove items from candidates, which do not have any of the
        # characteristic properties regarding their NER tag
        present_properties = {item['id']: item['claims'].keys()
                              for item in candidates}
        characteristic_properties = self.CHARACTERISTIC_PROPERTIES[ner_tag]
        candidates = [item for item in candidates
                      if characteristic_properties.intersection(present_properties[item['id']])]

        # Return candidate with the maximal similarity of its label and the
        # provided title
        if candidates:
            return max(candidates, key=lambda item: NGram.compare(title, item['labels']['en']['value'], N=2))

    def _request(self, **kwargs):
        url = '{}?{}'.format(self.API_URL, urlencode(kwargs))
        return requests.get(url)

    @staticmethod
    def _extend_title(title):
        words = title.split(' ')
        title_combinations = flatten([itertools.permutations(words, i+1)
                                      for i in reversed(range(len(words)))])
        return [' '.join(combination) for combination in title_combinations]

    def _search_items(self, title):
        response = self._request(action='wbsearchentities',
                                 language='en',
                                 type='item',
                                 search=title,
                                 format='json')
        if response.status_code != 200:
            raise Exception('Could not query Wikidata entities.')

        result = json.loads(response.text)
        if 'search' in result:
            return [entity['title'] for entity in result['search']
                    if 'description' not in entity or entity['description'] != 'Wikipedia disambiguation page']

        return []

    def _get_items(self, ids):
        response = self._request(action='wbgetentities',
                                 languages='en',
                                 ids='|'.join(ids),
                                 props='labels|claims',
                                 format='json')
        if response.status_code != 200:
            raise Exception('Could not retrieve Wikidata items.')

        result = json.loads(response.text)
        if 'entities' in result:
            return sorted(result['entities'].values(), key=lambda x: ids.index(x['id']))

        return []

