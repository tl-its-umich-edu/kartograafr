import inspect


class UtilMixin(object):
    def methodName(self, depth=1):
        return inspect.currentframe(depth).f_code.co_name


def stringContainsAllCharacters(string, characters):
    """
    Check whether 'string' contains all characters from iterable 'characters'.

    :param string: String to check for wanted characters
    :type string: str
    :param characters: String of characters to be found
    :type characters: Any iterable such as str, list, tuple, etc.
    :return: True if all characters are found, False otherwise
    :rtype: bool
    """
    assert type(string) is str
    assert iter(characters)
    return False not in [character in string for character in characters]
