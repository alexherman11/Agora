"""WM-thread-only policy handoff. No process replacement, lease transfer or release.

Only Manager policy and Native.windows may change. Constructors, native safety,
imports, engine, controller and watchdog must retain their startup bytes/ABI.
Source hashes identify reviewed bytes; they do not confer review or authority.
"""
import ast
from copy import copy
import hashlib
from pathlib import Path
import re
import threading
import time


POLICY = ('manager.py', 'win32_host.py')
FIXED = ('engine.py', 'feel.py', 'watchdog.py', 'wm_module.py', 'policy_reload.py',
         '../kernel-desktop/modproto.py')
MAX_SOURCE_BYTES = 256_000


def digest(sources):
    h = hashlib.sha256()
    for name, data in sorted(sources.items()):
        h.update(name.encode() + b'\0' + len(data).to_bytes(8, 'big') + data)
    return h.hexdigest()


def shape(node):
    return ast.dump(node, include_attributes=False)


def inert_definition(node):
    """Staging defines code only; no decorators/default expressions execute."""
    if isinstance(node, ast.ClassDef):
        for member in node.body:
            if isinstance(member, ast.FunctionDef):
                inert_definition(member)
            elif not (isinstance(member, ast.Expr) and
                      isinstance(member.value, ast.Constant) and isinstance(member.value.value, str)):
                raise PermissionError('class initialization is outside policy reload')
        return
    if (node.decorator_list or node.returns or
            any(a.annotation for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs) or
            (node.args.vararg and node.args.vararg.annotation) or
            (node.args.kwarg and node.args.kwarg.annotation)):
        raise PermissionError('decorators/annotations are outside policy reload')
    for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
        try:ast.literal_eval(default)
        except (ValueError, TypeError):
            raise PermissionError('executable defaults are outside policy reload') from None


def definitions(data, filename):
    tree = ast.parse(data, filename)
    selected, frozen = [], []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # Only the monitor classifier is reloadable on the native boundary.
            (selected if filename == 'manager.py' or node.name == 'covers_monitor'
             else frozen).append(node)
        elif isinstance(node, ast.ClassDef) and node.name == (
                'Manager' if filename == 'manager.py' else 'Native'):
            if node.decorator_list or node.bases or node.keywords:
                raise ValueError('handoff classes must retain the plain instance ABI')
            selected.append(node)
            # Freeze resource lifecycle and instance shape.
            for member in node.body:
                allowed = (isinstance(member, ast.FunctionDef) and
                           (member.name != 'switch' and not member.name.startswith('__') if filename == 'manager.py'
                            else member.name == 'windows'))
                if not allowed:
                    frozen.append(member)
        else:
            frozen.append(node)
    return selected, tuple(map(shape, frozen))


