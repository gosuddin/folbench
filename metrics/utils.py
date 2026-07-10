from networkx.algorithms.flow import networksimplex
import networkx as nx
import re
import uuid

def uid():
    return uuid.uuid4().hex[:6]

def new_var_instance(var):
    """Create a unique variable instance node."""
    return f"{var}_{uid()}"

def strip_outer_parens(s):
    s = s.strip()
    if not (s.startswith("(") and s.endswith(")")):
        return s
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if depth == 0 and i < len(s) - 1:
            return s
    return s[1:-1].strip()

def split_top_level(formula, operator):
    depth = 0
    L = len(operator)
    for i in range(len(formula)):
        if formula[i] == "(":
            depth += 1
        elif formula[i] == ")":
            depth -= 1
        elif depth == 0 and formula[i:i+L] == operator:
            return formula[:i].strip(), formula[i+L:].strip()
    return None

def parse_predicate(formula):
    m = re.match(r'^(\w+)\((.*)\)$', formula)
    if not m:
        return formula, []
    pred, args_str = m.groups()

    args = []
    depth = 0
    current = ""
    for ch in args_str:
        if ch == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
    if current.strip():
        args.append(current.strip())

    return pred, args

def tokenize_fol(s: str):
    token_spec = [
        (r'\s+', None),
        (r'∀|∃', 'QUANT'),
        (r'¬', 'NOT'),
        (r'∧', 'AND'),
        (r'∨', 'OR'),
        (r'→', 'IMPLIES'),
        (r'↔', 'IFF'),
        (r'⊕', 'XOR'),
        (r'\(', 'LPAREN'),
        (r'\)', 'RPAREN'),
        (r',', 'COMMA'),
        # ASCII fallbacks
        (r'forall|exists', 'QUANT'),
        (r'not', 'NOT'),
        (r'and', 'AND'),
        (r'or', 'OR'),
        (r'implies', 'IMPLIES'),
        (r'iff', 'IFF'),
        (r'xor', 'XOR'),
        # Predicates & constants
        (r'[A-Z][A-Za-z0-9_]*', 'PRED'),
        # Variables
        (r'[a-z][A-Za-z0-9_]*', 'VAR'),
    ]

    tokens = []
    i = 0
    while i < len(s):
        for pattern, tag in token_spec:
            m = re.match(pattern, s[i:])
            if m:
                if tag:
                    tokens.append((tag, m.group(0)))
                i += len(m.group(0))
                break
        else:
            raise ValueError(f"Unexpected character: {s[i]}")
    return tokens


def parse_fol(tokens):
    tokens = tokens[::-1] # reverse for efficient pop()

    def peek():
        return tokens[-1] if tokens else None

    def pop():
        return tokens.pop()

    # -----------------------------
    # Recursive descent with precedence
    # -----------------------------

    def parse_primary():
        tok = peek()

        # Parenthesized expression
        if tok and tok[0] == "LPAREN":
            pop()
            expr = parse_iff()
            if pop()[0] != "RPAREN":
                raise ValueError("Missing )")
            return expr

        # Quantifier
        if tok and tok[0] == "QUANT":
            quant = pop()[1]
            var = parse_primary()
            body = parse_primary()
            return ("forall" if quant in ("∀", "forall") else "exists", var, body)

        # NOT
        if tok and tok[0] == "NOT":
            pop()
            return ("not", parse_primary())

        # Variable or predicate
        return parse_atom()

    def parse_atom():
        tok = peek()

        if tok[0] == "VAR":
            return pop()[1]

        if tok[0] == "PRED":
            name = pop()[1]
            args = []
            if peek() and peek()[0] == "LPAREN":
                pop()
                while True:
                    args.append(parse_iff())
                    if peek() and peek()[0] == "COMMA":
                        pop()
                        continue
                    break
                if pop()[0] != "RPAREN":
                    raise ValueError("Missing ) in predicate args")
            return tuple([name] + args)

        raise ValueError(f"Unexpected token: {tok}")

    # -----------------------------
    # Precedence climbing
    # -----------------------------

    def parse_and():
        left = parse_primary()
        while peek() and peek()[0] == "AND":
            pop()
            right = parse_primary()
            left = ("and", left, right)
        return left

    def parse_or():
        left = parse_and()
        while peek() and peek()[0] == "OR":
            pop()
            right = parse_and()
            left = ("or", left, right)
        return left

    def parse_xor():
        left = parse_or()
        while peek() and peek()[0] == "XOR":
            pop()
            right = parse_or()
            left = ("xor", left, right)
        return left

    def parse_implies():
        left = parse_xor()
        while peek() and peek()[0] == "IMPLIES":
            pop()
            right = parse_xor()
            left = ("implies", left, right)
        return left

    def parse_iff():
        left = parse_implies()
        while peek() and peek()[0] == "IFF":
            pop()
            right = parse_implies()
            left = ("iff", left, right)
        return left

    return parse_iff()

