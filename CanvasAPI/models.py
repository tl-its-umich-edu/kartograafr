from argparse import Namespace

class CanvasObject(Namespace):
    def __getattribute__(self, name):
        """
        Unlike the default implementation, this method returns ``None``
        rather than raise an ``AttributeError`` exception if an attribute
        doesn't exist.
        """
        attrValue = None
        try:
            attrValue = object.__getattribute__(self, name)
        except AttributeError:
            pass
        return attrValue
