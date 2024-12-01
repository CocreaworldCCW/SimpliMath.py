import time

class SimpliMath:
    def __init__(self):
        self.variables = {}  # Stores variables and their values
        self.outputs = []  # Stores output data to display after code ends
        self.inputs = []   # Stores input requests to ensure precedence
        self.code_running = True
        self.hold = False  # State to track if the loop is active

    def execute(self, code):
        """Executes SimpliMath code entered by the user."""
        lines = code.strip().split("\n")
        for line in lines:
            if not self.code_running:
                break
            self.parse_command(line.strip())

        # Resolve inputs before handling outputs
        self.resolve_inputs()
        self.handle_outputs()

    def parse_command(self, command):
        """Parses and executes a single line of SimpliMath code."""
        if not command or command.startswith("***"):
            return  # Ignore empty lines and comments

        if "=" in command and "input(" in command and command.endswith(")"):
            self.queue_input(command)  # Parse and queue input for later resolution
        elif command.startswith("output(") and command.endswith(")"):
            self.outputs.append(command)  # Queue output for execution
        elif command.startswith("wait(") and command.endswith(")"):
            self.outputs.append(command)  # Queue wait for execution
        elif command.startswith("loop if(") and command.endswith(")"):
            self.handle_loop(command)  # Handle loop start
        elif command == "finish loop":
            self.finish_loop()  # End loop
        elif command.startswith("not hold"):
            self.not_hold()  # Toggle hold state
        elif command == "end":
            self.end()  # End the program
        elif "=" in command:
            self.assign_variable(command)  # Handle variable assignment
        else:
            raise SyntaxError(f"Unknown command: {command}")

    def handle_loop(self, command):
        """Handles the loop logic."""
        # Extract the condition inside the loop
        condition = command[9:-1].strip()  # Get the condition within the parentheses

        if condition in self.variables and self.variables[condition] == 'true':
            self.hold = True
        else:
            self.hold = False

    def finish_loop(self):
        """Ends the loop and continues the program."""
        self.hold = False

    def not_hold(self):
        """Reverses the value of hold."""
        self.hold = not self.hold

    def queue_input(self, command):
        """Parses and queues a variable for input during execution."""
        if "=" in command:
            var_name, input_call = map(str.strip, command.split("=", 1))
            if not self._is_valid_variable_name(var_name):
                raise SyntaxError(f"Invalid variable name: {var_name}")
            if input_call.startswith("input(\"") and input_call.endswith("\")"):
                prompt = input_call[7:-2].strip()  # Extract prompt text
            else:
                raise SyntaxError(f"Invalid input command: {command}")
        elif command.startswith("input(\"") and command.endswith("\")"):
            var_name = None
            prompt = command[7:-2].strip()
        else:
            raise SyntaxError(f"Invalid input syntax: {command}")
        self.inputs.append((var_name, prompt))

    def resolve_inputs(self):
        """Prompts the user to provide inputs for queued input variables."""
        for var_name, prompt in self.inputs:
            print(prompt)
            user_input = input()
            try:
                value = int(user_input)
            except ValueError:
                value = user_input  # Treat as string if not an integer
            if var_name:
                self.variables[var_name] = value

    def handle_outputs(self):
        """Handles all queued outputs after inputs have been resolved."""
        print("---Execution of code is below---")
        for command in self.outputs:
            if command.startswith("output(") and command.endswith(")"):
                # Handle output command
                value = command[7:-1].strip()
                formatted_value = self.format_string(value)  # Apply variable substitution
                print(formatted_value)  # Output formatted string
            elif command.startswith("wait(") and command.endswith(")"):
                # Handle wait command
                value = command[5:-1].strip()
                self.handle_wait(value)
            else:
                raise SyntaxError(f"Unknown or unsupported command during execution: {command}")

    def evaluate_expression(self, expr):
        """Evaluates arithmetic and string expressions."""
        import ast
        import operator

        # Supported operators
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv
        }

        def _eval(node):
            """Recursively evaluate an AST node."""
            if isinstance(node, ast.BinOp):  # Binary operations (+, -, *, /)
                left = _eval(node.left)
                right = _eval(node.right)
                return ops[type(node.op)](left, right)
            elif isinstance(node, ast.Num):  # Numbers
                return node.n
            elif isinstance(node, ast.Name):  # Variables
                if node.id in self.variables:
                    return self.variables[node.id]
                raise SyntaxError(f"Undefined variable: {node.id}")
            elif isinstance(node, ast.Str):  # Strings
                return node.s
            else:
                raise SyntaxError(f"Unsupported expression: {ast.dump(node)}")

        # Parse the expression
        try:
            tree = ast.parse(expr, mode='eval')
            return _eval(tree.body)
        except Exception as e:
            raise SyntaxError(f"Invalid arithmetic or string expression: {expr}")

    def assign_variable(self, command):
        """Handles variable assignment."""
        if not self.code_running:
            raise RuntimeError("Code has already ended. Use 'end' to restart.")

        var_name, value = map(str.strip, command.split("=", 1))
        if not self._is_valid_variable_name(var_name):
            raise SyntaxError(f"Invalid variable name: {var_name}")

        try:
            self.variables[var_name] = self.evaluate_expression(value)
        except Exception:
            raise SyntaxError(f"Invalid value or expression: {value}")

    def end(self):
        """Ends the code execution."""
        self.code_running = False
        print("---Execution of function is below---")

    def _is_valid_variable_name(self, name):
        """Checks if a variable name is valid (alphanumeric and starts with a letter)."""
        return name.isidentifier()

    def handle_wait(self, value):
        """Handles the wait command."""
        try:
            # Evaluate the value (supports variables or direct values)
            duration = self.evaluate_expression(value)

            if not isinstance(duration, (int, float)):
                raise SyntaxError(f"Invalid duration for wait: {value}")

            print(f"Waiting for {duration} seconds...")
            time.sleep(duration)
        except Exception as e:
            raise SyntaxError(f"Error in wait command: {e}")

    def format_string(self, template):
        """Replaces placeholders in strings with variable values."""
        while "/{" in template and "}/" in template:
            start = template.index("/{") + 2
            end = template.index("}/")
            var_name = template[start:end].strip()
            if var_name in self.variables:
                value = self.variables[var_name]
                template = template.replace(f"/{{{var_name}}}/", str(value), 1)
            else:
                raise SyntaxError(f"Undefined variable in string: {var_name}")
        return template

# SimpliMath Interpreter
if __name__ == "__main__":
    print("Write your code here (type 'end' to finish):")
    user_code = ""
    while True:
        line = input()
        if line.strip() == "end":
            user_code += line + "\n"
            break
        user_code += line + "\n"

    sm = SimpliMath()
    try:
        sm.execute(user_code)
    except Exception as e:
        print(f"Error: {e}")
