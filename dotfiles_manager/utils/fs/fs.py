import mimetypes
import pathlib

from dotfiles_manager.utils.exception import InvalidDotfile
from dotfiles_manager.utils.fs.base import DotfileFS
from dotfiles_manager.utils.fs.log import Log
from dotfiles_manager.utils.fs.shell import InterfaceFS
from dotfiles_manager.utils.style import style
from dotfiles_manager.utils.template import template_file


class Copy(DotfileFS):
    def validate(self, fs: InterfaceFS, flags):
        if fs.resolve(self.src) == fs.resolve(self.dest):
            raise InvalidDotfile(
                f"'{style.error(str(self.src))}' already linked", self
            )
        super().validate(fs, flags)

    def __call__(self, fs: InterfaceFS, flags):
        if fs.is_file(self.src):
            fs.mkdir(self.dest.parent)
            fs.copyfile(self.src, self.dest)
            Log.Info(f"copy file '{style.info(str(self.dest))}'")(fs, flags)
        elif fs.is_dir(self.src):
            fs.mkdir(self.dest.parent)
            fs.copydir(self.src, self.dest)
            Log.Info(f"copy directory '{style.info(str(self.dest))}'")(
                fs, flags
            )


class Symlink(DotfileFS):
    def __call__(self, fs: InterfaceFS, flags):
        if fs.exists(self.dest):
            # same follow
            if fs.resolve(self.dest) == fs.resolve(self.src):
                Log.Show(
                    f"symlink already exists'{style.info(str(self.dest))}', ignore..."
                )(fs, flags)
                return
            if flags.no:
                Log.Show(f"symlink '{style.info(str(self.dest))}' ignored...")(
                    fs, flags
                )
                return
            if not flags.yes:
                if not Log.Ask(
                    f"'file {style.info(str(self.dest))}' already exists, remove it ?"
                )(fs, flags):
                    return

        if fs.is_file(self.src):
            fs.mkdir(self.dest.parent)
            fs.symlinkfile(self.src, self.dest)
            Log.Info(f"symlink file '{style.info(str(self.dest))}'")(fs, flags)
        elif fs.is_dir(self.src):
            fs.mkdir(self.dest.parent)
            fs.symlinkdir(self.src, self.dest)
            Log.Info(f"symlink directory '{style.info(str(self.dest))}'")(
                fs, flags
            )


class Delete(DotfileFS):
    def __init__(self, src: pathlib.Path):
        super().__init__(src, src)

    def __call__(self, fs: InterfaceFS, flags):
        if fs.is_file(self.src):
            fs.removefile(self.dest)
            Log.Info(f"delete file '{style.info(str(self.dest))}'")(fs, flags)
        elif fs.is_dir(self.src):
            fs.removedir(self.dest)
            Log.Info(f"delete directory' {style.info(str(self.dest))}'")(
                fs, flags
            )


class WriteFile(DotfileFS):
    def __init__(self, src: pathlib.Path, content=""):
        super().__init__(src, src)
        self.content = content

    def __call__(self, fs: InterfaceFS, flags) -> None:
        fs.write(self.src, self.content)


class WriteFileTemplate(WriteFile):
    def is_enable(self):
        """Run template only in textfile"""
        mine = mimetypes.guess_type(self.src)
        if mine[0] in ["text/plain", None]:
            return True
        return False

    def __call__(self, fs: InterfaceFS, flags) -> None:
        if not self.is_enable():
            return

        content = fs.read(self.src)
        # no change after templating, so ignore it
        if content == self.content:
            return
        self.content = template_file(content, flags)
        super().__call__(fs, flags)


class Chown(DotfileFS):
    def __init__(self, src: pathlib.Path, user: str):
        super().__init__(src, src)
        self.user = user

    def __call__(self, fs: InterfaceFS, flags) -> None:
        fs.chown(self.src, self.user)
        Log.Debug(f"change owner' {style.info(str(self.dest))}'")(fs, flags)
