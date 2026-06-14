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

# def build_graph(formula, G, incoming=None, incoming_label=None, bound_vars=None):
#     if bound_vars is None:
#         bound_vars = {}

#     formula = strip_outer_parens(formula)

#     # 1. Quantifiers
#     q = re.match(r'^(∀|∃)(\w+)\s*(.*)$', formula)
#     if q:
#         quant, var, rest = q.groups()
#         qid = f"{quant}{var}_{uid()}"
#         G.add_node(qid, label=f"{quant}{var}", type="quantifier")

#         # new variable instance
#         var_inst = new_var_instance(var)
#         G.add_node(var_inst, label=var, type="variable")

#         # quantifier binds this instance
#         G.add_edge(qid, var_inst, label="binds")

#         # update bound vars
#         new_bound = bound_vars.copy()
#         new_bound[var] = var_inst

#         # connect quantifier to parent
#         if incoming:
#             G.add_edge(incoming, qid, label=incoming_label)

#         return build_graph(rest.strip(), G, qid, "scope", new_bound)

#     # 2. Negation
#     if formula.startswith("¬"):
#         nid = f"¬_{uid()}"
#         G.add_node(nid, label="¬", type="connective")
#         if incoming:
#             G.add_edge(incoming, nid, label=incoming_label)
#         return build_graph(formula[1:].strip(), G, nid, "negates", bound_vars)

#     # 3. Binary connectives
#     for op in ["→", "∨", "∧"]:
#         parts = split_top_level(formula, op)
#         if parts:
#             left, right = parts
#             # build left and right subgraphs
#             left_node = build_graph(left, G, None, None, bound_vars)
#             right_node = build_graph(right, G, None, None, bound_vars)

#             # connect predicates via edge
#             G.add_edge(left_node, right_node, label=op)

#             # if parent exists, attach the rightmost node upward
#             if incoming:
#                 G.add_edge(incoming, right_node, label=incoming_label)

#             return right_node

#     # 4. Predicate or atom
#     pred, args = parse_predicate(formula)
#     node_id = f"{pred}_{uid()}"
#     G.add_node(node_id, label=pred, type="predicate")

#     if incoming:
#         G.add_edge(incoming, node_id, label=incoming_label)

#     # add arguments
#     for i, arg in enumerate(args):
#         if arg in bound_vars:
#             # create a new instance of the bound variable
#             var_inst = new_var_instance(arg)
#             G.add_node(var_inst, label=arg, type="variable")

#             # connect to predicate
#             G.add_edge(node_id, var_inst, label=f"arg{i+1}")

#             # connect variable instances to show semantic relation
#             G.add_edge(bound_vars[arg], var_inst, label="coexists")

#         else:
#             # constant
#             G.add_node(arg, label=arg, type="constant")
#             G.add_edge(node_id, arg, label=f"arg{i+1}")

#     return node_id

# def tokenize_fol(s: str):
#     token_spec = [
#         (r'\s+', None),
#         (r'∀|∃', 'QUANT'),
#         (r'¬', 'NOT'),
#         (r'∧', 'AND'),
#         (r'∨', 'OR'),
#         (r'→', 'IMPLIES'),
#         (r'↔', 'IFF'),
#         (r'⊕', 'XOR'),
#         (r'\(', 'LPAREN'),
#         (r'\)', 'RPAREN'),
#         (r',', 'COMMA'),
#         (r'[A-Z][A-Za-z0-9_]*', 'PRED'), # Predicates, constants
#         (r'[a-z][A-Za-z0-9_]*', 'VAR'), # Variables
#     ]

#     tokens = []
#     i = 0
#     while i < len(s):
#         #print(s[i])
#         for pattern, tag in token_spec:
#             m = re.match(pattern, s[i:])
#             if m:
#                 if tag:
#                     tokens.append((tag, m.group(0)))
#                 i += len(m.group(0))
#                 break
#         else:
#             raise ValueError(f"Unexpected character: {s[i]}")
#     return tokens

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

# def parse_fol(tokens):
#     tokens = tokens[::-1] # reverse for efficient pop()

