"""
Sloth exception classes.
"""


class ImproperlyConfigured(Exception):
    """There is an error in the configuration."""
    pass


class NotImplementedException(Exception):
    """This function/method/class has not been implemented yet."""
    pass


class InvalidArgumentException(Exception):
    """The argument is invalid."""
    pass
