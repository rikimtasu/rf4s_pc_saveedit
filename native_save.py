"""Native save-operation seam, reusing the tested binary algorithms without a browser."""
import json
import gzip
from pathlib import Path

from PySide6.QtCore import QObject, Slot
from PySide6.QtQml import QJSEngine

ROOT = Path(__file__).resolve().parent
COMPAT = """
if (!Object.fromEntries) Object.fromEntries = function(entries) { var result={}; for (var entry of entries) Object.defineProperty(result, entry[0], {value:entry[1],enumerable:true,writable:true,configurable:true}); return result; };
if (!Object.hasOwn) Object.hasOwn = function(object,key) { return Object.prototype.hasOwnProperty.call(object,key); };
if (!Array.prototype.at) Object.defineProperty(Array.prototype,'at',{value:function(index){index=Math.trunc(index)||0;return this[index<0?this.length+index:index];}});
if (!Array.prototype.findLastIndex) Object.defineProperty(Array.prototype,'findLastIndex',{value:function(test){for(var i=this.length-1;i>=0;i--)if(test(this[i],i,this))return i;return -1;}});
if (!Array.prototype.flat) Object.defineProperty(Array.prototype,'flat',{value:function(depth){depth=depth===undefined?1:Math.max(0,Math.trunc(depth));var result=[];this.forEach(function(value){if(Array.isArray(value)&&depth>0)result.push.apply(result,value.flat(depth-1));else result.push(value);});return result;}});
if (!String.prototype.replaceAll) Object.defineProperty(String.prototype,'replaceAll',{value:function(from,to){return this.split(from).join(to);}});
var TextDecoder = class { decode(bytes) { return nativeCodec.decode(JSON.stringify(Array.from(bytes))); } };
var TextEncoder = class { encode(text) { return Uint8Array.from(JSON.parse(nativeCodec.encode(text))); } };
"""


class Codec(QObject):
    @Slot(str, result=str)
    def decode(self, text):
        return bytes(json.loads(text)).decode('utf-8', errors='replace')

    @Slot(str, result=str)
    def encode(self, text):
        return json.dumps(list(text.encode('utf-8')))


class NativeSave:
    def __init__(self):
        self._batch = None
        self.engine = QJSEngine()
        self.codec = Codec()
        self.engine.globalObject().setProperty('nativeCodec', self.engine.newQObject(self.codec))
        self._evaluate(COMPAT)
        self._evaluate((ROOT / 'web' / 'native-bundle.js').read_text(encoding='utf-8'), 'native-core')
        self.constants = self.call('constants')

    def _evaluate(self, script, name='native-save'):
        result = self.engine.evaluate(script, name)
        if result.isError():
            raise ValueError(f'{name}: {result.toString()} (line {result.property("lineNumber").toInt()})')
        return result

    def call(self, operation, **args):
        if self._batch is not None and (operation.startswith('set') or operation == 'patchBytes'):
            self._batch.append({'operation': operation, 'args': args})
            return True
        encoded = json.dumps(args, ensure_ascii=True, separators=(',', ':'))
        result = self._evaluate(f'JSON.stringify(RF4SNative.nativeInvoke({json.dumps(operation)}, {encoded}))')
        return json.loads(result.toString())

    def apply_callbacks(self, callbacks):
        """Collect editor writes, then validate/apply them as one atomic undo entry."""
        if self._batch is not None: raise ValueError('An edit batch is already active.')
        self._batch = []
        try:
            for callback in callbacks: callback()
            operations = self._batch
        finally:
            self._batch = None
        return self.call('applyOperations', operations=operations)

    def open(self, data, name):
        return self.call('open', bytes=list(data), name=name)

    def state(self):
        return self.call('state')

    def build(self, **options):
        return bytes(self.call('build', **options))


def local_references():
    bundled = ROOT / 'builtin' / 'references.json.gz'
    if bundled.is_file():
        with gzip.open(bundled, 'rt', encoding='utf-8') as stream: return json.load(stream)
    values = {}
    for key, filename in [('items', 'local-game-data.js'), ('recipes', 'local-save-reference.js'), ('languages', 'local-languages.js')]:
        path = ROOT / 'web' / filename
        if path.is_file():
            text = path.read_text(encoding='utf-8')
            values[key] = json.loads(text.split('=', 1)[1].strip().removesuffix(';'))
    return {key: value for key, value in values.items() if value is not None}
