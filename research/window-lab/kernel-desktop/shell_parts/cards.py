"""The shell bars' component cards (SHELL.md, "The bars as components"): data for `components`, `help <name>` and the
install. Each card names the component's settings (its handles), its named parts (style targets) and its gestures.
Builder draft, 26 Oct 2026."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def T(type='text', default=''):
    return dict(type=type, default=default)


LIMITS = ('Runs only inside the shell-top or shell-dock widget (it needs ShellKit, the bars\' vocabulary); in Worker '
          'quarantine (unreviewed or changed code) it stops calmly until a steward reviews it.')
# name: (purpose, settings, parts, gestures, example)
SHELL = {
    'shell-bar': ('The top bar\'s rail: holds any parts, and tells its window where it is solid and what strip to reserve.',
                  dict(label=T(default='Agora top bar')), 'rail', '', 'root : shell-bar\n  left : shell-island, side left'),
    'shell-island': ('A rounded group of bar parts: left, middle (centred) or right.', dict(side=T(default='left'), label=T()),
                     'body', '', 'left : shell-island, side left, label "Launcher and app"'),
    'shell-separator': ('A thin rule between groups in the dock or the bar.', {}, 'body', '', 'apps-start : shell-separator'),
    'shell-launcher': ('The Agora mark: opens the launcher (Agora apps, kept programs, or say a line). Alt+Space opens it.',
                       dict(apps=T()), 'body popover search app', 'lines start',
                       'launcher : shell-launcher\n  on lines do window.open lines'),
    'shell-spaces': ('One chip per window-manager space; shown only with two or more.', {}, 'body space', '', 'spaces : shell-spaces'),
    'shell-focused-app': ('The app in front and its window menu: pin in place, minimise, close, keep in dock, leave alone.',
                          dict(max=T('number', 250)), 'body icon name menu', '', 'focused : shell-focused-app'),
    'shell-clock': ('The time and date; opens a month calendar with a way to the notifications.',
                    dict(date=T('boolean', True), seconds=T('boolean', False)), 'body time date popover', '',
                    'clock : shell-clock, seconds yes'),
    'shell-reading': ('One machine reading as text (CPU 14%); with show setting, only while shell-settings show_<key>=yes.',
                      dict(key=T(default='cpu'), label=T(), show=T(default='setting')), 'body', '',
                      'cpu : shell-reading, key cpu, label CPU'),
    'shell-notifications': ('The bell, its unread count and the inbox.', {}, 'body badge popover', 'clear',
                            'notifications : shell-notifications\n  on clear do notice.clear'),
    'shell-media': ('What is playing, with its cover; play/pause, next, previous.', {}, 'body art title popover', 'play next prev',
                    'media : shell-media\n  on play do media.play'),
    'shell-tray': ('The quick-settings button: its chips are its children; a row per chip and the bar reading switches.',
                   dict(readings=T(default='cpu,memory')), 'body popover', '',
                   'tray : shell-tray\n  network : shell-chip, key network'),
    'shell-chip': ('One machine reading as a glyph in the tray (network, volume, battery or any system.now key), with its value.',
                   dict(key=T(default='network'), value=T()), 'body glyph value', 'press',
                   'battery : shell-chip, key battery\n  on press do window.settings which=battery'),
    'shell-jeff': ('JEFF\'s presence and a way to the conversation (default: shell-settings jeff_open, else window.open lines).',
                   {}, 'body dot name popover', 'open', 'jeff : shell-jeff'),
    'shell-power': ('Turns the Agora desktop off on a second press within four seconds.', {}, 'body', 'off',
                    'power : shell-power\n  on off do off window'),
    'shell-dock': ('The centred dock: arranged parts, and its shell-dock-item child repeated once per app (pinned, running, '
                   'Agora windows), reading wm.windows each second.', dict(apps=T()), 'pill', '',
                   'root : shell-dock\n  item : shell-dock-item'),
    'shell-dock-item': ('One app in the dock: icon, window count and a mark (open, front, minimised); press, middle press, '
                        'right press menu, hover preview with live thumbnails. Facts state and app on body for styles.',
                        dict(group=T('json', {})), 'body icon mark count menu preview tile', '',
                        'item : shell-dock-item'),
    'shell-dock-button': ('A fixed dock button: the Agora launcher (opens launcher) or a line (press).',
                          dict(icon=T(default='agora:agora'), label=T(default='Agora'), opens=T()), 'body popover app', 'press lines start',
                          'overview : shell-dock-button, icon agora:overview, label "Overview"\n  on press do window.open tasks'),
}


def cards():
    out = []
    for name, (purpose, settings, parts, gestures, example) in SHELL.items():
        out.append(dict(name=name, category='shell', purpose=purpose, settings=json.dumps(settings),
                        parts=json.dumps({p: dict(facts='the bar part') for p in parts.split()}), slots=json.dumps([]),
                        gestures=gestures, example=example, uses='Desktop shell: top bar and dock', limitations=LIMITS))
    return out


def code(name):
    return (HERE / 'components' / f'{name}.js').read_text(encoding='utf-8')
