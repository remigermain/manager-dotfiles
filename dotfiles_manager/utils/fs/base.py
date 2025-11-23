import abc

from dotfiles_manager.utils.exception import InvalidDotfile, PermissionDotfile
from dotfiles_manager.utils.fs.shell import InterfaceFS
from dotfiles_manager.utils.style import style


class DotfileInterface(abc.ABC):
    @abc.abstractmethod
    def validate(self, fs: InterfaceFS, flags):
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(self, fs: InterfaceFS, flags):
        raise NotImplementedError


class DotfileFS(DotfileInterface):
    def __init__(self, src, dest):
        self.src = src
        self.dest = dest

    def validate(self, fs: InterfaceFS, flags):
        if fs.exists(self.src):
            if not any((fs.is_file(self.src), fs.is_dir(self.src))):
                raise InvalidDotfile(
                    f"invalid type of file '{style.error(str(self.src))}'", self
                )
            if not fs.can_read(self.src):
                raise PermissionDotfile(
                    f"Read Permission denied: '{style.error(str(self.src))}'", self
                )
        if fs.exists(self.dest) and not fs.can_write(self.dest):
            raise PermissionDotfile(
                f"Write Permission denied: '{style.error(str(self.dest))}'", self
            )


class DotfileExtra(DotfileInterface):
    def __init__(self, *next: DotfileFS):
        self.next = next

    def validate(self, fs: InterfaceFS, flags):
        for next in self.next:
            next.validate(fs, flags)

    def __call__(self, fs: InterfaceFS, flags):
        for next in self.next:
            next(fs, flags)
