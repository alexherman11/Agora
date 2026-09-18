"""Repair only the two newly created trial clones' snapshot-bound NIC identity."""

from prepare_trials import ROOT, YARD, vbox
import json
import re

base = json.loads(YARD.read_text())
info = vbox("showvminfo", base["vm_id"], "--machinereadable")
mac = re.search(r'^macaddress1="([^"]+)"', info, re.M)[1]
expected = {
    "execution": "d0b8ac83-1217-4834-bfeb-703801221a45",
    "yard": "92dd45a0-682e-46ba-a866-12808c7262e4",
}
for role, vm_id in expected.items():
    folder = ROOT / "machines" / role
    config = json.loads((folder / "machine.json").read_text())
    baseline = json.loads((folder / "baseline.json").read_text())
    if config["vm_id"] != vm_id or baseline["vm_id"] != vm_id:
        raise RuntimeError("Unexpected VM")
    info = vbox("showvminfo", vm_id, "--machinereadable")
    if f'name="Agora3-Arrangement-{role}-20260916"' not in info:
        raise RuntimeError("Unexpected name")
    if 'VMState="running"' in info:
        vbox("controlvm", vm_id, "poweroff")
    vbox("snapshot", vm_id, "restore", baseline["snapshot_id"])
    vbox("modifyvm", vm_id, "--macaddress1", mac)
    vbox("snapshot", vm_id, "take", "trial-network-ready")
    listing = vbox("snapshot", vm_id, "list", "--machinereadable")
    snapshot = re.search(r'^CurrentSnapshotUUID="([^"]+)"', listing, re.M)[1]
    (folder / "baseline.json").write_text(
        json.dumps({"vm_id": vm_id, "snapshot_id": snapshot}, indent=2)
    )
    if role == "yard":
        (ROOT / "yard.json").write_text(
            json.dumps(
                {"machine_config": str(folder / "machine.json"), "snapshot_id": snapshot}, indent=2
            )
        )
    print(json.dumps({"role": role, "vm_id": vm_id, "snapshot": snapshot}))