def build_graph_from_ast(expr, G=None, parent=None, edge_type=None, role=None, counter=[0]):
    if G is None:
        G = nx.DiGraph()

    def new_id():
        counter[0] += 1
        return f"n{counter[0]}"

    # Variable or constant
    if isinstance(expr, str):
        nid = new_id()
        ntype = "variable" if expr.islower() else "constant"
        G.add_node(nid, type=ntype, label=expr)
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    op = expr[0]

    # Quantifier
    if op in ("forall", "exists"):
        nid = new_id()
        G.add_node(nid, type="quantifier", label=op)

        var = expr[1]
        var_id, G = build_graph_from_ast(var, G, parent=nid, edge_type="binding")

        body = expr[2]
        body_id, G = build_graph_from_ast(body, G, parent=nid, edge_type="scope")

        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Connectives
    if op in ("and", "or", "not", "implies", "xor", "iff"):
        nid = new_id()
        G.add_node(nid, type="connective", label=op)

        for child in expr[1:]:
            child_id, G = build_graph_from_ast(child, G, parent=nid, edge_type="logical")

        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Predicate
    nid = new_id()
    G.add_node(nid, type="predicate", label=op)

    for i, arg in enumerate(expr[1:]):
        arg_id, G = build_graph_from_ast(arg, G)
        G.add_edge(nid, arg_id, type="arg", role=f"arg{i}")

    if parent:
        G.add_edge(parent, nid, type=edge_type, role=role)

    return nid, G


def build_graph(fol_string: str) -> nx.DiGraph:
    tokens = tokenize_fol(fol_string)
    ast = parse_fol(tokens)
    root, G = build_graph_from_ast(ast)
    G.nodes[root]["is_root"] = True
    return G

def tokenize_fol_2(s: str):
    token_spec = [
        (r'\s+', None),

        # Quantifiers
        (r'∀|∃', 'QUANT'),
        (r'forall|exists', 'QUANT'),

        # Logical operators
        (r'\¬', 'NOT'),
        (r'\∧', 'AND'),
        (r'\∨', 'OR'),
        (r'\→', 'IMPLIES'),
        (r'\↔', 'IFF'),
        (r'\⟷', 'IFF'),
        (r'\⊕', 'XOR'),
        (r'not', 'NOT'),
        (r'and', 'AND'),
        (r' or ', 'OR'),
        (r'implies', 'IMPLIES'),
        (r'iff', 'IFF'),
        (r'xor', 'XOR'),

        # Equality
        (r'=', 'EQ'),
        (r'!=|≠', 'NEQ'),

        # Parentheses + comma
        (r'\(', 'LPAREN'),
        (r'\)', 'RPAREN'),
        (r',', 'COMMA'),

        # Quoted strings → treat as constants
        (r'"[^"]*"', 'STRING'),

        # Numbers → convert to numXXXX
        (r'\d+', 'NUMBER'),

        # Predicates (uppercase)
        (r'[A-Z][A-Za-z0-9_.-]*', 'PRED'),

        # Lowercase constants (multi‑char)
        (r'[a-z][a-zA-Z0-9_.-]+', 'CONST'),

        # Variables (single lowercase letter)
        (r'[a-zA-Z]', 'VAR'),

    ]

    tokens = []
    i = 0
    while i < len(s):
        for pattern, tag in token_spec:
            m = re.match(pattern, s[i:])
            if m:
                if tag:
                    tokens.append((tag, m.group(0)))
                i += len(m.group(0))
                break
        else:
            raise ValueError(f"Unexpected character: {s[i]}")
    return tokens
    
def merge_constants_in_args(tokens):
    merged = []
    i = 0

    while i < len(tokens):
        tag, val = tokens[i]

        # Only merge inside predicate argument lists
        if tag == "CONST":
            new_val = val
            j = i + 1

            # Merge following CONST or NUMBER tokens
            while j < len(tokens) and tokens[j][0] in ("CONST", "NUMBER"):
                new_val += tokens[j][1]
                j += 1

            merged.append(("CONST", new_val))
            i = j
            continue

        merged.append((tag, val))
        i += 1

    return merged
    
