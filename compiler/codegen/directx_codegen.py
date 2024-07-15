from ..ast import (
    ShaderNode,
    AssignmentNode,
    FunctionNode,
    ReturnNode,
    BinaryOpNode,
    IfNode,
    ForNode,
    VariableNode,
    FunctionCallNode,
    MemberAccessNode,
)


class HLSLCodeGen:
    def generate(self, ast):
        if isinstance(ast, ShaderNode):
            return self.generate_shader(ast)
        return ""

    def generate_shader(self, node):
        code = "struct VS_INPUT {\n"
        for i, (vtype, name) in enumerate(node.inputs):
            code += f"    {self.map_type(vtype)} {name} : POSITION{i};\n"
        code += "};\n\n"

        code += "struct PS_OUTPUT {\n"
        for i, (vtype, name) in enumerate(node.outputs):
            code += f"    {self.map_type(vtype)} {name} : SV_TARGET{i};\n"
        code += "};\n\n"

        for function in node.functions:
            code += self.generate_function(function) + "\n"
        return code

    def generate_function(self, node):
        if node.name == "main":
            params = "VS_INPUT input"
            return_type = "PS_OUTPUT"
        else:
            params = ", ".join(
                f"{self.map_type(param[0])} {param[1]}" for param in node.params
            )
            return_type = self.map_type(node.return_type)

        code = f"{return_type} {node.name}({params}) {{\n"
        if node.name == "main":
            code += "    PS_OUTPUT output;\n"
        for stmt in node.body:
            code += self.generate_statement(stmt, 1)
        if node.name == "main":
            code += "    return output;\n"
        code += "}\n"
        return code

    def generate_statement(self, stmt, indent=0):
        indent_str = "    " * indent
        if isinstance(stmt, AssignmentNode):
            return f"{indent_str}{self.generate_assignment(stmt)};\n"
        elif isinstance(stmt, IfNode):
            return self.generate_if(stmt, indent)
        elif isinstance(stmt, ForNode):
            return self.generate_for(stmt, indent)
        elif isinstance(stmt, ReturnNode):
            return f"{indent_str}return {self.generate_expression(stmt.value)};\n"
        else:
            return f"{indent_str}{self.generate_expression(stmt)};\n"

    def generate_assignment(self, node):
        if isinstance(node.name, VariableNode) and node.name.vtype:
            return f"{self.map_type(node.name.vtype)} {node.name.name} = {self.generate_expression(node.value)}"
        else:
            return f"{self.generate_expression(node.name)} = {self.generate_expression(node.value)}"

    def generate_if(self, node, indent):
        indent_str = "    " * indent
        code = f"{indent_str}if ({self.generate_expression(node.condition)}) {{\n"
        for stmt in node.if_body:
            code += self.generate_statement(stmt, indent + 1)
        code += f"{indent_str}}}"
        if node.else_body:
            code += " else {\n"
            for stmt in node.else_body:
                code += self.generate_statement(stmt, indent + 1)
            code += f"{indent_str}}}"
        code += "\n"
        return code

    def generate_for(self, node, indent):
        indent_str = "    " * indent

        if isinstance(node.init, AssignmentNode) and isinstance(
            node.init.name, VariableNode
        ):
            init = f"{self.map_type(node.init.name.vtype)} {node.init.name.name} = {self.generate_expression(node.init.value)}"
        else:
            init = self.generate_statement(node.init, 0).strip()[
                :-1
            ]  # Remove trailing semicolon

        condition = self.generate_expression(node.condition)
        update = self.generate_statement(node.update, 0).strip()[
            :-1
        ]  # Remove trailing semicolon

        code = f"{indent_str}for ({init}; {condition}; {update}) {{\n"
        for stmt in node.body:
            code += self.generate_statement(stmt, indent + 1)
        code += f"{indent_str}}}\n"
        return code

    def generate_expression(self, expr):
        if isinstance(expr, str):
            return expr
        elif isinstance(expr, VariableNode):
            return expr.name
        elif isinstance(expr, BinaryOpNode):
            return f"({self.generate_expression(expr.left)} {self.map_operator(expr.op)} {self.generate_expression(expr.right)})"
        elif isinstance(expr, FunctionCallNode):
            args = ", ".join(self.generate_expression(arg) for arg in expr.args)
            return f"{expr.name}({args})"
        elif isinstance(expr, MemberAccessNode):
            return f"{self.generate_expression(expr.object)}.{expr.member}"
        else:
            return str(expr)

    def map_type(self, vtype):
        type_mapping = {
            "void": "void",
            "vec2": "float2",
            "vec3": "float3",
            "vec4": "float4",
            "mat2": "float2x2",
            "mat3": "float3x3",
            "mat4": "float4x4",
            "sampler2D": "Texture2D",
        }
        return type_mapping.get(vtype, vtype)

    def map_operator(self, op):
        op_map = {
            "PLUS": "+",
            "MINUS": "-",
            "MULTIPLY": "*",
            "DIVIDE": "/",
            "LESS_THAN": "<",
            "GREATER_THAN": ">",
            "LESS_EQUAL": "<=",
            "GREATER_EQUAL": ">=",
            "EQUAL": "==",
            "NOT_EQUAL": "!=",
            "AND": "&&",
            "OR": "||",
        }
        return op_map.get(op, op)


# Usage example
if __name__ == "__main__":
    from compiler.lexer import Lexer
    from compiler.parser import Parser

    code = "shader main { input vec3 position; output vec4 color; void main() { color = vec4(position, 1.0); } }"
    lexer = Lexer(code)
    parser = Parser(lexer.tokens)
    ast = parser.parse()

    codegen = HLSLCodeGen()
    hlsl_code = codegen.generate(ast)
    print(hlsl_code)
