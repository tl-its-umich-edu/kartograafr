from argparse import Namespace


class CanvasObject(Namespace):
    def __getattribute__(self, name):
        """
        Unlike the default implementation, this method
        returns ``None`` rather than raise an ``AttributeError``
        exception if an attribute doesn't exist.
        :param name: Name of the attribute to retrieve
        :type name: str
        :return: Value of the named attribute or None
        :rtype: mixed
        """
        attrValue = None
        try:
            attrValue = object.__getattribute__(self, name)
        except AttributeError:
            pass
        return attrValue
