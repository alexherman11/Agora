"""Shared write/paint validation and data-only value presentation handles."""
from datetime import datetime, timezone
import json
import re

from kernel.kernel import Refused

TOKENS = dict(paper='#FAF9F6', card='#FFFFFF', ink='#35433D', muted='#929B99', accent='#638779',
              red='#CF514A', orange='#C58332', blue='#507EBC', grey='#9BA3AC', rose='#FBE9E8',
              peach='#FFF0DC', sage='#EAF3E9', sky='#E8F1FA', lilac='#F0EBF8',
              small='8px', medium='12px', large='16px', soft='12px', round='50%')
STYLE_KEYS = ('color','background','radius','padding','gap','glow','lines','emphasis','size')
# via_actor: the kernel's own attribution on anything an agent makes (words._agent_origin); without it here every
# part-style an agent made was refused at paint time (found 26 Oct by the shell's "make the clock bigger" test).
META = {'id','rev','by','kind','lens','target','made','changed','made_by','made_at','changed_at','name','title','personal','for','sees','from','origin','forgotten','pinned','via_actor'}
COLOUR = re.compile(r'(?:#(?:[a-f0-9]{3}|[a-f0-9]{4}|[a-f0-9]{6}|[a-f0-9]{8})|transparent|black|white|red|blue|green|grey|gray|orange|purple|pink|yellow)',re.I)
MEASURE = re.compile(r'(?:0|\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw))')
TARGET = re.compile(r'[\w-]+(?:\.[\w-]+)?(?:\[[\w-]+=[\w-]+\])?')


def motion(value):
    try: spec=json.loads(value) if isinstance(value,str) else value
    except ValueError: raise Refused('motion token needs JSON {from, to, duration}')
    if not isinstance(spec,dict) or set(spec)-{'from','to','duration'}:raise Refused('motion token allows from, to, duration')
    duration=spec.get('duration',200)
    if not isinstance(duration,(int,float)) or not 0<=duration<=2000:raise Refused('motion duration: 0..2000 ms')
    for state in ('from','to'):
        values=spec.get(state,{})
        if not isinstance(values,dict) or set(values)-{'opacity','transform'}:raise Refused('motion states allow opacity and transform')
        if 'opacity' in values and (not isinstance(values['opacity'],(float,int)) or not 0<=values['opacity']<=1):raise Refused('motion opacity: 0..1')
        if 'transform' in values and not re.fullmatch(r'(?:none|(?:(?:translate[XY]?|scale)\([-\d., px%]+\)\s*)+)',str(values['transform'])):raise Refused('motion transform allows translate/scale or none')
    return spec


def style_values(rule, tokens=None):
    tokens=dict(TOKENS,**(tokens or {}));target=rule.get('target','')
    if target=='tokens':
        result={}
        for key,value in rule.items():
            if key in META or key.startswith('in:'):continue
            if not re.fullmatch(r'[a-z][\w-]*',key):raise Refused('token name must be a plain word')
            if key.startswith('motion-'):result[key]=motion(value)
            elif key.endswith('-font') and re.fullmatch(r"[A-Za-z][A-Za-z0-9 ,'-]{0,100}",str(value)):result[key]=value
            elif re.fullmatch(r'\d{1,4}(?:\.\d+)?',str(value)) and float(value)<=2000:result[key]=value
            elif COLOUR.fullmatch(str(value)) or MEASURE.fullmatch(str(value)):result[key]=value
            else:raise Refused(f'token {key}: use a colour, measure, bounded number or plain font-family token')
        return result
    if not TARGET.fullmatch(target):raise Refused('style target: component.part[fact=value], component, or tokens')
    unknown=[key for key in rule if key not in META and key not in STYLE_KEYS and not key.startswith('in:')]
    if unknown:raise Refused('style allows '+', '.join(STYLE_KEYS)+'; unknown '+unknown[0])
    result={}
    for key in STYLE_KEYS:
        if key not in rule:continue
        val=str(tokens.get(str(rule[key]),rule[key]))
        if key in ('color','background','glow'):
            if not COLOUR.fullmatch(val):raise Refused(f'{key}: use a colour token or #rgb/#rgba/#rrggbb/#rrggbbaa')
            if key=='glow' and re.fullmatch(r'#[a-f0-9]{6}',val,re.I):val+='55'
        elif key=='lines':
            if not re.fullmatch('[1-9]',val):raise Refused('lines: allowed 1..9')
        elif key=='emphasis':
            if val not in ('normal','bold'):raise Refused('emphasis: allowed normal or bold')
        else:
            parts=val.split();limit=2 if key=='gap' else 4 if key in ('padding','radius') else 1
            if not 1<=len(parts)<=limit or not all(MEASURE.fullmatch(str(tokens.get(p,p))) for p in parts):
                raise Refused(f'{key}: use 1..{limit} nonnegative measures (px, rem, em, %, vh, vw) or spacing tokens')
            val=' '.join(str(tokens.get(p,p)) for p in parts)
        result[key]=val
    return result


