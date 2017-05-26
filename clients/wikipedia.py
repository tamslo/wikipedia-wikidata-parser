import re
import wikipedia


class WikipediaClient:
    def get_article(self, title):
        # Get wikipedia page from API
        page = wikipedia.page(title)

        # Sanitize content
        sanitized_content = re \
            .sub(r'={2,}.*={2,}', '', page.content) \
            .replace('\n', ' ') \
            .replace('\r', ' ') \
            .replace('  ', ' ')

        # Get referenced wikidata item
        wd_item = page.pageprops['wikibase_item']

        return WikipediaArticle(page.content, sanitized_content, wd_item)


class WikipediaArticle:
    def __init__(self, content, sanitized_content, wd_item):
        self._content = content
        self._sanitized_content = sanitized_content
        self._wd_item = wd_item

    @property
    def content(self):
        return self._content

    @property
    def sanitized_content(self):
        return self._sanitized_content

    @property
    def wd_item(self):
        return self._wd_item
