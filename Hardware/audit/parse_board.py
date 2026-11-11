import re, sys, json

def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in '()':
            yield c; i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                if s[j] == '\\':
                    buf.append(s[j:j+2]); j += 2; continue
                if s[j] == '"':
                    break
                buf.append(s[j]); j += 1
            yield ('STR', ''.join(buf).replace('\\"', '"'))
            i = j + 1
        else:
            j = i
            while j < n and not s[j].isspace() and s[j] not in '()':
                j += 1
            yield ('SYM', s[i:j])
            i = j

def parse(s):
    stack = [[]]
    for tok in tokenize(s):
        if tok == '(':
            stack.append([])
        elif tok == ')':
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(tok[1])
    return stack[0][0]

def find_all(node, name):
    out = []
    if isinstance(node, list):
        if node and node[0] == name:
            out.append(node)
        for ch in node:
            if isinstance(ch, list):
                out.extend(find_all(ch, name))
    return out

def get(node, name):
    for ch in node:
        if isinstance(ch, list) and ch and ch[0] == name:
            return ch
    return None

def unq(v):
    return v

if __name__ == '__main__':
    s = open(sys.argv[1]).read()
    b = parse(s)
    print('top:', b[0])
    print('n children:', len(b))
    vias = find_all(b, 'via')
    print('vias:', len(vias))
    from collections import Counter
    c = Counter()
    for v in vias:
        net = get(v, 'net')
        c[net[1] if net else '?'] += 1
    print(c.most_common(20))
    fps = find_all(b, 'footprint')
    print('footprints:', len(fps))
    segs = find_all(b, 'segment')
    print('segments:', len(segs))
    print('zones:', len(find_all(b, 'zone')))
    print('arcs:', len(find_all(b, 'arc')))
