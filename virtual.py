import sys
import os
import re
from enum import Enum
from collections import deque


class MemoryAddress:
    @staticmethod
    def is_valid(candidate):
        return bool(re.fullmatch(r"{[A-Za-z0-9_]+}", candidate))


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


class Command:
    def __init__(self, line: str):
        try:
            parts = line.split(" ")
            self.args = parts[1:]
            self.action = Action.from_str(parts[0])

            CommandChecker.check_and_parse(self.action, self.args)
        except Exception:
            raise ValueError(f"Invalid command: '{line}'")

    def __str__(self):
        return f"{self.action} {self.args}"


class CommandChecker:
    @staticmethod
    def check_and_parse(action, args: list):
        match action:
            case Action.Type.IDLE:
                return CommandChecker.Idle.check_and_parse(args)
            case Action.Type.PUSH:
                return CommandChecker.Push.check_and_parse(args)
            case Action.Type.POP:
                return CommandChecker.Pop.check_and_parse(args)
            case Action.Type.INC:
                return CommandChecker.Inc.check_and_parse(args)
            case Action.Type.ADD:
                return CommandChecker.Add.check_and_parse(args)
            case Action.Type.SUB:
                return CommandChecker.Sub.check_and_parse(args)
            case Action.Type.STORE:
                return CommandChecker.Store.check_and_parse(args)
            case Action.Type.LOAD:
                return CommandChecker.Load.check_and_parse(args)
            case Action.Type.FREE:
                return CommandChecker.Free.check_and_parse(args)
            case Action.Type.PRINT:
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
                raise ValueError(f"Invalid INC argument. Expected 1 argument: {args}")
            if MemoryAddress.is_valid(args[0]):
                return
            if Register.potential(args[0]):
                reg = Register.from_str(args[0])
                if Register.immutable(reg):
                    raise ValueError(f"Invalid INC argument. Register must be mutable: {args}")
                args[0] = reg
            else:
                args[0] = int(args[0])

    @staticmethod
    def check_2_args(args: list, err_prefix):
        if len(args) != 2:
            raise ValueError(f"{err_prefix}{args}")
        for i, arg in enumerate(args):
            if Register.potential(arg):
                args[i] = Register.from_str(arg)
            elif MemoryAddress.is_valid(arg):
                pass
            else:
                args[i] = int(arg)

    class Add:
        @staticmethod
        def check_and_parse(args: list):
            CommandChecker.check_2_args(args, "Invalid ADD arguments. Must be 2: ")

    class Sub:
        @staticmethod
        def check_and_parse(args: list):
            CommandChecker.check_2_args(args, "Invalid SUB arguments. Must be 2: ")

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


class CommandStorage:
    def __init__(self, filename: str):
        self._file = open(filename, "r")
        self._commands = []

    def next_command(self):
        for line in self._file:
            yield CommandStorage.parse_command(line.strip())

    @staticmethod
    def parse_command(line: str) -> Command:
        try:
            return Command(line)
        except ValueError as e:
            print(e, file=sys.stderr)
            exit(-1)

    def close(self):
        self._file.close()


class MachineState:
    def __init__(self):
        self.REGISTERS = dict([(r, 0) for r in Register.Type])
        self.MEMORY = {}
        self.STACK = deque()

    def set_register(self, rtype: Register.Type, value):
        if Register.immutable(rtype):
            raise TypeError(f"Cannot modify register: {rtype}")
        self.REGISTERS[rtype] = value

    def get_register_value(self, rtype: Register.Type):
        return self.REGISTERS[rtype]

    def set_memory(self, addr: str, value):
        self.MEMORY[addr] = value

    def get_memory_value(self, addr: str):
        return self.MEMORY[addr]

    def free_memory(self, addr: str):
        self.MEMORY.pop(addr)

    def resolve_int(self, arg):
        if isinstance(arg, Register.Type):
            return self.get_register_value(arg)
        elif type(arg) is str:
            return self.get_memory_value(arg)
        else:
            return arg


class Executor:
    def __init__(self, state: MachineState, out_file_path: str | None = None):
        self.state = state
        self._out_file = None
        if out_file_path is not None:
            try:
                self._out_file = open(out_file_path, "w")
                self.print = lambda data: self._out_file.write(f"{data}{os.linesep}")
            except OSError:
                print(f"Failed to open file for write {out_file_path}", file=sys.stderr)
                self.print = lambda data: print(data)

    def execute_command(self, command: Command):
        match command.action:
            case Action.Type.IDLE:
                pass
            case Action.Type.PUSH:
                self._push(command.args)

    def _push(self, args: list):
        self.state.STACK.append(self.state.resolve_int(args[0]))

    def _pop(self, args: list):
        val = self.state.STACK.pop()
        if args:
            self.state.set_memory(args[0], val)

    def _inc(self, args: list):
        arg = args[0]
        if isinstance(arg, Register.Type):
            if Register.immutable(arg):
                raise TypeError(f"[INC] The register is immutable: {arg}")
            self.state.set_register(arg, self.state.get_register_value(arg) + 1)
        elif type(arg) is str:
            self.state.set_memory(arg, self.state.get_memory_value(arg) + 1)
        else:
            self.state.set_register(Register.Type.RESULT, arg + 1)

    def _add(self, args: list):
        val1, val2 = self.state.resolve_int(args[0]), self.state.resolve_int(args[1])
        self.state.set_register(Register.Type.RESULT, val1 + val2)

    def _sub(self, args: list):
        val1, val2 = self.state.resolve_int(args[0]), self.state.resolve_int(args[1])
        self.state.set_register(Register.Type.RESULT, val1 - val2)

    def _store(self, args: list):
        arg = args[0]
        if type(arg) is int:
            value = args[0]
        else:
            value = self.state.get_register_value(Register.Type.RESULT)
        self.state.set_memory(args[1], value)

    def _load(self, args: list):
        self.state.set_register(Register.Type.RXX, args[0])

    def _free(self, args: list):
        self.state.free_memory(args[0])

    def _print(self, args: list):
        val = self.state.resolve_int(args[0])
        self.print(val)

    def close(self):
        if self._out_file is not None:
            self._out_file.close()


class VirtualMachine:

    def __init__(self):
        try:
            self._command_storage = CommandStorage("data/input.txt")
            self._executor = Executor(MachineState())
        except IOError as e:
            print(e)
            exit(-1)

    def run(self):
        try:
            for cmd in self._command_storage.next_command():
                self._executor.execute_command(cmd)
        finally:
            self._executor.close()
            self._command_storage.close()
