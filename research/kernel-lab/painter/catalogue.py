"""EDITING THE PAINTER (Alex, 4 Nov 2026; AGENTS.md "Source edits go down over time").
The painter's vocabulary (formats, handles, scopes, parts) is shared by every app. Add to it only what any lens could
use, documented where lens authors read it (ARRANGEMENT.md); never a handle, format or branch for one app. If one app
needs something, the general form of it is the change.

First-party cards: data for discovery, installation and the live gallery."""
import json


def setting(type='text', default=''):
    return dict(type=type, default=default)


T = setting
COMMON = dict(label=T(default='Example'))
CATALOGUE = {
    'action-notice': ('feedback', 'Show an action result and reverse its exact receipt, even after its row disappears.',
        dict(stateKey=T(default='actionNotice'),scopeKeys=T(),labels=T(default='{}')), 'body message undo dismiss', '', 'undo',
        'Map moves; private board actions; work panels; forms',
        'Bundled actionFeedback publishes immediate pending/results without a world reread. stateKey names a local channel; scopeKeys names view fields defining navigation (empty means all). Navigation clears results and invalidates pending tokens. Undo rechecks scope/token and uses the exact returned receipt only, with an authored gesture and existing permission. Work Mark done reuses the same contract. Old JSON view notices are intentionally ignored.'),
    'date-tile': ('content','A date tile, time range, place and bounded countdown for any dated thing.',
        dict(start=T(),end=T(),place=T(),soonDays=T('number',3),date=T(),month=T(),day=T(),weekday=T(),time=T(),labels=T(default='{}')),
        'body tile month day weekday time place countdown','','','Events; appointments; deadlines',
        'Display only. Local browser timezone; no calendar backend. Countdown only inside soonDays.'),
    'poll': ('inputs', 'Sealed counts and a choice over any thing with options and a closing time.',
        dict(labels=T(default='{}'),stamp=T()), 'body option counts closing', '', 'vote', 'Community board; polls; council vote tally',
        'Counts only. Vote admission and closing are world words; no voter identities.'),
    'slots': ('inputs', 'Claim the remaining seats on any claimable thing.',
        dict(label=T(),labels=T(default='{}')), 'body label count meter claim', '', 'claim', 'Community board; inventory; volunteering',
        'Claim admission, once and closing are checked by the world.'),
    'file': ('media', 'Read a converted photo, document, table, event, media or downloadable file.',
        dict(labels=T(default='{}'),content=T('json',{}),target=T('fact'),name=T(),owner=T('fact'),variant=T(default='content'),stamp=T(),page=T('number',1),pageTarget=T(),pageRequest=T('number',0),
             quoteMode=T(default='thread'),replyTarget=T('fact'),replyLabel=T(),startLabel=T(),replyGroup=T('fact')), 'body preview page alt download status quote-reply quote-text reply-text reply-send', 'table', 'quote reply start alt rsvp calendar',
        'Community board; file browser; reading room; photo gallery',
        'quoteMode=inline shows a local draft and named reply destination. replyTarget uses the authored reply gesture; without it, start explicitly creates a discussion. No send on selection. Shared right-click Comment is unchanged. Permission-checked Blob transport; PDF pages show extracted text.'),
    'field-list': ('content', 'Show a kind declaration\'s fields in authored order, including neighbour-made kinds.',
        dict(fields=T(),labels=T(default='{}'),stamp=T()), 'body label value', '', '', 'Community board; inventory; directory',
        'Fields are displayed as text, never evaluated.'),
    'calendar': ('collections', 'A shared month and week calendar over any dated things: add an event, RSVP in one click, see who is coming.',
        dict(label=T(default='Calendar'),month=T(),date=T(),view=T(default='month'),weekStart=T('number',0),placeField=T(default='location'),
             openKey=T(),defaultTime=T(default='18:00'),labels=T(default='{}')),
        'container body heading grid event agenda', '', 'select add rsvp', 'Community events; meetings; club calendars; habit tracker',
        'Children are the dated things (facts start, end, title, a place, text, going/maybe, coming, your_rsvp). Browser-local time. No recurrence or reminders; words come from the gestures arranged on it.'),
    'board': ('collections', 'Arrange lanes over shared tasks with quick add and filters.',
        dict(title=T(default='Task board'),subtitle=T(default='A clear mind, one thing at a time.'),
             eyebrow=T(default='A LITTLE SPACE FOR WHAT MATTERS'),hint=T(default='Add something worth doing…'),filter=T(default='all')),
        'body input filters lanes', 'lanes', 'add filter summarize undo', 'Task board; kanban; worker dashboard'),
    'lane': ('collections', 'A named drop collection with counts and a fold.',dict(name=T(default='Lane')),
        'body heading', 'cards', 'drop card', 'Task board; kanban; rooms'),
    'card': ('collections', 'A fact-backed card with content, actions and an editable detail drawer.',
        {key:T() for key in ('title','colour','note','note_colour','note_style','who')},
        'body top title note footer avatar', 'flag menu content', 'key 1 key 2 key 3 key 4 key d key Delete title text note note-colour note-style close',
        'Task board; kanban; feed; inventory'),
    'flag': ('feedback','A small priority marker.',dict(priority=T('number',4)), 'icon','', '', 'Task board; dashboard'),
    'menu': ('overlays','A keyboard-navigable menu of authored gesture lines.',{},'body item','', 'menu "Label"','Task board; file browser; tray'),
}