def parse_fol_2(tokens):
    tokens = tokens[::-1]

    def peek(): return tokens[-1] if tokens else None
    def pop(): return tokens.pop()

    def parse_primary():
        tok = peek()

        # Parenthesized expression
        if tok and tok[0] == "LPAREN":
            pop()
            expr = parse_iff()
            if pop()[0] != "RPAREN":
                raise ValueError("Missing )")
            return expr

        # Quantifier
        if tok and tok[0] == "QUANT":
            quant = pop()[1]
            var = parse_primary()
            body = parse_primary()
            return ("forall" if quant in ("∀", "forall") else "exists", var, body)

        # NOT
        if tok and tok[0] == "NOT":
            pop()
            return ("not", parse_primary())

        return parse_atom()
    
    def parse_atom():
        tok = peek()
    
        # Variables
        if tok[0] == "VAR":
            return pop()[1]
    
        # Constants
        if tok[0] == "CONST":
            return pop()[1]
    
        # Numbers
        if tok[0] == "NUMBER":
            return "num" + pop()[1]
    
        # Strings
        if tok[0] == "STRING":
            val = pop()[1][1:-1]
            return val
    
        # Predicates
        if tok[0] == "PRED":
            name = pop()[1]
            args = []
            if peek() and peek()[0] == "LPAREN":
                pop()  # '('
    
                # ---- first argument: parsed normally ----
                if peek() and peek()[0] != "RPAREN":
                    first_arg = parse_iff()
                    args.append(first_arg)
    
                # ---- remaining stuff: merged into one constant ----
                rest_tokens = []
                while peek() and peek()[0] != "RPAREN":
                    tag, val = pop()
                    if tag in ("COMMA",):
                        continue
                    rest_tokens.append(val)
    
                if rest_tokens:
                    merged = "".join(rest_tokens)
                    args.append(merged)
    
                if not peek() or pop()[0] != "RPAREN":
                    raise ValueError("Missing ) in predicate args")
    
            return tuple([name] + args)

    # Precedence climbing
    def parse_eq():
        left = parse_primary()
        while peek() and peek()[0] in ("EQ", "NEQ"):
            op = pop()[0]
            op = "=" if op == "EQ" else "!="
            right = parse_primary()
            left = (op, left, right)
        return left

    def parse_and():
        left = parse_eq()
        while peek() and peek()[0] == "AND":
            pop()
            right = parse_eq()
            left = ("and", left, right)
        return left

    def parse_or():
        left = parse_and()
        while peek() and peek()[0] == "OR":
            pop()
            right = parse_and()
            left = ("or", left, right)
        return left

    def parse_xor():
        left = parse_or()
        while peek() and peek()[0] == "XOR":
            pop()
            right = parse_or()
            left = ("xor", left, right)
        return left

    def parse_implies():
        left = parse_xor()
        while peek() and peek()[0] == "IMPLIES":
            pop()
            right = parse_xor()
            left = ("implies", left, right)
        return left

    def parse_iff():
        left = parse_implies()
        while peek() and peek()[0] == "IFF":
            pop()
            right = parse_implies()
            left = ("iff", left, right)
        return left

    return parse_iff()

def build_graph_from_ast_2(expr, G=None, parent=None, edge_type=None, role=None, counter=[0]):

    if G is None:
        G = nx.DiGraph()

    def new_id():
        counter[0] += 1
        return f"n{counter[0]}"

    # Variable or constant
    if isinstance(expr, str):
        nid = new_id()
        ntype = "variable" if expr.islower() and len(expr) == 1 else "constant"
        G.add_node(nid, type=ntype, label=expr)
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    op = expr[0]

    # Quantifier
    if op in ("forall", "exists"):
        nid = new_id()
        G.add_node(nid, type="quantifier", label=op)

        var = expr[1]
        build_graph_from_ast_2(var, G, parent=nid, edge_type="binding")

        body = expr[2]
        build_graph_from_ast_2(body, G, parent=nid, edge_type="scope")

        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Connectives
    if op in ("and", "or", "not", "implies", "xor", "iff"):
        nid = new_id()
        G.add_node(nid, type="connective", label=op)
        for child in expr[1:]:
            build_graph_from_ast_2(child, G, parent=nid, edge_type="logical")
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Equality / inequality
    if op in ("=", "!="):
        nid = new_id()
        G.add_node(nid, type="predicate", label=op)
        build_graph_from_ast_2(expr[1], G, parent=nid, edge_type="arg", role="arg0")
        build_graph_from_ast_2(expr[2], G, parent=nid, edge_type="arg", role="arg1")
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Predicate
    nid = new_id()
    G.add_node(nid, type="predicate", label=op)
    for i, arg in enumerate(expr[1:]):
        build_graph_from_ast_2(arg, G, parent=nid, edge_type="arg", role=f"arg{i}")
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
    return nid, G

def build_graph_2(fol_string: str) -> nx.DiGraph:
    tokens = tokenize_fol_2(fol_string)
    tokens = merge_constants_in_args(tokens)
    ast = parse_fol_2(tokens)
    root, G = build_graph_from_ast_2(ast)
    G.nodes[root]["is_root"] = True
    return G