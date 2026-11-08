"""Generate the local schema from the pinned Venti structs and override handlers."""
import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor' / 'venti' / 'src' / 'rf'
COMMIT = '6588b5ff7c28ddd82fd5b2a4591486af3e9c901a'


def enum_value(expression, names):
    node = ast.parse(expression, mode='eval').body

    def evaluate(value):
        if isinstance(value, ast.Constant) and isinstance(value.value, int):
            return value.value
        if isinstance(value, ast.Name):
            return names[value.id]
        if isinstance(value, ast.BinOp):
            left, right = evaluate(value.left), evaluate(value.right)
            if isinstance(value.op, ast.BitOr):
                return left | right
            if isinstance(value.op, ast.LShift):
                return left << right
        raise ValueError(f'Unsupported enum expression: {expression}')

    return evaluate(node)


def main():
    enums = {}
    structs = {}
    for path in sorted(SOURCE.glob('*.h')):
        text = path.read_text(encoding='utf-8')
        for match in re.finditer(r'enum class (\w+) : (u?int\d+_t)\s*\{(.*?)\};', text, re.S):
            name, underlying, body = match.groups()
            values = {}
            for line in body.splitlines():
                entry = re.match(r'\s*(\w+)\s*=\s*([^,]+),?', line.split('//')[0])
                if entry:
                    values[entry[1]] = enum_value(entry[2].strip(), values)
            enums[name] = {'underlying': underlying, 'values': values}
        for match in re.finditer(r'struct (\w+)\s*\{', text):
            name = match[1]
            size_match = re.search(rf'static_assert\(sizeof\({name}\) == (0x[\da-fA-F]+|\d+)\)', text)
            if not size_match:
                continue
            depth = 1
            offset = 0
            alignment = 1
            members = {}
            comments = []
            for line in text[match.end():].splitlines():
                if depth == 1:
                    if line.strip().startswith('//'):
                        comments.append(line.strip()[2:].strip())
                    member = re.match(r'\s*(std::array<\s*\w+\s*,\s*\d+\s*>|\w+)\s+(\w+)\s*;\s*(?://\s*(.*))?$', line)
                    if member:
                        kind, field, inline = member.groups()
                        array = re.fullmatch(r'std::array<\s*(\w+)\s*,\s*(\d+)\s*>', kind)
                        length = int(array[2]) if array else 0
                        element = array[1] if array else kind
                        primitive = enums.get(element, {}).get('underlying', element)
                        primitive_match = re.fullmatch(r'(u?)int(8|16|32)_t', primitive)
                        if not primitive_match:
                            raise ValueError(f'Unsupported member {name}.{field}: {kind}')
                        unsigned, bits = primitive_match.groups()
                        bits = int(bits)
                        element_size = bits // 8
                        alignment = max(alignment, element_size)
                        offset = (offset + element_size - 1) // element_size * element_size
                        members[field] = {
                            'offset': offset, 'bits': bits, 'signed': not bool(unsigned),
                            'min': 0 if unsigned else -(2 ** (bits - 1)),
                            'max': 2 ** bits - 1 if unsigned else 2 ** (bits - 1) - 1,
                            'length': length, 'description': ' '.join(comments + ([inline] if inline else [])),
                        }
                        if element in enums:
                            members[field]['enum'] = enums[element]['values']
                            members[field]['bitmask'] = 'Flags' in element
                        offset += element_size * (length or 1)
                        comments = []
                    elif line.strip() and not line.strip().startswith('//'):
                        comments = []
                depth += line.split('//')[0].count('{') - line.split('//')[0].count('}')
                if depth == 0:
                    break
            size = (offset + alignment - 1) // alignment * alignment
            expected = int(size_match[1], 0)
            if size != expected:
                raise ValueError(f'{name}: computed size {size}, upstream asserts {expected}')
            structs[name] = {'members': members, 'size': size, 'source': f'src/rf/{path.name}'}

    tables = {}
    functions = {}
    for path in sorted((SOURCE / 'overrides').glob('*_override.cpp')):
        text = path.read_text(encoding='utf-8')
        match = re.search(r'apply_all_overrides<(\w+)>\(config, (\w+), mods, "(\w+)"', text)
        if not match:
            raise ValueError(f'Unrecognized handler {path}')
        struct, apply, key = match.groups()
        fields = {}
        for field_match in re.finditer(r'read_override\((?:node|tbl), "(\w+)", record\.(\w+)\);', text):
            field, member = field_match.groups()
            fields[field] = dict(structs[struct]['members'][member])
        for field in re.findall(r'read_nibble_override\(node, "(\w+)"', text):
            fields[field] = {
                **structs[struct]['members']['rarity_max_stack'],
                'min': 0, 'max': 15, 'shift': 4 if field == 'rarity' else 0,
                'description': f'{field.replace("_", " ").capitalize()}, from 0 to 15; one packed nibble.',
            }
        group_match = re.search(r'k\w+GroupNames\s*=.*?\(\{(.*?)\}\)', text, re.S)
        groups = re.findall(r'"(\w+)"', group_match[1]) if group_match else []
        tables[key] = {
            'struct': struct, 'source': structs[struct]['source'],
            'handler': f'src/rf/overrides/{path.name}', 'size': structs[struct]['size'],
            'fields': fields, 'groups': groups, 'variants': [],
        }
        functions[apply.replace('apply_', 'apply_all_', 1)] = key

    hook = (ROOT / 'vendor' / 'venti' / 'src' / 'hooks' / 'config_data_hook.cpp').read_text(encoding='utf-8')
    for match in re.finditer(r'case (\d+):\s*// ([^\n]+)\n\s*return make_applier\((\w+)(?:, ("\w+"|true))?\);', hook):
        index, filename, function, argument = match.groups()
        key = functions[function]
        tables[key]['variants'].append({
            'sub': argument.strip('"') if argument and argument != 'true' else '',
            'file': filename.strip(), 'archiveIndex': int(index), 'raw': argument == 'true',
        })
    for key, table in tables.items():
        if not table['fields'] or not table['variants']:
            raise ValueError(f'Incomplete schema for {key}')
    content = 'export const VENTI_COMMIT = ' + json.dumps(COMMIT) + ';\n'
    content += 'export const VENTI_TABLES = ' + json.dumps(tables, ensure_ascii=False, indent=2) + ';\n'
    names = json.loads((ROOT / 'vendor' / 'rf4-modkit' / 'rf4s_item_names.json').read_text(encoding='utf-8'))
    content += 'export const ITEM_NAMES = ' + json.dumps(names, ensure_ascii=False, indent=2) + ';\n'
    (ROOT / 'web' / 'game-schema.js').write_text(content, encoding='utf-8')
    (ROOT / 'vendor' / 'venti' / 'schema.json').write_text(json.dumps(tables, indent=2), encoding='utf-8')
    print(f'Generated {len(tables)} types, {sum(len(t["fields"]) for t in tables.values())} fields, '
          f'{sum(len(t["variants"]) for t in tables.values())} file variants. All struct sizes match upstream assertions.')


if __name__ == '__main__':
    main()