for name,category,purpose,settings,uses,limits in [
    ('button','inputs','Press to say an authored word, or select named view state.',
     dict(selectKey=T(),value=T(),completionText=T(),noticeKey=T(default='actionNotice')),
     'Forms; settings; sign-in page','completionText publishes the returned receipt to action-notice. Pending presses cannot repeat. selectKey changes only local view state.'),
    ('input','inputs','Edit one line; commit=submit sends only on Enter or the explicit button, retaining refused drafts.',
     dict(value=T(),hint=T(),commit=T(default='change'),submitLabel=T(default='Submit'),labels=T(default='{}')),
     'Forms; settings; chat; search','commit=change emits change on blur; commit=submit emits submit, ignores IME Enter, and prevents duplicate pending submissions.'),
    ('editor','inputs','Edit plain text or Markdown source.',dict(value=T(),hint=T()),'Writing room; document editor; email','No collaborative rich text, pagination or desktop publishing engine.'),
    ('choice','inputs','Choose one supplied option.',dict(value=T(),options=T(default='One|Two|Three'),selectKey=T()),'Forms; polls; settings','selectKey changes local view state; otherwise emits the authored change gesture.'),
    ('switch','inputs','Toggle a boolean setting.',dict(checked=T('boolean',False)),'Settings; form builder',''),
    ('text-block','content','Show selectable text.',dict(value=T(default='A little room to think.')),'Feed; rooms; writing room',''),
    ('markdown','content','Render safe Markdown headings, emphasis and checklists.',dict(value=T(default='## Welcome\n**Bring** a thought.\n- [ ] Make room')),'Feed; writing room; reading room','No raw HTML or concurrent document model.'),
    ('code','content','Display source or logs as literal text.',dict(value=T(default='hello, world')),'Diff review; terminal; logs','Display only; no terminal execution or semantic diff engine.'),
    ('icon','content','A text or Unicode icon with a label.',dict(value=T(default='✦')),'Browser chrome; tray widgets',''),
    ('image','media','Show an inline image with alternative text.',dict(value=T(default='Inline image')),'Feed; gallery; recipes','Inline data/blob images only; no remote image fetching.'),
    ('avatar','media','Show an inline portrait or initials.',dict(value=T(default='Alex Neighbour')),'Chat; feed; directory; JEFF bar',''),
    ('player','media','Play Blob audio or arrange controls beside granted media verbs.',dict(value=T()),'Spotify-style player; audio editor','Native playback accepts Blob sources from the permission-checked file transport; remote streams stay blocked. OS playback uses separately granted media.* verbs. No Spotify connector, video calls, WebRTC or waveform decoding.'),
    ('badge','feedback','A compact labelled status.',{},'Notifications; dashboard; HUD',''),
    ('progress','feedback','A labelled native progress indicator.',dict(value=T('number',65),max=T('number',100)),'Polls and votes; worker dashboard; HUD',''),
    ('empty-state','feedback','Explain an empty collection.',{},'Feed; board; file browser',''),
    ('list','collections','Stack supplied parts with keyboard navigation.',{},'Feed; chat; search results; agenda',''),
    ('virtual-list','collections','Window a long collection in fixed-height rows.',dict(height=T('number',320),row_height=T('number',40)),'Logs; search results; long lists','Fixed-height rows; no automatic measurement of variable-height items.'),
    ('table','collections','Display and sort text cells in named columns.',dict(columns=T(default='Name|Status'),sortable=T('boolean',False),data=T('json',[{'Name':'Welcome','Status':'Ready'}])),'Spreadsheet-like table; worker dashboard; budget','No formulas, range editing or spreadsheet engine.'),
    ('tree','collections','Nested disclosure sections.',{},'File browser; tiling window manager','Supplied structure only; no filesystem provider.'),
    ('timeline','collections','Arrange ordered event parts across a row.',{},'Timeline; meeting agenda','No zoom or time scale engine.'),
    ('gallery','collections','Responsive grid of supplied media parts.',{},'Photo gallery; directory; video call grid','No cloud photo importer or WebRTC.'),
    ('map','collections','Plot local XY points on a labelled 2D surface.',dict(data=T('json',[{'x':50,'y':80},{'x':180,'y':90}]),width=T('number',320),height=T('number',180),caption=T()),'Seabright map; dashboards','No geographic tiles, projection, geocoding or routing.'),
    ('chart','collections','Draw a supplied numeric series on a labelled 2D surface.',dict(data=T('json',[2,5,4,8,6]),width=T('number',320),height=T('number',180),caption=T()),'Charts; dashboards; vote tally','No statistics or streaming signal decoder.'),
    ('pixel-surface','media','Draw supplied pixels on a 2D surface; press supplies coordinates.',dict(pixels=T(default='..aa..\n.aaaa.\n.a..a.\n..aa..'),width=T('number',160),height=T('number',120),caption=T()),'Pixel guy and editor; game HUD; node graph; music sequencer','2D only. No 3D CAD, geometry engine, game engine or precise audio scheduling.'),
    ('toolbar','layout','Arrange actions in a row.',{},'Browser chrome; writing room; system bars',''),
    ('tabs','layout','Arrange focusable tab-like children.',{},'Phone layout; browser chrome; settings','Selection is supplied by facts/conditions; no hidden navigation state.'),
    ('split-pane','layout','Two resizable content columns.',{},'Tiling window manager; file browser; email','Layout only; native window management uses window words.'),
    ('palette','overlays','Filter supplied commands by their displayed words.',{},'Command palette; search','Only supplied commands; no arbitrary shell execution.'),
]:
    CATALOGUE[name]=(category,purpose,dict(COMMON,**settings),
                     'body control submit status' if name == 'input' else 'body control',
                     'content','press change select submit' if name == 'input' else 'press change select',uses)
    # Limits are prose on the same card, not an implicit promise in a name.
    CATALOGUE[name] += (limits,)

for name in ('dialog','popover','tooltip','toast','drawer'):
    CATALOGUE[name]=('overlays',f'Open a {name} with supplied content.',dict(COMMON,text=T(default='A little room for details.')),
                     'body','content','press', 'Notifications; settings; forms; phone layout','')


def cards():
    result=[]
    for name,row in CATALOGUE.items():
        category,purpose,settings,parts,slots,gestures,uses,*limits=row
        example=f'root : {name}'
        if name=='calendar': example='root : calendar, month 2026-11, date 2026-11-04'
        if name=='card': example='root : card, title "A small next step"'
        if name=='menu': example='root : card, title "Try the menu button"\n  actions : menu\n    on menu "Read my profile" do look $viewer.id'
        result.append(dict(name=name,category=category,purpose=purpose,settings=json.dumps(settings),
            parts=json.dumps({p:dict(facts='bound visible row') for p in parts.split()}),slots=json.dumps(slots.split()),
            gestures=gestures,example=example,uses=uses,limitations=limits[0] if limits else ''))
    return result
