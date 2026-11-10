"""Reviewed registration specification; never connects to a live world itself."""
import sys
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]
PYTHON = LAB.parents[1] / '.venv/Scripts/python.exe'


def specs(worker=None):
    return [dict(name='model', run=[str(PYTHON), str(worker or LAB/'modules/model/model.py')],
                 publishes='model.*', grants='model.* look rows help set'),
            dict(name='summarize', run=[str(PYTHON), str(LAB/'modules/summarize/summarize.py')],
                 publishes='summarize.*', grants='summarize.* model.preview rows make set',
                 only='kind:taskboard-task', **{'for': 'steward'})]


def configure(door):
    """Use only world words after both processes have offered. Idempotent."""
    for word in ('ask', 'summarize', 'classify', 'status', 'preview'):
        row = door.rows('word', bound='model.'+word)[0]
        if row.get('once') != 'at most 60 per day per person':
            door.say('look '+row['id'])
            door.say('word-set '+row['id']+' may=members once="at most 60 per day per person"')
    if not door.rows('model-settings', name='model'):
        door.say('make kind=model-settings name=model model=qwen3.5:9b')