#     def peek():
#         return tokens[-1] if tokens else None

#     def pop():
#         return tokens.pop()

#     def parse_expr():
#         tok = peek()

#         # Parenthesized expression
#         if tok and tok[0] == "LPAREN":
#             pop()
#             expr = parse_expr()
#             if pop()[0] != "RPAREN":
#                 raise ValueError("Missing )")
#             return expr

#         # Quantifier
#         if tok and tok[0] == "QUANT":
#             quant = pop()[1]
#             var = parse_atom()
#             body = parse_expr()
#             return ("forall" if quant == "∀" else "exists", var, body)

#         # Unary NOT
#         if tok and tok[0] == "NOT":
#             pop()
#             return ("not", parse_expr())

#         # Parse left side
#         left = parse_atom()

#         # Binary operators
#         tok = peek()
#         if tok and tok[0] in ("AND", "OR", "IMPLIES", "IFF", "XOR"):
#             op_map = {
#                 "AND": "and",
#                 "OR": "or",
#                 "IMPLIES": "implies",
#                 "IFF": "iff",
#                 "XOR": "xor"
#             }
#             op = op_map[pop()[0]]
#             right = parse_expr()
#             return (op, left, right)

#         return left

#     def parse_atom():
#         tok = peek()

#         if tok[0] == "VAR":
#             return pop()[1]

#         if tok[0] == "PRED":
#             name = pop()[1]
#             args = []
#             if peek() and peek()[0] == "LPAREN":
#                 pop()
#                 while True:
#                     args.append(parse_expr())
#                     if peek() and peek()[0] == "COMMA":
#                         pop()
#                         continue
#                     break
#                 if pop()[0] != "RPAREN":
#                     raise ValueError("Missing ) in predicate args")
#             return tuple([name] + args)

#         raise ValueError(f"Unexpected token: {tok}")

#     return parse_expr()

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

# def build_graph_from_ast(expr, G=None, parent=None, edge_type=None, role=None, counter=[0]):
#     if G is None:
#         G = nx.DiGraph()

#     def new_id():
#         counter[0] += 1
#         return f"n{counter[0]}"

#     # Variable or constant
#     if isinstance(expr, str):
#         nid = new_id()
#         ntype = "variable" if expr.islower() else "constant"
#         G.add_node(nid, type=ntype, label=expr)
#         if parent:
#             G.add_edge(parent, nid, type=edge_type, role=role)
#         return nid, G

#     op = expr[0]

#     # Quantifier
#     if op in ("forall", "exists"):
#         nid = new_id()
#         G.add_node(nid, type="quantifier", label=op)

#         var = expr[1]
#         var_id, G = build_graph_from_ast(var, G, parent=nid, edge_type="binding")

#         body = expr[2]
#         body_id, G = build_graph_from_ast(body, G, parent=nid, edge_type="scope")

#         if parent:
#             G.add_edge(parent, nid, type=edge_type, role=role)
#         return nid, G

#     # Connectives (including xor, iff)
#     if op in ("and", "or", "not", "implies", "xor", "iff"):
#         nid = new_id()
#         G.add_node(nid, type="connective", label=op)

#         for child in expr[1:]:
#             child_id, G = build_graph_from_ast(child, G, parent=nid, edge_type="logical")

#         if parent:
#             G.add_edge(parent, nid, type=edge_type, role=role)
#         return nid, G

#     # Predicate
#     nid = new_id()
#     G.add_node(nid, type="predicate", label=op)

#     for i, arg in enumerate(expr[1:]):
#         arg_id, G = build_graph_from_ast(arg, G)
#         G.add_edge(nid, arg_id, type="arg", role=f"arg{i}")

#     if parent:
#         G.add_edge(parent, nid, type=edge_type, role=role)

#     return nid, G


# def build_graph(fol_string: str) -> nx.DiGraph:
#     tokens = tokenize_fol(fol_string)
#     ast = parse_fol(tokens)
#     root, G = build_graph_from_ast(ast)
#     G.nodes[root]["is_root"] = True
#     return G
