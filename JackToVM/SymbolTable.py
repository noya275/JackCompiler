class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self.__class_level_symbol_table = {}
        self.__subroutine_symbol_table = {}
        self.__cur_symbol_table = self.__class_level_symbol_table

        self.__static_counter = 0
        self.__field_counter = 0

        self.__arg_counter = 0
        self.__var_counter = 0
        self.__if_counter = 0
        self.__while_counter = 0

    def start_subroutine(self, name: str) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's
        symbol table).
        """
        self.__subroutine_symbol_table[name] = {}
        self.__arg_counter = 0
        self.__var_counter = 0
        self.__if_counter = 0
        self.__while_counter = 0

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns
        it a running index. "STATIC" and "FIELD" identifiers have a class scope,
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """
        if kind == "static":
            self.__class_level_symbol_table[name] = (
                type, kind, self.__static_counter)
            self.__static_counter += 1
        elif kind == "field":
            self.__class_level_symbol_table[name] = (
                type, kind, self.__field_counter)
            self.__field_counter += 1
        elif kind == "arg":
            self.__cur_symbol_table[name] = (
                type, kind, self.__arg_counter)
            self.__arg_counter += 1
        elif kind == "var":
            self.__cur_symbol_table[name] = (
                type, kind, self.__var_counter)
            self.__var_counter += 1

    def subroutine_level_var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in
            the current scope.
        """
        count = 0
        for tpl in self.__cur_symbol_table.values():
            if tpl[1] == kind:
                count += 1
        return count

    def class_level_var_count(self, kind: str) -> int:
        count = 0
        for tpl in self.__class_level_symbol_table.values():
            if tpl[1] == kind:
                count += 1
        return count

    def kind_of(self, name: str):
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        if name in self.__cur_symbol_table:
            return self.__cur_symbol_table[name][1]
        if name in self.__class_level_symbol_table:
            return self.__class_level_symbol_table[name][1]

    def type_of(self, name: str):
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope.
        """
        if name in self.__cur_symbol_table:
            return self.__cur_symbol_table[name][0]
        if name in self.__class_level_symbol_table:
            return self.__class_level_symbol_table[name][0]

    def index_of(self, name: str):
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier.
        """
        if name in self.__cur_symbol_table:
            return self.__cur_symbol_table[name][2]
        if name in self.__class_level_symbol_table:
            return self.__class_level_symbol_table[name][2]

    def get_if_counter(self) -> int:
        return self.__if_counter

    def get_while_counter(self) -> int:
        return self.__while_counter

    def increment_if_counter(self) -> None:
        self.__if_counter += 1

    def increment_while_counter(self) -> None:
        self.__while_counter += 1

    def set_cur_level_symbol_table(self, name: str):
        if name == "class":
            self.__cur_symbol_table = self.__class_level_symbol_table
        else:
            self.__cur_symbol_table = self.__subroutine_symbol_table[name]

    def current_symbol_table_contains(self, name: str) -> bool:
        return name in self.__cur_symbol_table

    def class_level_symbol_table_contains(self, name: str) -> bool:
        return name in self.__class_level_symbol_table
