"""Bounded recovery restart for the renderer defects found after deployment.
Does not rerun taskboard seeding/migration or recreate its windows.
"""
from deploy import assert_clear,run,DESKTOP
from install import install,taskboard

assert_clear()
run(DESKTOP/'kdesk_off.py')
run(DESKTOP/'kdesk_on.py','--wait')
assert_clear()
print('Widget definitions reconciled:',', '.join(install(taskboard.live_door())),flush=True)
