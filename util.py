# Converted to Python 3.
# Make UtilMixin a no-op.
# remove CaptureStdoutLines

import datetime
import logging

logger = logging.getLogger(__name__)


# Method names are now hard-coded so this is a no-op.
class UtilMixin(object):
    def methodName(self):
        logger.debug("call methodName")


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


def formatNameAndID(objectA):
     return '"{}" ({})'.format(objectA.title, objectA.id)


def elideString(string):
    """
    Return version of string with the middle removed.  This allows identifying
    information strings without revealing the whole string.
    """

    chunkSize = 3

    # use fake value if string is too short to be safe
    if len(string) < 9:
        return "***"
    
    # keep the first and last chunks
    string = string[0:chunkSize]+"..."+string[-chunkSize:]

    return string


def splitListIntoSublists(origList, sublistLength=10):
    sublists = [origList[x:x + sublistLength] for x in range(0, len(origList), sublistLength)]
    return sublists


class Iso8601UTCTimeFormatter(logging.Formatter):
    """
    A logging Formatter class giving timestamps in a more common ISO 8601 format.

    The default logging.Formatter class **claims** to give timestamps in ISO 8601 format
    if it is not initialized with a different timestamp format string.  However, its
    format, "YYYY-MM-DD hh:mm:ss,sss", is much less common than, "YYYY-MM-DDThh:mm:ss.sss".
    That is, the separator between date and time is a space instead of the letter "T"
    and the separator for fractional seconds is a comma instead of a period (full stop).
    While these differences may not be strictly *wrong*, it makes the formatted timestamp
    *unusual*.

    This formatter class removes some of the differences by using Python's own
    datetime.datetime.isoformat() method.  That method uses "T" as the default separator
    between date and time.  And it always uses a period (full stop) for fractional
    seconds, even if a comma is normally used for fractional numbers in the current
    locale.

    This class also assumes the timestamp should use the UTC timezone.
    """

    def __init__(self, logFormat=None, timeFormat=None):
        """
        The purpose of this constructor is to set the timezone to UTC for later use.

        :param logFormat: Log record formatting string.
        :type logFormat: str
        :param timeFormat: Time formatting string. You probably **DO NOT** want one.
        :type timeFormat: str
        """
        super(Iso8601UTCTimeFormatter, self).__init__(logFormat, timeFormat)

        from dateutil.tz import tzutc
        self._TIMEZONE_UTC = tzutc()

    def formatTime(self, record, timeFormat=None):
        """
        In the event that a timeFormat string is given, this method will use the
        formatTime() method of the superclass (logging.Formatter) instead.  That's
        because this method doesn't need timeFormat. So, other than this solution,
        the options for handling that argument were to ignore it or raise an exception,
        either of which probably violate the principle of least astonishment (POLA).

        :param record: Record of the current log entry
        :type record: logging.LogRecord
        :param timeFormat: Time formatting string. You probably **DO NOT** want one.
        :type timeFormat: str
        :return: Log record's timestamp in ISO 8601 format
        :rtype: str or unicode
        """
        if timeFormat is not None:
            return super(Iso8601UTCTimeFormatter, self).formatTime(record, timeFormat)

        return datetime.datetime.fromtimestamp(record.created, self._TIMEZONE_UTC).isoformat()


class LoggingContext(object):
    """
    A context manager to temporarily change the log level or add a handler
    to logging statements for a block of code.

    Example::
        # Assuming logger doesn't log to console, add a handler to log to console
        with LoggingContext(logger, handler=logging.StreamHandler()):
            logger.info('Logged to console')

        logger.info('No longer logging to console')

        # Assuming logger works at INFO level or lower, change the level to log only ERROR or higher
        with LoggingContext(logger, level=logging.ERROR):
            logger.info('Not logged because INFO < ERROR')

        logger.info('Logged because INFO is allowed again')
    """

    def __init__(self, logger, level=None, handler=None, close=False):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.oldLevel = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)

    def __exit__(self, exceptionType, exceptionValue, traceback):
        if self.level is not None:
            self.logger.setLevel(self.oldLevel)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()
