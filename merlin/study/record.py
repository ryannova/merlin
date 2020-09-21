class Record:
    """A container class for holding general information."""

    def __init__(self):
        """Initialize an empty Record."""
        self._info = {}

    def get(self, key, default=None):
        """
        Get information by key in a record.

        :param key: The key to look up in a Record's stored information.
        :param default: The default value to return if the key is not found
        (Default: None).
        :returns: The information labeled by parameter key. Default if key does
        not exist.
        """
        return self._info.get(key, default)