def validate_write(k, actor, kind, values, tx=None):
    if kind=='theme':
        # a theme is data with a closed schema: refuse anything unsafe before it is written (theme/model.py)
        from theme.model import ThemeError,check_text
        try:check_text(values.get('text'))
        except ThemeError as exc:raise Refused('theme not accepted: '+str(exc)[:400])
        return
    if kind!='part-style':return
    def lens_id(name):
        return next((t for t in k.things('lens') if name in (t,k.state.get(t,'name'))),name)
    tokens={}
    for t in k.things('part-style'):
        a=k.shown(actor.person,t)
        if a and a.get('target')=='tokens' and lens_id(a.get('lens'))==lens_id(values.get('lens')) and (not a.get('personal') or a.get('made_by') in (actor.id,actor.person) or a.get('for')==actor.person):
            try:tokens.update(style_values(a))
            except Refused:pass
    if tx:
        pending={}
        for (t,key),v in tx.over.items():pending.setdefault(t,{})[key]=v
        for a in pending.values():
            if a.get('kind')=='part-style' and a.get('target')=='tokens' and a.get('lens')==values.get('lens'):tokens.update(style_values(a))
    style_values(values,tokens)


def present(value, kind, now):
    if kind=='initials':return ''.join(letters[0] for word in str(value).split() if (letters:=''.join(c for c in word if c.isalpha())))[:2].upper()
    if kind=='count':
        if isinstance(value,(list,dict)):return str(len(value))
        try:return f'{float(value):,.0f}'
        except (ValueError,TypeError):raise Refused('count formatter needs a number or JSON collection')
    if kind=='relative-date':
        if not value:return ''
        try:date=datetime.fromisoformat(str(value).replace('Z','+00:00')).replace(tzinfo=timezone.utc)
        except ValueError:raise Refused('relative-date needs an ISO date')
        days=(date.date()-now.date()).days
        return 'Today' if days==0 else 'Tomorrow' if days==1 else 'Yesterday' if days==-1 else f'In {days} days' if days>0 else f'{-days} days ago'
    if kind=='text':return str(value)
    if kind in ('short-relative','calendar-date','month','day','weekday','time'):
        if not value:return ''
        try:
            date=datetime.fromisoformat(str(value).replace('Z','+00:00'))
            if date.tzinfo is None:date=date.replace(tzinfo=timezone.utc)
        except ValueError:raise Refused('date format needs an ISO date')
        if kind=='month':return date.strftime('%b')
        if kind=='day':return str(date.day)
        if kind=='weekday':return date.strftime('%a')
        if kind=='time':return date.strftime('%I:%M %p').lstrip('0').lower()
        if kind=='calendar-date':return f'{date.day} '+date.strftime('%b')+(f' {date.year}' if date.year!=now.year else '')
        seconds=(now-date).total_seconds();days=(now.date()-date.date()).days
        if 0<=seconds<60:return 'now'
        if 0<=seconds<3600:return f'{int(seconds//60)}m'
        if 0<=seconds<86400 and days==0:return f'{int(seconds//3600)}h'
        return date.strftime('%a') if 0<=days<7 else date.strftime('%b ')+str(date.day)
    raise Refused('format: initials, relative-date, short-relative, calendar-date, month, day, weekday, time, count or text')
