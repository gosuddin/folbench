import networkx as nx
import re

def tokenize_fol(s: str):
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
    
def parse_fol(tokens):
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

def build_graph_from_ast(expr, G=None, parent=None, edge_type=None, role=None, counter=[0]):

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
        build_graph_from_ast(var, G, parent=nid, edge_type="binding")

        body = expr[2]
        build_graph_from_ast(body, G, parent=nid, edge_type="scope")

        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Connectives
    if op in ("and", "or", "not", "implies", "xor", "iff"):
        nid = new_id()
        G.add_node(nid, type="connective", label=op)
        for child in expr[1:]:
            build_graph_from_ast(child, G, parent=nid, edge_type="logical")
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Equality / inequality
    if op in ("=", "!="):
        nid = new_id()
        G.add_node(nid, type="predicate", label=op)
        build_graph_from_ast(expr[1], G, parent=nid, edge_type="arg", role="arg0")
        build_graph_from_ast(expr[2], G, parent=nid, edge_type="arg", role="arg1")
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
        return nid, G

    # Predicate
    nid = new_id()
    G.add_node(nid, type="predicate", label=op)
    for i, arg in enumerate(expr[1:]):
        build_graph_from_ast(arg, G, parent=nid, edge_type="arg", role=f"arg{i}")
        if parent:
            G.add_edge(parent, nid, type=edge_type, role=role)
    return nid, G

def build_graph(fol_string: str) -> nx.DiGraph:
    tokens = tokenize_fol(fol_string)
    tokens = merge_constants_in_args(tokens)
    ast = parse_fol(tokens)
    root, G = build_graph_from_ast(ast)
    G.nodes[root]["is_root"] = True
    return G