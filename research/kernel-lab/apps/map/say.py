"""Say one line to a scratch world kept up by `scratch.py serve` (the door file it wrote), and print the answer.

    python say.py <door-file> "<line>"
"""
import json
import sys
import urllib.error
import urllib.request

SEE = {'rows', 'look', 'help', 'kinds', 'recent', 'who', 'look-view', 'components', 'map.find', 'map.where',
       'map.near', 'map.path', 'map.layers'}


def say(door_file, line, who='token'):
    door = json.loads(open(door_file, encoding='utf-8').read())
    route = '/see' if line.split()[0] in SEE else '/do'
    req = urllib.request.Request(door['url'] + route, json.dumps({'line': line}).encode(),
                                 {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + door[who]})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'ok': False, 'text': e.read().decode()}


if __name__ == '__main__':
    out = say(sys.argv[1], ' '.join(sys.argv[2:]))
    print(('' if out.get('ok') else 'REFUSED ') + (out.get('text') or ''))
