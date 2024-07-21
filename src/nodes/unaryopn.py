class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node
        
    def __repr__(self):
        return f"({self.op_tok}, {self.node})"