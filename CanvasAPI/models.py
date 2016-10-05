from argparse import Namespace


class CanvasObject(Namespace):
    def __getattribute__(self, name):
        """
        Unlike the default implementation, this method returns
        ``None`` rather than raise an ``AttributeError`` exception
        if an attribute doesn't exist.

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

    def __str__(self):
        """
        Some Canvas objects have their name-like value in their
        "name" attribute, others have it in their "title" attribute.
        This method attempts to pick which of those attributes is
        better, giving preference to "title".

        :return: A string representation of this Canvas object, of the form: "Title/Name" (ID)
        :rtype: str
        """
        return '"{}" ({})'.format(self.title or self.name, self.id)
