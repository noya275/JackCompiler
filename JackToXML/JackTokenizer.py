import re
import typing


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.

    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters,
    and comments, which are ignored. There are three possible comment formats:
    /* comment until closing */ , /** API comment until closing */ , and
    // comment until the line's end.

    - 'xxx': quotes are used for tokens that appear verbatim ('terminals').
    - xxx: regular typeface is used for names of language constructs
           ('non-terminals').
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' |
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 
               'true' | 'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 
               'else' | 'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' |
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including
                      double quote or newline '"'
    - identifier: A sequence of letters, digits, and underscore ('_') not
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate
    file. A compilation unit is a single class. A class is a sequence of tokens
    structured according to the following context free syntax:

    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type)
    - subroutineName '(' parameterList ')' subroutineBody
    - parameterList: ((type varName) (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement |
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{'
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions

    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant | varName |
            varName '['expression']' | subroutineCall | '(' expression ')' |
            unaryOp term
    - subroutineCall: subroutineName '(' expressionList ')' | (className |
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'

    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """
    # jack language and xml conversion related
    __KEYWORDS = {"class", "constructor", "function", "method", "field",
                  "static", "var", "int", "char", "boolean", "void", "true",
                  "false", "null", "this", "let", "do", "if", "else", "while",
                  "return"}
    __SYMBOLS = {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*',
                 '/', '&', '<', '>', '=', '~', '|', '^', '#'}
    __XML_DICT = {'<': '&lt;', '>': '&gt;', '&': '&amp;'}
    # for regex usage
    __INTEGER_RE = r'\d+'
    __STRING_RE = r'"[^"\n]*"'
    __IDENTIFIER_RE = r'[\w]+'
    __KEYWORD_RE = r'{}(?!\w)'.format(r'(?!\w)|'.join(__KEYWORDS))
    __SYMBOL_RE = '[{}]'.format('|'.join(re.escape(s) for s in __SYMBOLS))
    __PATTERN = re.compile('|'.join([__KEYWORD_RE, __SYMBOL_RE,
                                     __INTEGER_RE, __STRING_RE,
                                     __IDENTIFIER_RE]))

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.
        Args:
            input_stream (typing.TextIO): input stream.
        """
        self.__input_file_str = input_stream.read()
        self.__remove_comments()
        self.__cur_token = ()
        self.__tokens = self.__get_tokens()

    def advance(self) -> tuple:
        """Gets the next token from the input and makes it the current token.
        This method should be called if there are tokens left.
        Initially there is no current token.
        """
        self.__cur_token = self.__tokens.pop(0)
        return self.__cur_token

    def next_token_tuple(self) -> tuple:
        return self.__tokens[0]

    def __remove_comments(self) -> None:
        cur_idx = 0
        comment_free_str = ''
        while cur_idx < len(self.__input_file_str):
            # add quotations to comment_free_str - ignore comments inside
            if self.__input_file_str[cur_idx] == "\"":
                quot_end = self.__input_file_str.find("\"", cur_idx + 1)
                comment_free_str += self.__input_file_str[cur_idx:quot_end + 1]
                cur_idx = quot_end + 1
            # ignore comments and move to next characters in file
            if self.__input_file_str[cur_idx:cur_idx + 2] == "//":
                cur_idx = self.__input_file_str.find("\n", cur_idx + 1) + 1
                comment_free_str += "\n"
            elif self.__input_file_str[cur_idx:cur_idx + 2] == "/*":
                cur_idx = self.__input_file_str.find("*/", cur_idx + 1) + 2
                comment_free_str += "\n"
            else:
                comment_free_str += self.__input_file_str[cur_idx]
                cur_idx += 1
        self.__input_file_str = comment_free_str

    def __get_tokens(self) -> list:
        tokens = []
        for word in JackTokenizer.__PATTERN.findall(
                self.__input_file_str):
            tokens.append(JackTokenizer.__type_and_value(word))
        return tokens

    @staticmethod
    def __type_and_value(word) -> tuple:
        if JackTokenizer.__word_matches_pattern(JackTokenizer.__INTEGER_RE, word):
            return "integerConstant", word
        if JackTokenizer.__word_matches_pattern(JackTokenizer.__STRING_RE, word):
            return "stringConstant", word[1:-1]
        if JackTokenizer.__word_matches_pattern(JackTokenizer.__KEYWORD_RE, word):
            return "keyword", word
        if JackTokenizer.__word_matches_pattern(JackTokenizer.__SYMBOL_RE, word):
            xml_appropriate = word
            if word in JackTokenizer.__XML_DICT.keys():
                xml_appropriate = JackTokenizer.__XML_DICT[word]
            return "symbol", xml_appropriate
        return "identifier", word

    @staticmethod
    def __word_matches_pattern(pattern, word):
        return re.match(pattern, word) is not None
