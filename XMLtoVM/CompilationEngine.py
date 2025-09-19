class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """
    # jack language and vm related
    __UNARY_OP_DICT = {'-': "neg", '~': "not", '^': "shiftleft",
                       '#': "shiftright"}
    __CALL_BINARY_OP_DICT = {'*': "Math.multiply", '/': "Math.divide"}
    __ARITHMETIC_BINARY_OP_DICT = {'+': "add", '-': "sub", '&': "and",
                                   '|': "or", '<': "lt", '>': "gt", '=': "eq"}
    __KEYWORD_CONSTANT = {"true", "false", "null", "this"}
    __VAR_DICT1 = {"var": "local", "arg": "argument"}
    __VAR_DICT2 = {"field": "this", "static": "static"}
    __ARGS = 2

    def __init__(self, input_stream: "JackTokenizer",
                 output_stream: "VMWriter", symbol_table: "SymbolTable") -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.__input_tokenizer = input_stream
        self.__output_vm_writer = output_stream
        self.__symbol_table = symbol_table
        self.__class_name = ""
        # dict of statements and their correspondant compile methods
        self.__statements_dict = {"do": self.__compile_do,
                                  "let": self.__compile_let,
                                  "while": self.__compile_while,
                                  "return": self.__compile_return,
                                  "if": self.__compile_if}

    def compile_class(self) -> None:
        """
        Compiles a complete class.
        """
        # class
        self.__advance()
        # class name
        self.__class_name = self.__advance()
        # {
        self.__advance()
        while self.__next_token_value_in({"static", "field"}):
            self.__compile_class_var_dec()
        while self.__next_token_value_in({"constructor", "method", "function"}):
            self.__compile_subroutine()
        # }
        self.__advance()

    def __compile_class_var_dec(self) -> None:
        """
        Compiles a static declaration or a field declaration.
        """
        # static or field -> var type -> var name
        kind = self.__advance()
        type = self.__advance()
        name = self.__advance()
        # add entry to symbol table using inputs
        self.__symbol_table.define(name, type, kind)
        while self.__next_token_value_in({','}):
            # ,
            self.__advance()
            # var name
            name = self.__advance()
            # add entry to symbol table
            self.__symbol_table.define(name, type, kind)
        # ;
        self.__advance()

    def __compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        # constructor or function or method
        function_type = self.__advance()
        # class name or return type
        self.__advance()
        # subroutine's name
        sub_name = self.__advance()
        # get new or subroutine's name
        cur_name = "{}.{}".format(self.__class_name, sub_name)
        # start the new subroutine and update current symbol table
        self.__symbol_table.start_subroutine(cur_name)
        self.__symbol_table.set_cur_level_symbol_table(cur_name)
        # (
        self.__advance()
        self.__compile_parameter_list(function_type)
        # )
        self.__advance()
        self.__compile_subroutine_body(function_type, cur_name)

    def __compile_parameter_list(self, function_type) -> None:
        """
        Compiles a (possibly empty) parameter list, not including the
        enclosing "()".
        """
        if function_type == "method":
            self.__symbol_table.define("this", "self", "arg")
        while not self.__next_token_value_in({')'}):
            # parameter type and name
            type = self.__advance()
            name = self.__advance()
            # add entry to symbol table
            self.__symbol_table.define(name, type, "arg")
            if self.__next_token_value_in({','}):
                # ,
                self.__advance()

    def __compile_var_dec(self) -> None:
        """
        Compiles a var declaration.
        """
        # variable declaration's: var -> var type -> var name
        kind = self.__advance()
        type = self.__advance()
        name = self.__advance()
        self.__symbol_table.define(name, type, kind)
        while self.__next_token_value_in({','}):
            # ,
            self.__advance()
            # var name
            name = self.__advance()
            self.__symbol_table.define(name, type, kind)
        # ;
        self.__advance()

    def __compile_statements(self) -> None:
        """
        Compiles a sequence of statements, not including the enclosing "{}".
        """
        while self.__next_token_value_in(self.__statements_dict.keys()):
            next_token_value = self.__input_tokenizer.next_token_tuple()[1]
            self.__statements_dict[next_token_value]()

    def __compile_do(self) -> None:
        """
        Compiles a do statement.
        """
        # do
        self.__advance()
        self.__compile_subroutine_call()
        # dump redundant return value
        self.__output_vm_writer.write_pop("temp", 0)
        # ;
        self.__advance()

    def __compile_let(self) -> None:
        """
        Compiles a let statement.
        """
        # let
        self.__advance()
        # var name
        name = self.__advance()
        # if varname[expression]
        is_array = self.__write_left_square_bracket(name)
        # =
        self.__advance()
        self.__compile_expression()
        if is_array:
            self.__output_vm_writer.write_pop("temp", 0)
            self.__output_vm_writer.write_pop("pointer", 1)
            self.__output_vm_writer.write_push("temp", 0)
            self.__output_vm_writer.write_pop("that", 0)
        else:
            self.__write_pop(name)
        # ;
        self.__advance()

    def __compile_while(self) -> None:
        """
        Compiles a while statement.
        """
        while_counter = self.__symbol_table.get_while_counter()
        self.__symbol_table.increment_while_counter()
        start_label = "WHILE_START{}".format(while_counter)
        end_label = "WHILE_END{}".format(while_counter)
        self.__output_vm_writer.write_label(start_label)
        # while -> (
        self.__advance()
        self.__advance()
        self.__compile_expression()
        self.__output_vm_writer.write_arithmetic("not")
        self.__output_vm_writer.write_if(end_label)
        # ) -> {
        self.__advance()
        self.__advance()
        self.__compile_statements()
        self.__output_vm_writer.write_goto(start_label)
        self.__output_vm_writer.write_label(end_label)
        # }
        self.__advance()

    def __compile_return(self) -> None:
        """
        Compiles a return statement.
        """
        # return
        self.__advance()
        redundant_return = True
        while (self.__next_token_type_in({"integerConstant", "stringConstant",
                                          "identifier"})) or (
                self.__next_token_value_in({'('}.union(
                    CompilationEngine.__KEYWORD_CONSTANT,
                    set(CompilationEngine.__UNARY_OP_DICT.keys())))):
            redundant_return = False
            self.__compile_expression()
        if redundant_return:
            self.__output_vm_writer.write_push("constant", 0)
        self.__output_vm_writer.write_return()
        # ;
        self.__advance()

    def __compile_if(self) -> None:
        """
        Compiles a if statement, possibly with a trailing else clause.
        """
        # if -> (
        self.__advance()
        self.__advance()
        self.__compile_expression()
        # )
        self.__advance()
        if_counter = self.__symbol_table.get_if_counter()
        self.__symbol_table.increment_if_counter()
        if_true_label = "IF_START{}".format(if_counter)
        if_false_label = "ELSE{}".format(if_counter)
        self.__output_vm_writer.write_if(if_true_label)
        self.__output_vm_writer.write_goto(if_false_label)
        self.__output_vm_writer.write_label(if_true_label)
        # {
        self.__advance()
        self.__compile_statements()
        # }
        self.__advance()
        self.__write_if_else(if_counter, if_false_label)

    def __write_if_else(self, if_counter, if_false_label):
        if_end_label = "IF_END{}".format(if_counter)
        if self.__next_token_value_in({"else"}):
            self.__output_vm_writer.write_goto(if_end_label)
            self.__output_vm_writer.write_label(if_false_label)
            # else -> {
            self.__advance()
            self.__advance()
            self.__compile_statements()
            # }
            self.__advance()
            self.__output_vm_writer.write_label(if_end_label)
        else:
            self.__output_vm_writer.write_label(if_false_label)

    def __compile_expression(self) -> None:
        """
        Compiles an expression.
        """
        self.__compile_term()
        while self.__next_token_value_in(
                set(CompilationEngine.__CALL_BINARY_OP_DICT.keys()).union(
                    set(CompilationEngine.__ARITHMETIC_BINARY_OP_DICT.keys()))):
            op = self.__advance()
            # operation expression
            self.__compile_term()
            if op in CompilationEngine.__CALL_BINARY_OP_DICT.keys():
                self.__output_vm_writer.write_call(
                    CompilationEngine.__CALL_BINARY_OP_DICT[op],
                    CompilationEngine.__ARGS)
            elif op in CompilationEngine.__ARITHMETIC_BINARY_OP_DICT.keys():
                self.__output_vm_writer.write_arithmetic(
                    CompilationEngine.__ARITHMETIC_BINARY_OP_DICT[op])

    def __compile_term(self) -> None:
        """
        Compiles a term.
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of '[', '(', or '.'
        suffices to distinguish between the three possibilities. Any other
        token is not part of this term and should not be advanced over.
        """
        if (self.__next_token_type_in({"integerConstant", "stringConstant"})) or (
                self.__next_token_value_in(CompilationEngine.__KEYWORD_CONSTANT)):
            self.__write_integer_string_keyword_constant()
        elif self.__next_token_type_in({"identifier"}):
            self.__write_identifier_term()
        elif self.__next_token_value_in(CompilationEngine.__UNARY_OP_DICT.keys()):
            # unary operation expression
            op = self.__advance()
            self.__compile_term()
            self.__output_vm_writer.write_arithmetic(CompilationEngine.__UNARY_OP_DICT[op])
        elif self.__next_token_value_in({'('}):
            # (
            self.__advance()
            self.__compile_expression()
            # )
            self.__advance()

    def __compile_expression_list(self) -> int:
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        """
        args_counter = 0
        if (self.__next_token_type_in({"integerConstant", "stringConstant",
                                       "identifier"})) or (
                self.__next_token_value_in({'('}.union(
                    CompilationEngine.__KEYWORD_CONSTANT,
                    set(CompilationEngine.__UNARY_OP_DICT.keys())))):
            self.__compile_expression()
            args_counter = 1
        # if number of expressions is greater than 1
        while self.__next_token_value_in({','}):
            # ,
            self.__advance()
            self.__compile_expression()
            args_counter += 1
        return args_counter

    def __compile_subroutine_call(self) -> None:
        name = self.__advance()
        # if subroutine call
        if self.__next_token_value_in({'.'}):
            n_args, precise_name = self.__write_precise_subroutine_name(name)
        else:
            self.__output_vm_writer.write_push("pointer", 0)
            n_args = 1
            precise_name = "{}.{}".format(self.__class_name, name)
        # (
        self.__advance()
        n_args += self.__compile_expression_list()
        self.__output_vm_writer.write_call(precise_name, n_args)
        # )
        self.__advance()

    def __write_precise_subroutine_name(self, name):
        # .
        self.__advance()
        # subroutine name
        sub_name = self.__advance()
        if (self.__symbol_table.current_symbol_table_contains(name)) or (
                self.__symbol_table.class_level_symbol_table_contains(name)):
            self.__write_push(name)
            precise_name = "{}.{}".format(self.__symbol_table.type_of(name),
                                          sub_name)
            n_args = 1
        else:
            precise_name = "{}.{}".format(name, sub_name)
            n_args = 0
        return n_args, precise_name

    def __compile_subroutine_body(self, function_type, cur_name) -> None:
        # {
        self.__advance()
        while self.__next_token_value_in({"var"}):
            self.__compile_var_dec()
        n_locals = self.__symbol_table.subroutine_level_var_count("var")
        self.__output_vm_writer.write_function(cur_name, n_locals)
        self.__write_pointer_update(function_type)
        self.__compile_statements()
        # }
        self.__advance()
        # update current symbol table
        self.__symbol_table.set_cur_level_symbol_table("class")

    def __write_integer_string_keyword_constant(self) -> None:
        if self.__next_token_type_in({"integerConstant"}):
            # constant
            number = self.__advance()
            self.__output_vm_writer.write_push("constant", number)
        elif self.__next_token_type_in({"stringConstant"}):
            # string
            string = self.__advance()
            self.__output_vm_writer.write_push("constant", len(string))
            self.__output_vm_writer.write_call("String.new", 1)
            for char in string:
                self.__output_vm_writer.write_push("constant", ord(char))
                self.__output_vm_writer.write_call("String.appendChar",
                                                   CompilationEngine.__ARGS)
        elif self.__next_token_value_in(CompilationEngine.__KEYWORD_CONSTANT):
            # keyword constant
            keyword_constant = self.__advance()
            if keyword_constant == "this":
                self.__output_vm_writer.write_push("pointer", 0)
            else:
                self.__output_vm_writer.write_push("constant", 0)
                # negate boolean
                if keyword_constant == "true":
                    self.__output_vm_writer.write_arithmetic("not")

    def __write_pointer_update(self, function_type) -> None:
        if function_type == "constructor":
            n_args = self.__symbol_table.class_level_var_count("field")
            self.__output_vm_writer.write_push("constant", n_args)
            self.__output_vm_writer.write_call("Memory.alloc", 1)
            self.__output_vm_writer.write_pop("pointer", 0)
        elif function_type == "method":
            self.__output_vm_writer.write_push("argument", 0)
            self.__output_vm_writer.write_pop("pointer", 0)

    def __write_identifier_term(self) -> None:
        # class name or var name
        name = self.__advance()
        # if varname[expression]
        is_array = self.__write_left_square_bracket(name)
        if self.__next_token_value_in({'('}):
            n_args = 1
            self.__output_vm_writer.write_push("pointer", 0)
            # (
            self.__advance()
            n_args += self.__compile_expression_list()
            # )
            self.__advance()
            self.__output_vm_writer.write_call("{}.{}".format(self.__class_name, name), n_args)
        # if subroutine call
        else:
            self.__write_period_and_array_end(is_array, name)

    def __write_period_and_array_end(self, is_array, name) -> None:
        precise_name = name
        if self.__next_token_value_in({'.'}):
            n_args, precise_name = self.__write_precise_subroutine_name(name)
            # (
            self.__advance()
            n_args += self.__compile_expression_list()
            # )
            self.__advance()
            self.__output_vm_writer.write_call(precise_name, n_args)
        else:
            if is_array:
                self.__output_vm_writer.write_pop("pointer", 1)
                self.__output_vm_writer.write_push("that", 0)
            else:
                self.__write_push(precise_name)

    def __write_left_square_bracket(self, name: str) -> bool:
        is_array = False
        if self.__next_token_value_in({'['}):
            is_array = True
            # [
            self.__advance()
            self.__compile_expression()
            # ]
            self.__advance()
            self.__write_push(name)
            self.__output_vm_writer.write_arithmetic("add")
        return is_array

    def __advance(self) -> str:
        return self.__input_tokenizer.advance()[1]

    def __next_token_type_in(self, types_set) -> bool:
        return self.__input_tokenizer.next_token_tuple()[0] in types_set

    def __next_token_value_in(self, values_set) -> bool:
        return self.__input_tokenizer.next_token_tuple()[1] in values_set

    def __write_pop_or_push(self, name, method) -> None:
        kind = self.__symbol_table.kind_of(name)
        if self.__symbol_table.current_symbol_table_contains(name):
            if kind in CompilationEngine.__VAR_DICT1:
                method(CompilationEngine.__VAR_DICT1[kind],
                       self.__symbol_table.index_of(name))
        else:
            if kind in CompilationEngine.__VAR_DICT2:
                method(CompilationEngine.__VAR_DICT2[kind],
                       self.__symbol_table.index_of(name))

    def __write_pop(self, name) -> None:
        self.__write_pop_or_push(name, self.__output_vm_writer.write_pop)

    def __write_push(self, name) -> None:
        self.__write_pop_or_push(name, self.__output_vm_writer.write_push)
