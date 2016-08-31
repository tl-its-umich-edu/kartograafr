import inspect
import sys
from cStringIO import StringIO


class UtilMixin(object):
    def methodName(self, depth=1):
        return inspect.currentframe(depth).f_code.co_name


class CaptureStdoutLines(list):
    """
    A context manager for capturing the lines sent to stdout as elements
    of a list.  Useful for capturing important output printed by
    poorly-designed API methods.

    Example::
        with CaptureStdoutLines() as output:
            print('Norwegian blue parrot')
        assert output == ['Norwegian blue parrot']

        with CaptureStdoutLines(output) as output:
            print('Venezuelan beaver cheese')
        assert output == ['Norwegian blue parrot', 'Venezuelan beaver cheese']
    """

    def __enter__(self):
        self._originalStdout = sys.stdout
        sys.stdout = self._stdoutStream = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stdoutStream.getvalue().splitlines())
        self.notEmpty = len(self) != 0
        sys.stdout = self._originalStdout


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