class PolicyReload:
    def __init__(self, owner, manager_module, native_module, root=None):
        self.owner = owner
        self.thread = None
        self.root = Path(root or Path(__file__).resolve().parent)
        self.sources = self.read()
        self.fixed = {n: b for n, b in self.sources.items() if n in FIXED}
        self.syntax = {n: definitions(self.sources[n], n)[1] for n in POLICY}
        self.namespaces = {'manager.py': vars(manager_module).copy(),
                           'win32_host.py': vars(native_module).copy()}
        # These safety observations remain the original reviewed implementation.
        self.context = native_module.reload_context
        self.strict_gate = native_module.gate
        self.work_area = native_module.work_area
        self.loaded = digest(self.sources)
        self.previous = None

    def bind(self):
        """Called only by tick, never by the protocol reader's hello thread."""
        current = threading.get_ident()
        if self.thread not in (None, current):
            raise PermissionError('WM owner thread changed')
        self.thread = current

    def read(self):
        sources = {}
        for name in POLICY + FIXED:
            with (self.root / name).open('rb') as f:
                data = f.read(MAX_SOURCE_BYTES + 1)
            if len(data) > MAX_SOURCE_BYTES:
                raise PermissionError('policy source exceeds bounded staging size')
            sources[name] = data
        return sources

    def checkpoint(self):
        m = self.owner.manager
        return (type(m), type(m.native), m.gate_fn, self.namespaces, self.loaded)

    def restore(self, checkpoint):
        m = self.owner.manager
        m.__class__, m.native.__class__, m.gate_fn, self.namespaces, self.loaded = checkpoint

    def observe(self, deadline):
        if threading.get_ident() != self.thread:
            raise PermissionError('reload must run on the WM owner thread')
        if time.monotonic() >= deadline:
            raise TimeoutError('reload request expired; not applied')
        o, m = self.owner, self.owner.manager
        if (m.mode != 'live' or not m.lease or not m.native.mutating or o.held
                or o.stop.is_set() or o.latest or o.backlog or not o.requests.empty()
                or m.pending or m.gesture or m.preview or m.share or m.boot or m.gated):
            raise PermissionError('reload requires settled live WM with no queued intent or layout work')
        # Never use the share exception or cached gaming gate for lifecycle work.
        if self.strict_gate():
            raise PermissionError('reload refused: gaming/fullscreen or inspection gate')
        context = self.context()  # raises on unknown, busy, lock, missing input desktop
        rows = m.native.windows()
        work = self.work_area()
        if work != m.state.work:
            raise PermissionError('work area changed since last WM observation')
        fields = ('rect', 'state', 'maximised', '_normal', '_preferred', 'owned')
        snapshot = {r['key']: (r['ref'].record(), {f: r.get(f) for f in fields})
                    for r in rows}
        if len(snapshot) != len(rows):
            raise PermissionError('duplicate native identities')
        # A stale controller must reconcile normally before a new explicit request.
        old = {r['key']: (r['ref'].record(), {f: r.get(f) for f in fields})
               for r in m.rows}
        if old != snapshot:
            raise PermissionError('windows changed since last WM observation')
        observed = {r['key']: r for r in rows}
        for key, window in m.state.windows.items():
            row = observed.get(key)
            if (not row or window.minimised != (row['state'] == 'minimised')
                    or (not window.minimised and window.rect.values() != row['rect'])):
                raise PermissionError('controller layout has not settled to native bounds')
        if self.strict_gate() or self.context() != context:
            raise PermissionError('desktop changed during reload observation')
        if time.monotonic() >= deadline:
            raise TimeoutError('reload request expired during observation')
        m.lease.heartbeat()  # retain the SAME watchdog and durable claim cookies
        return context, snapshot, work

    def stage(self, sources):
        if any(sources[n] != b for n, b in self.fixed.items()):
            raise PermissionError('controller/engine/lease ABI changed; policy reload unsupported')
        namespaces = {}
        for name in POLICY:
            nodes, frozen = definitions(sources[name], name)
            if frozen != self.syntax[name]:
                raise PermissionError('imports, constructors or native safety ABI changed')
            ns = self.namespaces[name].copy()
            for node in nodes:inert_definition(node)
            exec(compile(ast.Module(body=nodes, type_ignores=[]), name, 'exec'), ns)
            namespaces[name] = ns
            self.owner.manager.lease.heartbeat()
        return namespaces

    def apply(self, expected, deadline, rollback=False):
        if not re.fullmatch(r'[0-9a-f]{64}', expected or ''):
            raise ValueError('supply the independently reviewed sha256')
        before = self.observe(deadline)
        checkpoint = self.checkpoint()
        if rollback:
            if not self.previous or expected != self.previous[-1]:
                raise PermissionError('no matching retained rollback generation')
            candidate = self.previous
        else:
            sources = self.read()
            if digest(sources) != expected:
                raise PermissionError('reviewed source hash mismatch')
            ns = self.stage(sources)
            candidate = (ns['manager.py']['Manager'], ns['win32_host.py']['Native'],
                         ns['win32_host.py']['gate'], ns, expected)
            # Check instance layout on disposable copies, without executing
            # candidate methods against any live state or resource.
            probe = copy(self.owner.manager)
            probe.__class__ = candidate[0]
            probe = copy(self.owner.manager.native)
            probe.__class__ = candidate[1]
            if self.read() != sources:
                raise PermissionError('source changed during staging')
        if self.observe(deadline) != before:
            raise PermissionError('desktop or windows changed during staging')
        try:
            self.restore(candidate)
            if self.observe(deadline) != before:
                raise PermissionError('desktop or windows changed at handoff')
        except BaseException:
            self.restore(checkpoint)
            raise
        self.previous = None if rollback else checkpoint
        return {'text': ('WM policy rolled back to ' if rollback else 'WM policy loaded ') + self.loaded,
                'rows': [{'sha256': self.loaded, 'rollback_sha256':
                          self.previous[-1] if self.previous else None}]}
