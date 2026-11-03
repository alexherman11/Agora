"""Asks & offers lens: its own component lens, standalone in a widget and nestable in the board. Never opens a window.

Built only from gallery parts (list, input, badge, avatar, text-block, button) over the board's `board.asks`
reading, so anyone may restyle it (personal-style) or rearrange it (personal-view) without touching the board.
Inside the board it is one arrangement line: `asks : lens, name seabright-asks`.
"""
import json

from ui_install import upsert, widget_source, Q, TOKENS, HERE

NAME = 'seabright-asks'
# asks_channel is where "add one" posts; channel filters the list and is shared with the host board when nested.
VIEW = dict(channel='', asks_channel='', asks_side='all', asks_status='active', asks_seats=1)
GRANTS = ('window.surface rows look look-view help component-health component-action personal-view personal-style '
          'board.* claim set undo hear:board.* hear:claim hear:set hear:undo')


def install_asks(door):
    """door: say/rows over an authenticated door. Expects the board world and gallery components installed."""
    view = dict(VIEW, asks_channel=next((c['group'] for c in door.rows('board-channel') if c.get('title') == 'Asks & offers'), ''))
    lens = upsert(door, 'lens', NAME, title='Asks & offers', painter='components',
                  text=(HERE / 'asks.lens').read_text(encoding='utf-8'), view=json.dumps(view))
    upsert(door, 'part-style', NAME + '-theme', lens=NAME, target='tokens', **TOKENS)
    widget = upsert(door, 'widget', NAME, title='Asks & offers', style='bars', receipts='quiet',
                    component_lens=NAME, code=widget_source())
    current = door.rows('widget', name=NAME)[0]
    if not current.get('on') or not any(g.get('words') == GRANTS and not g.get('revoked') for g in door.rows('grant', to=widget)):
        door.say('look ' + widget); door.say('widget ' + widget + ' surface=window grants=' + Q(GRANTS))
    return dict(lens=lens, widget=widget)
