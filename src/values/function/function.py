import main.interpret as Interpreter
from src.values.function.base import BaseFunction
from src.run.runtime import RTResult

class Function(BaseFunction):
	def __init__(self, name, body_node, arg_names):
		super().__init__(name)
		self.body_node = body_node
		self.arg_names = arg_names

	def execute(self, args):
		res = RTResult()
		interpreter = Interpreter.Interpreter()
		exec_ctx = self.generate_new_context()

		res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
		if res.error: return res

		value = res.register(interpreter.visit(self.body_node, exec_ctx))
		if res.error: return res
		return res.success(value)

	def copy(self):
		copy = Function(self.name, self.body_node, self.arg_names)
		copy.set_context(self.context)
		copy.set_pos(self.pos_start, self.pos_end)
		return copy

	def __repr__(self):
		return f"<function {self.name}>"