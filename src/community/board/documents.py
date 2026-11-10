"""EDITING A MODULE (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
A module is a seam to something outside the kernel (a model provider, git, Twitch, the media session, a map server) and
turns it into world facts and words. What the world does with them (who is told, when, in what words, how it looks)
belongs in rules, lenses and this module's settings thing, read at each use. Names (JEFF, Alex), ids (dk...), models,
counts, timeouts and message text in this file are debt: move them to settings when you touch them, and never add more.

Folder metadata around admitted files; no byte transport or private store."""
from protocol import line


ENTRIES = [
    # <id> declares a positional target to kernel admission, even inside a
    # named argument. Reserve it for the file/entry actually acted on.
    dict(word='files.browse', kind='see', takes='library=<library> [parent=<folder>]', may='members',
         help='files.browse library=<library> parent=<folder>: visible folders, files and links from posts.'),
    *[dict(word='files.' + word, kind='do', may='members', undo='yes', takes=takes, help=help)
      for word, takes, help in [
          ('folder', 'name=<name> library=<library> [parent=<folder>]', 'Make a folder in a document library.'),
          ('store', '<id> library=<library> [parent=<folder>] [name=<name>]', 'Make a document entry; attach a new private upload to that entry to share it. Existing post attachments keep their permissions.'),
          ('rename', '<id> name=<name>', 'Rename a document entry or folder.'),
          ('move', '<id> to=<folder|library>', 'Move an entry or folder. Cycles and crossing libraries refuse.')]],
]


def call(message, read):
    use, envelope = message['use'], message.get('args') or {}
    args = dict(envelope.get('kv') or {})
    args['target'] = envelope.get('target')
    word = message['word'].split('.')[-1]
    libraries = read(use, 'rows document-library')
    folders = read(use, 'rows document-folder')
    entries = read(use, 'rows document-entry')
    visible = {r['id']: r for r in libraries + folders + entries}
    target = visible.get(args.get('target'))
    library_id = args.get('library') or (target or {}).get('library')
    library = next((r for r in libraries if r['id'] == library_id), None)
    if not library:
        raise ValueError('Choose a visible document library.')
    if target and target.get('library') != library_id:
        raise ValueError('Choose a target in this library.')
    parent_id = args.get('to') if word == 'move' else args.get('parent')
    parent_id = parent_id or library_id
    parent = visible.get(parent_id)
    if not parent or (parent_id != library_id and
                      (parent.get('kind') != 'document-folder' or parent.get('library') != library_id)):
        raise ValueError('Choose a folder in this library.')
    saw = {library_id: library['rev'], parent_id: parent['rev']}
    group = (library.get('groups') or [None])[0]

    def named():
        name = str(args.get('name', '')).strip()
        if not name or len(name) > 200:
            raise ValueError('Use a name between 1 and 200 characters.')
        return name

    if word == 'browse':
        files = {r['id']: r for r in read(use, 'rows file')}
        posts = {r['id']: r for r in read(use, 'rows post')}
        indexed = {r.get('file') for r in entries if r.get('library') == library_id}
        result = []
        for row in folders + entries:
            if row.get('library') != library_id or row.get('parent') != parent_id:
                continue
            if row['kind'] == 'document-folder':
                result.append(row)
            elif row.get('file') in files:
                file = files[row['file']]
                post = posts.get(file.get('attached_to'), {})
                result.append(dict(row, file_id=file['id'], upload_owner=file.get('upload_owner'),
                                   source_post=post.get('id', ''), source_title=post.get('title', ''),
                                   source_text=post.get('text', '')))
        # Attachments shared in the library's board channel are discoverable at root.
        if parent_id == library_id:
            for file in files.values():
                post = posts.get(file.get('attached_to'))
                if file['id'] not in indexed and post and group in post.get('groups', []):
                    result.append(dict(file, kind='document-link', file_id=file['id'],
                                       library=library_id, parent=library_id, source_post=post['id'],
                                       source_title=post.get('title', ''), source_text=post.get('text', '')))
        return dict(rows=sorted(result, key=lambda r: (r['kind'] != 'document-folder', r.get('name', '').casefold())))
    if word == 'folder':
        return dict(lines=[line('make', kind='document-folder', name=named(), library=library_id,
                                parent=parent_id, within=library_id,
                                **({'in': group} if group else {}))], saw=saw)
    if word == 'store':
        file = next((r for r in read(use, 'rows file') if r['id'] == args.get('target')), None)
        if not file:
            raise ValueError('Choose a visible uploaded file.')
        if any(r.get('library') == library_id and r.get('file') == file['id'] for r in entries):
            raise ValueError('This file already has an entry in this library.')
        # The ordinary attach word is a separate, uploader-authorised action.
        # Merely indexing a private file never publishes its bytes.
        return dict(lines=[line('make', kind='document-entry', file=file['id'],
                                name=args.get('name') or file.get('name', 'File'),
                                library=library_id, parent=parent_id, within=library_id,
                                **({'in': group} if group else {}))],
                    saw={**saw, file['id']: file['rev']})
    if not target or target.get('kind') not in ('document-folder', 'document-entry'):
        raise ValueError('Choose a folder or document entry.')
    saw[target['id']] = target['rev']
    if word == 'rename':
        return dict(lines=[line('set', target['id'], name=named())], saw=saw)
    if word != 'move':
        raise ValueError('Unknown document word.')
    ancestor, visited = parent_id, set()
    while ancestor != library_id:
        if ancestor == target['id'] or ancestor in visited:
            raise ValueError('A folder cannot be moved inside itself.')
        visited.add(ancestor)
        folder = visible.get(ancestor)
        if not folder or folder.get('library') != library_id:
            raise ValueError('The destination folder is unavailable.')
        saw[ancestor] = folder['rev']
        ancestor = folder.get('parent')
    return dict(lines=[line('set', target['id'], parent=parent_id)], saw=saw)
