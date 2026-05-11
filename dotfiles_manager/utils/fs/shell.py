import abc
import io
import pathlib
import subprocess
import tempfile

from dotfiles_manager.utils.logger import logger


class InterfaceFS(abc.ABC):
    def __init__(self, sudo=False):
        self.sudo = sudo

    @abc.abstractmethod
    def mkdir(self, path: pathlib.Path): ...

    @abc.abstractmethod
    def copyfile(self, src: pathlib.Path, dest: pathlib.Path): ...

    @abc.abstractmethod
    def copydir(self, src: pathlib.Path, dest: pathlib.Path): ...

    @abc.abstractmethod
    def symlinkfile(self, src: pathlib.Path, dest: pathlib.Path): ...

    @abc.abstractmethod
    def symlinkdir(self, src: pathlib.Path, dest: pathlib.Path): ...

    @abc.abstractmethod
    def removefile(self, path: pathlib.Path): ...

    @abc.abstractmethod
    def removedir(self, path: pathlib.Path): ...

    @abc.abstractmethod
    def write(self, path: pathlib.Path, content: str | bytes): ...

    @abc.abstractmethod
    def read(self, path: pathlib.Path): ...

    @abc.abstractmethod
    def is_dir(self, path: pathlib.Path) -> bool: ...

    @abc.abstractmethod
    def is_file(self, path: pathlib.Path) -> bool: ...

    @abc.abstractmethod
    def exists(self, path: pathlib.Path) -> bool: ...

    @abc.abstractmethod
    def can_read(self, path: pathlib.Path) -> bool: ...

    @abc.abstractmethod
    def can_write(self, path: pathlib.Path) -> bool: ...

    @abc.abstractmethod
    def resolve(self, path: pathlib.Path) -> pathlib.Path: ...

    @abc.abstractmethod
    def chown(self, path: pathlib.Path): ...

    @abc.abstractmethod
    def chmod(self, path: pathlib.Path, mode: str): ...


class Shell(InterfaceFS):
    def run(self, cmds, check=True, *ar, **kw):
        kw.setdefault("stdout", subprocess.PIPE)
        kw.setdefault("stderr", subprocess.PIPE)
        cmds = list(cmds)
        if self.sudo:
            cmds.insert(0, "sudo")

        logger.info("Shell Command: %s", cmds)
        result = subprocess.run(cmds, **kw)
        logger.info("Shell Command Result: %s", result.returncode)
        if check:
            result.check_returncode()
        return result

    def mkdir(self, path: pathlib.Path):
        self.run(["mkdir", "-p", str(path)])

    def copyfile(self, src: pathlib.Path, dest: pathlib.Path):
        self.run(["cp", str(src), str(dest)])

    def copydir(self, src: pathlib.Path, dest: pathlib.Path):
        self.run(["cp", "-r", str(src), str(dest)])

    def symlinkfile(self, src: pathlib.Path, dest: pathlib.Path):
        self.run(["ln", "-f", "-s", str(src), str(dest)])

    def symlinkdir(self, src: pathlib.Path, dest: pathlib.Path):
        self.symlinkfile(src, dest)

    def removefile(self, path: pathlib.Path):
        self.run(["rm", "-f", str(path)])

    def removedir(self, path: pathlib.Path):
        self.run(["rm", "-rf", str(path)])

    def write(
        self,
        path: pathlib.Path,
        content: str | bytes | io.StringIO | io.BytesIO,
    ):
        if not isinstance(content, (io.StringIO | io.BytesIO)):
            if isinstance(content, str):
                stdin = io.StringIO()
            else:
                stdin = io.BytesIO()
            stdin.write(content)
            stdin.seek(0)
        else:
            stdin = content

        # create a temporyfile to copy to its final dest
        with tempfile.NamedTemporaryFile() as f:
            f.write(stdin.read().encode())
            f.seek(0)
            self.copyfile(f.name, str(path))

    def read(self, path: pathlib.Path) -> str:
        result = self.run(["cat", str(path)])
        return result.stdout.decode()

    def is_dir(self, path: pathlib.Path) -> bool:
        result = self.run(["test", "-d", str(path)], check=False)
        return result.returncode == 0

    def is_file(self, path: pathlib.Path) -> bool:
        result = self.run(["test", "-f", str(path)], check=False)
        return result.returncode == 0

    def is_symlink(self, path: pathlib.Path) -> bool:
        result = self.run(["test", "-L", str(path)], check=False)
        return result.returncode == 0

    def exists(self, path: pathlib.Path) -> bool:
        if self.run(["test", "-e", str(path)], check=False).returncode != 0:
            return False
        return self.is_file(path) or self.is_dir(path)

    def can_read(self, path: pathlib.Path) -> bool:
        if not self.exists(path):
            return False
        result = self.run(["test", "-r", str(path)], check=False)
        return result.returncode == 0

    def can_write(self, path: pathlib.Path) -> bool:
        if not self.exists(path):
            return False
        result = self.run(["test", "-w", str(path)], check=False)
        return result.returncode == 0

    def resolve(self, path: pathlib.Path) -> bool:
        if self.is_symlink(path):
            result = self.run(["readlink", str(path)], text=True)
            return pathlib.Path(result.stdout.strip())
        return path

    def chown(self, path: pathlib.Path, user: str):
        self.run(["chown", user, "-R", str(path)])

    def chmod(self, path: pathlib.Path, mode: str):
        self.run(["chmod", mode, str(path)])
