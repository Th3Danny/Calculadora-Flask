from flask import Flask, render_template, request, jsonify
from lark import Lark, Transformer, Tree
import ply.lex as lex

app = Flask(__name__)

# Gramática ajustada
grammar = """
    ?start: expr
    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
         | term
    ?term: term "*" factor  -> mul
         | term "/" factor  -> div
         | factor
    ?factor: "-" factor     -> neg
           | "(" expr ")"
           | NUMBER           -> number

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

class CalculateTree(Transformer):
    def add(self, args):
        return args[0] + args[1]
    def sub(self, args):
        return args[0] - args[1]
    def mul(self, args):
        return args[0] * args[1]
    def div(self, args):
        return args[0] / args[1]
    def neg(self, args):
        return -args[0]
    def number(self, args):
        return float(args[0])

parser = Lark(grammar, parser='lalr', transformer=CalculateTree())

tokens = (
    'NUMERO',
    'SUMA',
    'RESTA',
    'MULTIPLICACION',
    'DIVISION',
    'LPAREN',
    'RPAREN'
)

t_SUMA = r'\+'
t_RESTA = r'-'
t_MULTIPLICACION = r'\*'
t_DIVISION = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

def t_NUMERO(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

t_ignore = ' \t'

def t_error(t):
    raise ValueError(f"Token inválido: {t.value[0]}")

lexer = lex.lex()

def analyze_tokens(expression):
    lexer.input(expression)
    tokens_list = []
    total_numbers = 0
    total_operators = 0
    total_integers = 0
    total_decimals = 0

    for token in lexer:
        tokens_list.append(token)
        if token.type == 'NUMERO':
            total_numbers += 1
            if isinstance(token.value, int):
                total_integers += 1
            else:
                total_decimals += 1
        elif token.type in {'SUMA', 'RESTA', 'MULTIPLICACION', 'DIVISION'}:
            total_operators += 1

    return tokens_list, total_numbers, total_operators, total_integers, total_decimals

def generate_tree_json(tree):
    """Convierte el árbol de Lark a un formato JSON jerárquico y traduce los nombres al español."""
    translations = {
        "add": "suma",
        "sub": "resta",
        "mul": "multiplicación",
        "div": "división",
        "neg": "negativo",
        "number": "número"
    }
    if isinstance(tree, Tree):
        return {
            "name": translations.get(tree.data, tree.data),
            "children": [generate_tree_json(child) for child in tree.children]
        }
    else:
        return {"name": str(tree)}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        expression = request.json.get('expression')
        try:
            tokens_list, total_numbers, total_operators, total_integers, total_decimals = analyze_tokens(expression)
            parse_tree = Lark(grammar, parser='lalr').parse(expression)
            result = parser.parse(expression)
            tree_json = generate_tree_json(parse_tree)

            return jsonify({
                "result": result,
                "tokens": [{"tipo": t.type, "valor": t.value} for t in tokens_list],
                "total_tokens": total_numbers + total_operators,
                "total_numeros": total_numbers,
                "total_enteros": total_integers,
                "total_decimales": total_decimals,
                "total_operadores": total_operators,
                "tree_json": tree_json
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
