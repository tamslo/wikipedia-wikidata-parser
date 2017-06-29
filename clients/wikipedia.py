import re
import wikipedia
from unidecode import unidecode


class WikipediaClient:
    def get_article(self, title):
        # Get wikipedia page from API
        page = wikipedia.page(title)

        # Sanitize content: Remove headline formattings, newlines,
        # double-spaces, transliteration to ASCII
        sanitized_content = re \
            .sub(r'={2,}.*={2,}', '', page.content) \
            .replace('\n', ' ') \
            .replace('\r', ' ') \
            .replace('  ', ' ')
        sanitized_content = unidecode(sanitized_content)

        # Get referenced wikidata item
        wd_item = page.pageprops['wikibase_item']

        return WikipediaArticle(page.title, page.content,
                                sanitized_content, wd_item)


class WikipediaArticle:
    def __init__(self, title, content, sanitized_content, wd_item):
        self._title = title
        self._content = content
        self._sanitized_content = sanitized_content
        self._wd_item = wd_item

    @property
    def title(self):
        return self._title

    @property
    def content(self):
        return self._content

    @property
    def sanitized_content(self):
        return self._sanitized_content

    @property
    def wd_item(self):
        return self._wd_item
