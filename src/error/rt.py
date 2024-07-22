from src.error.error import Error
from src.arrow import arrow

class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "\nRuntime Error", details)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        result += f"\n{arrow(self.pos_start.ftxt, self.pos_start, self.pos_end)}"
        return result

    def generate_traceback(self):
        result = ""
        pos = self.pos_start
        ctx = self.context

        while ctx:
            result = f" File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n{result}"
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return f"\nTraceback:\n{result}"