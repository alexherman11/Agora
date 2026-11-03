"""Imported policy code diagnostics. Live code replacement is unsupported.

No source reads, native observations, lease operations, staging, class swaps,
or background keepalive. Snapshot before the Manager can acquire a lease.
"""
import hashlib
import json
import sys
from types import CodeType, FunctionType


REFUSAL = ('WM hot reload/rollback unavailable: the existing watchdog cannot '
           'bound a stalled handoff; a separately authorized WM-only lifecycle '
           'with geometry/claim release is required')
CLASSES = {'manager.py': 'Manager', 'win32_host.py': 'Native'}


def code_digest(code):
    """Hash real code, including nested code; normalize only checkout paths."""
    data = json.dumps(code_record(code), sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(data.encode()).hexdigest()


def constant_record(value):
    if isinstance(value, CodeType):
        return ['code', code_record(value)]
    if type(value) in (tuple, frozenset):
        items = [constant_record(v) for v in value]
        if type(value) is frozenset:
            items.sort(key=lambda v: json.dumps(v, sort_keys=True))
        return [type(value).__name__, items]
    if type(value) in (str, bytes, int, float, complex, bool, type(None)) or value is Ellipsis:
        return [type(value).__name__, repr(value)]
    raise ValueError('unsupported code constant')


def code_record(code):
    # Structural encoding avoids marshal's object-sharing/interning differences.
    fields = ('co_name', 'co_qualname', 'co_argcount', 'co_posonlyargcount',
              'co_kwonlyargcount', 'co_nlocals', 'co_stacksize', 'co_flags',
              'co_firstlineno', 'co_names', 'co_varnames', 'co_freevars', 'co_cellvars')
    result = {name: getattr(code, name) for name in fields}
    for name in ('co_code', 'co_linetable', 'co_exceptiontable'):
        result[name] = getattr(code, name).hex()
    result['co_consts'] = [constant_record(c) for c in code.co_consts]
    return result


def runtime_manifest(modules):
    """Local top-level functions and Manager/Native direct method code only.

    No source lookup or execution. This is code identity, not an attestation of
    defaults, globals, imports, native DLLs or all other live process state.
    """
    result = {}
    for label, module in modules.items():
        for name, value in vars(module).items():
            if isinstance(value, FunctionType) and value.__module__ == module.__name__:
                result[label + ':' + name] = code_digest(value.__code__)
        cls = vars(module).get(CLASSES[label])
        if not isinstance(cls, type):
            raise ValueError('policy class unavailable')
        for name, value in vars(cls).items():
            if isinstance(value, FunctionType):
                result[label + ':' + cls.__name__ + '.' + name] = code_digest(value.__code__)
    return result


def compiled_manifest(sources):
    """Offline House comparison; compile supplied bytes without executing them.

    Caller supplies reviewed bytes. Never invoked by WM hello/tick/call.
    Same Python version/optimization and exact line layout are required.
    """
    result = {}
    for label, data in sources.items():
        root = compile(data, label, 'exec', dont_inherit=True,
                       optimize=sys.flags.optimize)
        for code in root.co_consts:
            if not isinstance(code, CodeType):
                continue
            if code.co_name == CLASSES[label]:
                for method in code.co_consts:
                    if isinstance(method, CodeType):
                        result[label + ':' + code.co_name + '.' + method.co_name] = code_digest(method)
            else:
                # Other classes are outside the declared code scope.
                if code.co_flags & 2:  # CO_NEWLOCALS: function, not a class body
                    result[label + ':' + code.co_name] = code_digest(code)
    return result


class PolicyStatus:
    def __init__(self, manager_module, native_module):
        manifest = runtime_manifest({'manager.py': manager_module,
                                     'win32_host.py': native_module})
        self.manifest = tuple(sorted(manifest.items()))
        h = hashlib.sha256()
        for name, sha in self.manifest:
            h.update(name.encode() + b'\0' + sha.encode() + b'\n')
        self.runtime_code_sha256 = h.hexdigest()
        self.python_cache_tag = sys.implementation.cache_tag
        self.optimization = sys.flags.optimize

    def reading(self):
        return {'text': 'Startup imported policy code snapshot; hot reload unavailable',
                'rows': [{'runtime_code_sha256': self.runtime_code_sha256,
                          'code_manifest': dict(self.manifest),
                          'python_cache_tag': self.python_cache_tag,
                          'optimization': self.optimization,
                          'provenance': 'startup imported code objects; scoped, not full process attestation',
                          'reload_supported': False, 'rollback_supported': False}]}
