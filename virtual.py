import sys
from enum import Enum


class MemoryAddress:
    @staticmethod
    def is_valid(candidate: str):
        return type(candidate) == str and len(candidate) > 2 and candidate[0] == '{' and candidate[-1] == '}'


class Action:
    class Type(Enum):
        IDLE = 0x0
        PUSH = 0x1
        POP = 0x2
        INC = 0x3
        ADD = 0x4
        SUB = 0x5
        STORE = 0x6
        LOAD = 0x7
        FREE = 0x8
        PRINT = 0x9

    SET = set([a.name for a in Type])

    @staticmethod
    def from_str(candidate):
        if not Action.SET.__contains__(candidate):
            raise ValueError("Invalid command action")

        return Action.Type[candidate]


class Register:
    class Type(Enum):
        RESULT = "%res"
        RXX = "%rxx"

    MAP = dict([(r.value, r.name) for r in Type])

    @staticmethod
    def immutable(reg):
        return reg == Register.Type.RESULT

    @staticmethod
    def potential(candidate: str):
        return candidate[0:2] == "%r"

    @staticmethod
    def from_str(candidate):
        if not Register.MAP.__contains__(candidate):
            raise ValueError("Invalid register type")

        return Register.Type[Register.MAP[candidate]]


class Argument:
    def __init__(self, values: list[int | str]):
        self.values = []
        self.memory_addr = None
        self.register = None
        self.count = 0
        for v in values:
            if v[0] == "{" and v[-1] == '}':
                self.memory_addr = v
            elif v[0] == "%":
                self.register = Register.from_str(v)
            else:
                self.values.append(v)
            self.count += 1


class CommandChecker:
    @staticmethod
    def check_and_parse(action, args: list):
        if action == Action.Type.IDLE:
            return CommandChecker.Idle.check_and_parse(args)
        elif action == Action.Type.PUSH:
            return CommandChecker.Push.check_and_parse(args)
        elif action == Action.Type.POP:
            return CommandChecker.Pop.check_and_parse(args)
        elif action == Action.Type.INC:
            return CommandChecker.Inc.check_and_parse(args)
        elif action == Action.Type.ADD:
            return CommandChecker.Add.check_and_parse(args)
        elif action == Action.Type.SUB:
            return CommandChecker.Sub.check_and_parse(args)
        elif action == Action.Type.STORE:
            return CommandChecker.Store.check_and_parse(args)
        elif action == Action.Type.LOAD:
            return CommandChecker.Load.check_and_parse(args)
        elif action == Action.Type.FREE:
            return CommandChecker.Free.check_and_parse(args)
        elif action == Action.Type.PRINT:
            return CommandChecker.Print.check_and_parse(args)

    class Idle:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 0:
                raise ValueError(f"IDLE command must not have arguments: {args}")

    class Push:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 1:
                raise ValueError(f"Invalid PUSH arguments: {args}")

            if MemoryAddress.is_valid(args[0]):
                pass
            elif Register.potential(args[0]):
                args[0] = Register.from_str(args[0])
            else:
                args[0] = int(args[0])

    class Pop:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) == 1 and not MemoryAddress.is_valid(args[0]):
                raise ValueError(f"Invalid POP argument. Must be a memory address: {args}")
            if len(args) != 0:
                raise ValueError(f"Invalid POP arguments: {args}")

    class Inc:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 1:
                raise ValueError(f"Invalid INC argument. Must be a memory address or a register: {args}")
            if MemoryAddress.is_valid(args[0]):
                return
            if not Register.potential(args[0]):
                raise ValueError(f"Invalid INC argument. Must be a memory address or a register: {args}")

            reg = Register.from_str(args[0])
            if Register.immutable(reg):
                raise ValueError(f"Invalid INC argument. Register must not be readonly: {args}")
            args[0] = reg

    class Add:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 2:
                raise ValueError(f"Invalid ADD arguments. Must be 2: {args}")
            for i, arg in enumerate(args):
                if Register.potential(arg):
                    args[i] = Register.from_str(arg)
                elif MemoryAddress.is_valid(arg):
                    pass
                else:
                    args[i] = int(arg)

    class Sub:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 2:
                raise ValueError(f"Invalid SUB arguments. Must be 2: {args}")
            for i, arg in enumerate(args):
                if Register.potential(arg):
                    args[i] = Register.from_str(arg)
                elif MemoryAddress.is_valid(arg):
                    pass
                else:
                    args[i] = int(arg)

    class Store:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) == 0:
                raise ValueError(f"Invalid STORE arguments. Memory address is expected")

            if len(args) == 1:
                if not MemoryAddress.is_valid(args[0]):
                    raise ValueError(f"Invalid STORE arguments. Must be a memory address: {args}")
            elif len(args) == 2:
                if not Register.potential(args[0]):
                    raise ValueError(f"Invalid STORE arguments. Invalid register: {args}")
                args[0] = Register.from_str(args[0])
            else:
                raise ValueError(f"Invalid STORE arguments: {args}")

    class Load:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 1 or not MemoryAddress.is_valid(args[0]):
                raise ValueError(f"Invalid LOAD arguments. Must be a memory address: {args}")

    class Free:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) == 0 or (len(args) == 1 and not MemoryAddress.is_valid(args[0])):
                raise ValueError(f"Invalid LOAD arguments. Must be a memory address or empty: {args}")

    class Print:
        @staticmethod
        def check_and_parse(args: list):
            if len(args) != 1:
                raise ValueError(f"Invalid PRINT arguments. Must be 1: {args}")
            if Register.potential(args[0]):
                args[0] = Register.from_str(args[0])



class Command:
    def __init__(self, line: str):
        try:
            parts = line.split(" ")
            self.args = parts[1:]
            self.action = Action.from_str(parts[0])

            CommandChecker.check_and_parse(self.action, self.args)

        except Exception:
            raise ValueError(f"Invalid command: '{line}'")

    def action(self):
        return self.action

    def __str__(self):
        return f"{self.action} {self.args}"

class CommandStorage:
    def __init__(self, filename: str):
        self._file = open(filename, "r")
        self._commands = []

    def next_command(self):
        for line in self._file:
            yield CommandStorage.parse_command(line.strip())

    @staticmethod
    def parse_command(line: str):
        try:
            return Command(line)
        except ValueError as e:
            print(e, file=sys.stderr)
            exit(-1)

    def close(self):
        self._file.close()


class VirtualMachine:

    def __init__(self):
        try:
            self._command_storage = CommandStorage("data/input.txt")
        except IOError as e:
            print(e)
            exit(-1)

    def run(self):
        for cmd in self._command_storage.next_command():
            print(cmd)
