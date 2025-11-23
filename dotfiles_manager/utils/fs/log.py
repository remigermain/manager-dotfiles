import logging
import sys

from dotfiles_manager.utils.fs.base import DotfileExtra, DotfileFS
from dotfiles_manager.utils.fs.shell import InterfaceFS


class Message(DotfileExtra):
    def __init__(self, msg, *next: list[DotfileFS], logg_level=logging.INFO):
        super().__init__(*next)
        self.msg = msg
        self.logg_level = logg_level

    def __call__(self, fs: InterfaceFS, flags):
        file = (
            sys.stderr
            if self.logg_level is not None and self.logg_level >= logging.ERROR
            else sys.stdout
        )
        print(self.msg, file=file)
        return super().__call__(fs, flags)


class Ask(Message):
    def __call__(self, fs: InterfaceFS, flags) -> bool:
        choices_yes = ["y", "yes"]
        choices_no = ["n", "no"]
        choices_join = ", ".join(choices_yes + choices_no)
        while True:
            result = input(f"{self.msg} [{choices_join}]\n").strip().lower()
            if result in choices_yes:
                return True
            elif result in choices_no:
                return False
            print(f"invalid choices '{result}'", file=sys.stderr)


class Log:
    @classmethod
    def Error(cls, msg: str, *next: list[DotfileFS]):
        return Message(msg, *next, logg_level=logging.ERROR)

    @classmethod
    def Warning(cls, msg: str, *next: list[DotfileFS]):
        return Message(msg, *next, logg_level=logging.WARNING)

    @classmethod
    def Info(cls, msg: str, *next: list[DotfileFS]):
        return Message(msg, *next, logg_level=logging.INFO)

    @classmethod
    def Debug(cls, msg: str, *next: list[DotfileFS]):
        return Message(msg, *next, logg_level=logging.DEBUG)

    @classmethod
    def Show(cls, msg: str, *next: list[DotfileFS]):
        return Message(msg, *next, logg_level=None)

    @classmethod
    def Ask(cls, msg: str, *next: list[DotfileFS]):
        return Ask(msg, *next, logg_level=logging.DEBUG)
