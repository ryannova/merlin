from collections import OrderedDict
import logging
import re

LOG = logging.getLogger(__name__)


class Combination(object):
    def __init__(self, token="$"):
        self._params = {}
        self._labels = OrderedDict()
        self._names = {}
        self._token = token

    def add(self, key, name, value, label):
        var = "{}({})".format(self._token, key)
        self._params[var] = value
        var = "{}({}.label)".format(self._token, key)
        self._labels[var] = label
        var = "{}({}.name)".format(self._token, key)
        self._names[var] = name

    def __str__(self):
        return ".".join(self._labels.values())

    def get_param_string(self, params):
        combo_str = []
        for item in sorted(params):
            var = "{}({}.label)".format(self._token, item)
            combo_str.append(self._labels[var])

        return ".".join(combo_str)

    def apply(self, item):
        for key, value in self._labels.items():
            item = item.replace(key, str(value))

        for key, value in self._params.items():
            item = item.replace(key, str(value))

        for key, name in self._names.items():
            item = item.replace(key, str(name))

        return item


class ParameterGenerator:
    def __init__(self, token="$", ltoken="%%"):
        self.parameters = OrderedDict()
        self.labels = {}
        self.names = {}
        self.label_token = ltoken
        self.token = token

        self.length = 0

    def add_parameter(self, key, values, label=None, name=None):
        if key in self.parameters:
            LOG.warning("'%s' already in parameter set. Overriding.", key)

        self.parameters[key] = values
        if self.length == 0:
            self.length = len(values)

        elif len(values) != self.length:
            error = "Length of values list must be the same size as " \
                    "the other parameters that exist in the " \
                    "generators. Length of '{}' is {}. Aborting." \
                    .format(name, len(values))
            LOG.exception(error)
            raise ValueError(error)

        if label:
            self.labels[key] = label
        else:
            self.labels[key] = "{}.{}".format(key, self.label_token)

        if name:
            self.names[key] = name
        else:
            self.names[key] = key

    def __iter__(self):
        return self.get_combinations()

    def __bool__(self):
        return bool(self.parameters)

    __nonzero__ = __bool__

    def get_combinations(self):
        for i in range(0, self.length):
            combo = Combination()
            for key in self.parameters.keys():
                pvalue = self.parameters[key][i]
                if isinstance(self.labels[key], list):
                    tlabel = self.labels[key][i]
                else:
                    tlabel = self.labels[key].replace(self.label_token,
                                                      str(pvalue))
                name = self.names[key]
                combo.add(key, name, pvalue, tlabel)
            yield combo

    def _get_used_parameters(self, item, params):
        if not item:
            return
        elif isinstance(item, int):
            return
        elif isinstance(item, str):
            for key in self.parameters.keys():
                _ = r"\{}\({}\.*\w*\)".format(self.token, key)
                matches = re.findall(_, item)
                if matches:
                    params.add(key)
        elif isinstance(item, list):
            for each in item:
                self._get_used_parameters(each, params)
        elif isinstance(item, dict):
            for each in item.values():
                self._get_used_parameters(each, params)
        else:
            msg = "Encountered an object of type '{}'. Expected a str, list," \
                  " int, or dict.".format(type(item))
            LOG.error(msg)
            raise ValueError(msg)

    def get_used_parameters(self, step):
        params = set()
        self._get_used_parameters(step.__dict__, params)
        return params

    def get_metadata(self):
        meta = {}
        for combo in self.get_combinations():
            meta[str(combo)] = {}
            meta[str(combo)]["params"] = combo._params
            meta[str(combo)]["labels"] = combo._labels

        return meta
