class DotfileError(Exception):
    """BaseException dotfile"""

    def __init__(self, msg: str, parent=None):
        super().__init__(msg)
        self.parent = parent


class PermissionDotfile(DotfileError):
    """Permission error if file/dir need root"""


class InvalidDotfile(DotfileError):
    """When dotfile file/dir dosent required spec"""
