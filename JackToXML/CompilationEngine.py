class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """
    # jack language and xml related
    __BINARY_OP = {'+', '-', '*', '/', '&amp;', '|', '&lt;', '&gt;', '='}
    __UNARY_OP = {'-', '~', '^', '#'}
    __KEYWORD_CONSTANT = {"true", "false", "null", "this"}
    # constants for readability of the code
    __INDENTATION_SPACES_AMOUNT = 2
    __ONE_TIME = 1
    __TWO_TIMES = 2
    __THREE_TIMES = 3

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.__input_tokenizer = input_stream
        self.__output_stream = output_stream
        # for readability of the output file
        self.__indentation = ""
        # for keeping track of opening and closing tags
        self.__tag_rules = []
        # dict of statements and their correspondant compile methods
        self.__statements_compile_methods = {"do": self.__compile_do,
                                             "let": self.__compile_let,
                                             "while": self.__compile_while,
                                             "return": self.__compile_return,
                                             "if": self.__compile_if}

    def compile_class(self):
        """
        Compiles a complete class.
        """
        self.__write_non_terminal_opening_tag("class")
        # class -> class name -> {
        self.__advance_and_write_token(CompilationEngine.__THREE_TIMES)
        if self.__next_token_value_in({"static", "field"}):
            self.__compile_class_var_dec()
        while self.__next_token_value_in({"constructor", "method", "function"}):
            self.__compile_subroutine()
        # }
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_class_var_dec(self):
        """
        Compiles a static declaration or a field declaration.
        """
        while self.__next_token_value_in({"static", "field"}):
            self.__write_non_terminal_opening_tag("classVarDec")
            # static or field -> var type -> var name
            self.__advance_and_write_token(CompilationEngine.__THREE_TIMES)
            while self.__next_token_value_in({','}):
                # , -> var name
                self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
            # ;
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__write_non_terminal_closing_tag()

    def __compile_subroutine(self):
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        self.__write_non_terminal_opening_tag("subroutineDec")
        # subroutine's: type -> return type or constructor -> name or new
        self.__advance_and_write_token(CompilationEngine.__THREE_TIMES)
        # (
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__compile_parameter_list()
        # )
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__compile_subroutine_body()
        self.__write_non_terminal_closing_tag()

    def __compile_parameter_list(self):
        """
        Compiles a (possibly empty) parameter list, not including the
        enclosing "()".
        """
        self.__write_non_terminal_opening_tag("parameterList")
        while not self.__next_token_value_in({')'}):
            # parameters in list
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_var_dec(self):
        """
        Compiles a var declaration.
        """
        self.__write_non_terminal_opening_tag("varDec")
        # variable declaration's: var -> var type -> var name
        self.__advance_and_write_token(CompilationEngine.__THREE_TIMES)
        while self.__next_token_value_in({','}):
            # , -> var name
            self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        # ;
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_statements(self):
        """
        Compiles a sequence of statements, not including the enclosing "{}".
        """
        self.__write_non_terminal_opening_tag("statements")
        while self.__next_token_value_in({"do", "let", "while", "return", "if"}):
            next_token_value = self.__input_tokenizer.next_token_tuple()[1]
            self.__statements_compile_methods[next_token_value]()
        self.__write_non_terminal_closing_tag()

    def __compile_do(self):
        """
        Compiles a do statement.
        """
        self.__write_non_terminal_opening_tag("doStatement")
        # do
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__compile_subroutine_call()
        # ;
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_let(self):
        """
        Compiles a let statement.
        """
        self.__write_non_terminal_opening_tag("letStatement")
        # let -> var name
        self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        # if varname[expression]
        if self.__next_token_value_in({'['}):
            # [
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_expression()
            # ]
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        # =
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__compile_expression()
        # ;
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_while(self):
        """
        Compiles a while statement.
        """
        self.__write_non_terminal_opening_tag("whileStatement")
        # while -> (
        self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        self.__compile_expression()
        # ) -> {
        self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        self.__compile_statements()
        # }
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_return(self):
        """
        Compiles a return statement.
        """
        self.__write_non_terminal_opening_tag("returnStatement")
        # return
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        while (self.__next_token_type_in({"integerConstant", "stringConstant",
                                          "identifier"})) or (
                self.__next_token_value_in({'('}.union(
                    CompilationEngine.__KEYWORD_CONSTANT,
                    CompilationEngine.__UNARY_OP))):
            self.__compile_expression()
        # ;
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_if(self):
        """
        Compiles a if statement, possibly with a trailing else clause.
        """
        self.__write_non_terminal_opening_tag("ifStatement")
        # if -> (
        self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        self.__compile_expression()
        # ) -> {
        self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        self.__compile_statements()
        # } - end of body
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        if self.__next_token_value_in({"else"}):
            # else -> {
            self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
            self.__compile_statements()
            # } - end of body
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_expression(self):
        """
        Compiles an expression.
        """
        self.__write_non_terminal_opening_tag("expression")
        self.__compile_term()
        while self.__next_token_value_in(CompilationEngine.__BINARY_OP):
            # operation expression
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_term()
        self.__write_non_terminal_closing_tag()

    def __compile_term(self):
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
        self.__write_non_terminal_opening_tag("term")
        if (self.__next_token_type_in({"integerConstant", "stringConstant"})) or (
                self.__next_token_value_in(CompilationEngine.__KEYWORD_CONSTANT)):
            # constant
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        elif self.__next_token_type_in({"identifier"}):
            self.__write_identifier_term()
        elif self.__next_token_value_in(CompilationEngine.__UNARY_OP):
            # unary operation expression
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_term()
        elif self.__next_token_value_in({'('}):
            # (
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_expression()
            # )
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __compile_expression_list(self):
        """
        Compiles a (possibly empty) comma-separated list of expressions.
        """
        self.__write_non_terminal_opening_tag("expressionList")
        if (self.__next_token_type_in({"integerConstant", "stringConstant",
                                       "identifier"})) or (
                self.__next_token_value_in({'('}.union(
                    CompilationEngine.__KEYWORD_CONSTANT,
                    CompilationEngine.__UNARY_OP))):
            self.__compile_expression()
        # if number of expressions is greater than 1
        while self.__next_token_value_in({','}):
            # , - separating expressions
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_expression()
        self.__write_non_terminal_closing_tag()

    def __compile_subroutine_call(self):
        # class name or subroutine name or var name
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        # if subroutine call
        if self.__next_token_value_in({'.'}):
            # . -> subroutine name
            self.__advance_and_write_token(CompilationEngine.__TWO_TIMES)
        # (
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__compile_expression_list()
        # )
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)

    def __compile_subroutine_body(self):
        self.__write_non_terminal_opening_tag("subroutineBody")
        # { - beginning of body
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        while self.__next_token_value_in({"var"}):
            self.__compile_var_dec()
        self.__compile_statements()
        # } - end of body
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        self.__write_non_terminal_closing_tag()

    def __write_non_terminal_opening_tag(self, tag_rule):
        self.__output_stream.write("{}<{}>\n".format(
            self.__indentation, tag_rule))
        self.__tag_rules.append(tag_rule)
        self.__increase_indentation()

    def __write_non_terminal_closing_tag(self):
        self.__decrease_indentation()
        self.__output_stream.write("{}</{}>\n".format(self.__indentation,
                                                      self.__tag_rules.pop()))

    def __write_terminal_tags_and_value(self, token_type, token_value):
        self.__output_stream.write("{}<{}> {} </{}>\n".format(
            self.__indentation, token_type, token_value, token_type))

    def __write_identifier_term(self):
        # class name or var name
        self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        # if varname[expression]
        if self.__next_token_value_in({'['}):
            # [
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_expression()
            # ]
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        if self.__next_token_value_in({'('}):
            # (
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
            self.__compile_expression_list()
            # )
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)
        # if subroutine call
        if self.__next_token_value_in({'.'}):
            # . -> subroutine name -> (
            self.__advance_and_write_token(CompilationEngine.__THREE_TIMES)
            self.__compile_expression_list()
            # )
            self.__advance_and_write_token(CompilationEngine.__ONE_TIME)

    def __advance_and_write_token(self, iterations):
        for i in range(iterations):
            token_type, token_value = self.__input_tokenizer.advance()
            self.__write_terminal_tags_and_value(token_type, token_value)

    def __next_token_value_in(self, values_set):
        return self.__input_tokenizer.next_token_tuple()[1] in values_set

    def __next_token_type_in(self, types_set):
        return self.__input_tokenizer.next_token_tuple()[0] in types_set

    def __increase_indentation(self):
        for i in range(CompilationEngine.__INDENTATION_SPACES_AMOUNT):
            self.__indentation += " "

    def __decrease_indentation(self):
        self.__indentation = \
            self.__indentation[:-CompilationEngine.__INDENTATION_SPACES_AMOUNT]
