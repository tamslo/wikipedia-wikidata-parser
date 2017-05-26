import json


class WikidataClient:
    def __init__(self, properties_file):
        self.properties_file = properties_file

    def get_properties(self):
        property_objects = json.load(open(self.properties_file))
        return [WikidataProperty.from_json(obj) for obj in property_objects]

    def get_properties_dict(self, numeric_id=False):
        if numeric_id:
            return {prop.numeric_id: prop for prop in self.get_properties()}
        else:
            return {prop.id: prop for prop in self.get_properties()}


class WikidataProperty:
    def __init__(self, id, label, aliases, data_type):
        self._id = id
        self._label = label
        self._aliases = aliases
        self._data_type = data_type

    @property
    def id(self):
        return self._id

    @property
    def numeric_id(self):
        return int(self.id[1:])

    @property
    def label(self):
        return self._label

    @property
    def aliases(self):
        return self._aliases

    @property
    def label_aliases(self):
        return [self.label] + self.aliases

    @property
    def data_type(self):
        return self._data_type

    @staticmethod
    def from_json(obj):
        return WikidataProperty(obj['id'],
                                obj['label'],
                                obj['aliases'],
                                obj['datatype'])