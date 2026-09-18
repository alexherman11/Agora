"""Contract extension tests; no component engine is installed or executed."""
import copy
import hashlib
from pathlib import Path
import unittest
from component_registry import ComponentRefusal, ComponentRegistry


def record(fields):
    return {"type": "object", "properties": fields, "required": list(fields), "additionalProperties": False}


def descriptor(name="research.exact-text", version=1):
    return {"id": name, "version": version,
            "implementation": {"package": "research.engine-fixture", "revision": 1, "export": "surface"},
            "material_schema": record({"text": {"type": "string", "maxLength": 4000}}),
            "actions": {"replace": {"input_schema": record({"value": {"type": "string", "maxLength": 4000}}), "effect": "material"}},
            "inspect_schema": record({"complete": {"type": "boolean"}})}


class RegistryTests(unittest.TestCase):
    def test_missing_is_honest_refusal(self):
        with self.assertRaisesRegex(ComponentRefusal, "not declared") as cm:
            ComponentRegistry().resolve([{"instance": "first", "component": {"id": "missing.engine", "version": 1}, "material": {}}])
        self.assertEqual(cm.exception.code, "missing-capability")

    def test_export_is_immutable_and_defensive(self):
        r=ComponentRegistry(); d=descriptor(); ref=r.register(d)
        d["material_schema"]={"type":"number"}
        self.assertEqual(r.inspect(ref)["descriptor"]["material_schema"]["type"],"object")
        altered=descriptor(); altered["implementation"]["revision"]=2
        with self.assertRaises(ComponentRefusal) as cm:r.register(altered)
        self.assertEqual(cm.exception.code,"immutable-export")
        altered["version"]=2; self.assertEqual(r.register(altered)["version"],2)
        exposed=r.inspect(ref);exposed["descriptor"]["actions"].clear()
        self.assertIn("replace",r.inspect(ref)["descriptor"]["actions"])

    def test_exact_text_empty_and_literal_characters(self):
        r=ComponentRegistry();ref=r.register(descriptor())
        for value in ('', '  print("hi")\n\t$& \\end  '):
            result=r.validate_action(ref,"replace",{"value":value})
            self.assertEqual(result["args"]["value"],value)
            self.assertFalse(result["executable"])

    def test_undeclared_actions_bad_types_and_callbacks_refuse(self):
        r=ComponentRegistry();ref=r.register(descriptor())
        for action,args in (("delete",{}),("replace",{"value":12})):
            with self.assertRaises(ComponentRefusal):r.validate_action(ref,action,args)
        d=descriptor();d["callback"]=lambda:None
        with self.assertRaises(ComponentRefusal) as cm:r.register(d)
        self.assertEqual(cm.exception.code,"non-json")

    def test_second_domain_resolves_without_registry_or_compiler_change(self):
        paths=[Path(__file__).with_name("component_registry.py"),Path(__file__).with_name("frame_contract.py")]
        self.assertTrue(all(p.exists() for p in paths),"Compiler file must exist for freeze evidence")
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        r=ComponentRegistry();first=r.register(descriptor())
        r.resolve([{"instance":"code","component":first,"material":{"text":"x"}}])
        second=descriptor("research.timed-clip")
        second["material_schema"]=record({"time": {"type":"number","minimum":0},"playing":{"type":"boolean"}})
        second["actions"]={"seek":{"input_schema":record({"time":{"type":"number","minimum":0}}),"effect":"view"}}
        ref=r.register(second)
        result=r.resolve([{"instance":"clip","component":ref,"material":{"time":1.25,"playing":False}}])
        self.assertEqual(result[0]["contract"]["status"],"declared-not-loaded")
        self.assertEqual(r.validate_action(ref,"seek",{"time":3})["args"],{"time":3})
        self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__=="__main__":unittest.main()
