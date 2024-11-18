from flask import Flask, render_template, request
from lark import Lark, Transformer, Tree

app = Flask(__name__)

# Definición de la gramática para manejar n números con soporte para decimales
grammar = """
    ?start: expr
    ?expr: expr "+" term   -> add
         | expr "-" term   -> sub
         | term
    ?term: term "*" factor  -> mul
         | term "/" factor  -> div
         | factor
    ?factor: "(" expr ")"
           | NUMBER           -> number

    %import common.CNAME
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
    def number(self, args):
        return float(args[0])

# Configuración del parser
parser = Lark(grammar, parser='lalr', transformer=CalculateTree())

# Función para construir el árbol de análisis sin evaluar la expresión
def get_parse_tree(expression):
    raw_tree = Lark(grammar, parser='lalr').parse(expression)  # Genera el árbol sin transformar
    return transform_tree_to_spanish(raw_tree)

# Función para transformar el árbol a términos en español
def transform_tree_to_spanish(tree):
    tree_str = tree.pretty()
    translations = {
        "add": "suma",
        "sub": "resta",
        "mul": "multiplicación",
        "div": "división",
        "number": "número"
    }
    for eng, esp in translations.items():
        tree_str = tree_str.replace(eng, esp)
    return tree_str

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    parse_tree = None
    if request.method == 'POST':
        expression = request.form.get('expression')
        try:
            # Construir el árbol de análisis
            parse_tree = get_parse_tree(expression)
            # Evaluar la expresión usando el transformer
            result = parser.parse(expression)
        except Exception as e:
            result = f"Error: {e}"
            parse_tree = "No se pudo construir el árbol debido a un error."
    return render_template('index.html', result=result, parse_tree=parse_tree)

if __name__ == '__main__':
    app.run(debug=True)
