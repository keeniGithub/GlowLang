from main.lexer import Lexer
from main.parser.parser import Parser
from main.interpreter import Interpreter
from main.symboltable import SymbolTable
from src.run.context import Context
from src.values.number import Number

global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number(0))


def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error
    
    interpreter = Interpreter()
    context = Context("<program>")
    context.symbol_table = global_symbol_table
    result = interpreter.visit(ast.node, context)

    return result.value, result.error #ast.node, ast.error