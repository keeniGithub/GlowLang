from src.main.lexer import Lexer
from src.main.parser.parser import Parser
from src.main.interpret import Interpreter
from src.main.symboltable import SymbolTable
from src.run.context import Context
from src.values.types.number import Number
from src.values.function.buildin import BuiltInFunction

global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number.null)
global_symbol_table.set("true", Number.true)
global_symbol_table.set("false", Number.false)
global_symbol_table.set("pi", Number.math_PI)
global_symbol_table.set("e", Number.math_E)

BuiltInFunction.print = BuiltInFunction("print")
BuiltInFunction.input = BuiltInFunction("input")
BuiltInFunction.input_int = BuiltInFunction("input_int")
BuiltInFunction.clear = BuiltInFunction("clear")
BuiltInFunction.is_number = BuiltInFunction("is_number")
BuiltInFunction.is_string = BuiltInFunction("is_string")
BuiltInFunction.is_list = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append = BuiltInFunction("append")
BuiltInFunction.pop = BuiltInFunction("pop")
BuiltInFunction.extend = BuiltInFunction("extend")
BuiltInFunction.len = BuiltInFunction("len")
BuiltInFunction.run = BuiltInFunction("run")

global_symbol_table.set("print", BuiltInFunction.print)
global_symbol_table.set("input", BuiltInFunction.input)
global_symbol_table.set("input_int", BuiltInFunction.input_int)
global_symbol_table.set("clear", BuiltInFunction.clear)
global_symbol_table.set("cls", BuiltInFunction.clear)
global_symbol_table.set("is_num", BuiltInFunction.is_number)
global_symbol_table.set("is_str", BuiltInFunction.is_string)
global_symbol_table.set("is_list", BuiltInFunction.is_list)
global_symbol_table.set("is_func", BuiltInFunction.is_function)
global_symbol_table.set("append", BuiltInFunction.append)
global_symbol_table.set("pop", BuiltInFunction.pop)
global_symbol_table.set("extend", BuiltInFunction.extend)
global_symbol_table.set("len", BuiltInFunction.len)
global_symbol_table.set("run", BuiltInFunction.run)

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

    return result.value, result.error