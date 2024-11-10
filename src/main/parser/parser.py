from src.var.token import (
    TT_INT, TT_FLOAT, TT_STRING,
    TT_MUL, TT_DIV,
    TT_POW,
    TT_PLUS, TT_MINUS,
    TT_LPAREN, TT_RPAREN,
    TT_LSQUARE, TT_RSQUARE,
    TT_E0F,
    TT_KEYWORD, TT_IDENTIFIER, TT_EQ,
    TT_EE, TT_NE, TT_LT, TT_GT,
                  TT_LTE, TT_GTE,
    TT_COMMA, TT_ARROW,
    TT_NEWLINE
)

from src.nodes.types.number import NumberNode
from src.nodes.ops.binop import BinOpNode
from src.nodes.ops.unaryop import UnaryOpNode
from src.nodes.variables.access import VarAccessNode
from src.nodes.variables.assign import VarAssignNode
from src.nodes.condition.ifN import IfNode
from src.nodes.loops.forN import ForNode
from src.nodes.loops.whileN import WhileNode
from src.nodes.function.funcdef import FuncDefNode
from src.nodes.function.call import CallNode
from src.nodes.types.string import StringNode
from src.nodes.types.list import ListNode
from src.nodes.jump.breakN import BreakNode
from src.nodes.jump.returnN import ReturnNode
from src.nodes.jump.continueN import ContinueNode
from src.error.message.invalidsyntax import InvalidSyntaxError
from src.main.parser.result import ParseResult

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        self.update_current_tok()
        return self.current_tok

    def reverse(self, amount=1):
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self):
        if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
    
    def parse(self):
        res = self.statements()
        if not res.error and self.current_tok.type != TT_E0F:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'and' or 'or'"
            ))
        return res

    def list_expr(self):
        res = ParseResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '['"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-', '(', '[' or 'not'"
                ))

            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error: return res

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ']'"
                ))

            res.register_advancement()
            self.advance()

        return res.success(ListNode(
            element_nodes,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    def if_expr(self):
        res = ParseResult()
        all_cases = res.register(self.if_expr_cases("if"))
        if res.error: return res
        cases, else_case = all_cases
        return res.success(IfNode(cases, else_case))
    
    def if_expr_b(self):
        return self.if_expr_cases("elif")
    
    def if_expr_c(self):
        res = ParseResult()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, "else"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()

                statements = res.register(self.statements())
                if res.error: return res
                else_case = (statements, True)

                if self.current_tok.matches(TT_KEYWORD, "end"):
                    res.register_advancement()
                    self.advance()
                else:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected 'end'"
                    ))
            else:
                expr = res.register(self.statement())
                if res.error: return res
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self):
        res = ParseResult()
        cases, else_case = [], None

        if self.current_tok.matches(TT_KEYWORD, "elif"):
            all_cases = res.register(self.if_expr_b())
            if res.error: return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error: return res
        
        return res.success((cases, else_case))

    def if_expr_cases(self, case_keyword):
        res = ParseResult()
        cases = []
        else_case = None

        if not self.current_tok.matches(TT_KEYWORD, case_keyword):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '{case_keyword}'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'then'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            statements = res.register(self.statements())
            if res.error: return res
            cases.append((condition, statements, True))

            if self.current_tok.matches(TT_KEYWORD, "end"):
                res.register_advancement()
                self.advance()
            else:
                all_cases = res.register(self.if_expr_b_or_c())
                if res.error: return res
                new_cases, else_case = all_cases
                cases.extend(new_cases)
        else:
            expr = res.register(self.statement())
            if res.error: return res
            cases.append((condition, expr, False))

            all_cases = res.register(self.if_expr_b_or_c())
            if res.error: return res
            new_cases, else_case = all_cases
            cases.extend(new_cases)

        return res.success((cases, else_case))

    def for_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "for"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'for'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected identifier"
            ))

        var_name = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '='"
            ))
        
        res.register_advancement()
        self.advance()

        start_value = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, "to"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'to'"
            ))
        
        res.register_advancement()
        self.advance()

        end_value = res.register(self.expr())
        if res.error: return res

        if self.current_tok.matches(TT_KEYWORD, "step"):
            res.register_advancement()
            self.advance()

            step_value = res.register(self.expr())
            if res.error: return res
        else:
            step_value = None

        if not self.current_tok.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'then'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, "end"):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected 'end'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))
            
        body = res.register(self.statement())
        if res.error: return res

        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    def while_expr(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, "while"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'while'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.statement())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, "then"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'then'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, "end"):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected 'end'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(WhileNode(condition, body, True))
    
        body = res.register(self.expr())
        if res.error: return res

        return res.success(WhileNode(condition, body, False))

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(tok))
        
        if tok.type in TT_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(tok))
        
        elif tok.type == TT_IDENTIFIER:
            res.register_advancement()
            self.advance()
            return res.success(VarAccessNode(tok))

        elif tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))
        
        elif tok.type == TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)

        elif tok.matches(TT_KEYWORD, "if"):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)

        elif tok.matches(TT_KEYWORD, "for"):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)
        
        elif tok.matches(TT_KEYWORD, "while"):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)
        
        elif tok.matches(TT_KEYWORD, "func"):
            func_def = res.register(self.func_def())
            if res.error: return res
            return res.success(func_def)

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, identifier, '+', '-', or '(', '[', 'for', 'while', 'if', 'func'"
        ))

    def power(self):
        return self.bin_op(self.call, (TT_POW, ), self.factor)
    
    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error: return res

        if self.current_tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            if self.current_tok.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-', '(', '[' or 'not'"
                    ))

                while self.current_tok.type == TT_COMMA:
                    res.register_advancement()
                    self.advance()

                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res

                if self.current_tok.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected ',' or ')'"
                    ))

                res.register_advancement()
                self.advance()
            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def arith_expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def comp_expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, "not"):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_tok, node))
        
        node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))

        if res.error:
            return res.failure(InvalidSyntaxError(
				self.current_tok.pos_start, self.current_tok.pos_end,
				"Expected int, float, identifier, '+', '-', '(', '[', or 'not'"
			))
        
        return res.success(node)

    def statements(self):
        res = ParseResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

        statement = res.register(self.statement())
        if res.error: return res
        statements.append(statement)

        more_statements = True

        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements = False
        
            if not more_statements: break
            statement = res.try_register(self.statement())
            if not statement:
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)

        return res.success(ListNode(
            statements,
            pos_start,
            self.current_tok.pos_end.copy()
        ))

    def statement(self):
        res = ParseResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, 'return'):
            res.register_advancement()
            self.advance()

            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))
        
        if self.current_tok.matches(TT_KEYWORD, 'continue'):
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))
        
        if self.current_tok.matches(TT_KEYWORD, 'break'):
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

        expr = res.register(self.expr())
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'return', 'continue', 'break', 'var', 'if', 'for', 'while', 'func', int, float, identifier, '+', '-', '(', '[' or 'not'"
            ))
        
        return res.success(expr)

    def expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, "var"):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))
            
            var_name = self.current_tok
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))
            
            res.register_advancement()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VarAssignNode(var_name, expr))

        node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, "and"), (TT_KEYWORD, "or"))))

        if res.error: 
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'var', 'if', 'for', 'while', 'fun' int, float, identifier, '+', '-', '(', '[', 'not'"
            ))

        return res.success(node)

    def func_def(self):
        res = ParseResult()

        if not self.current_tok.matches(TT_KEYWORD, 'func'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'func'"
            ))
        
        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_IDENTIFIER:
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected '('"
                ))
        else:
            var_name_tok = None
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or '('"
                ))

        res.register_advancement()
        self.advance()
        arg_name_toks = []

        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()
            
            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        f"Expected identifier"
                    ))

                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()
            
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected ',' or ')'"
                ))
        else:
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    f"Expected identifier or ')'"
                ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_ARROW:
            res.register_advancement()
            self.advance()

            body = res.register(self.expr())
            if res.error: return res

            return res.success(FuncDefNode(
                var_name_tok,
                arg_name_toks,
                body,
                True
            ))
            
        if self.current_tok.type != TT_NEWLINE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '->' or NEWLINE"
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.statements())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, "end"):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected 'end'"
            ))

        res.register_advancement()
        self.advance()
        
        return res.success(FuncDefNode(
            var_name_tok,
            arg_name_toks,
            body,
            False
        ))

    def bin_op(self, func_a, ops, func_b=None): 
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinOpNode(left, op_tok, right)

        return res.success(left)