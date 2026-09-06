"""Authored programs used only as independent examples in disposable-world tests."""

from kernel import verbs

COUNTER = """({
 render(c) {return {id:'counter',tag:'button',text:String(c.state.count),on:{click:'inc'}}},
 handle(c,e) {return {state:{count:c.state.count+1}}},
 actions:{increment(c,a){return {
   state:{count:c.state.count+a.amount},value:c.state.count+a.amount}}}
})"""

DRAG = """({
 render(c) {
   const scene=c.objects.ent_desk.facets['core.scene'].body.appearances;
   const notes=Object.values(c.objects).filter(o=>o.facets['core.text']);
   return {id:'board',tag:'div',style:{position:'relative',width:'100%',height:'100%'},children:[
     {id:'heading',tag:'h1',text:'My movable notes',style:{padding:'20px'}},
     ...notes.map((o,i)=>{
       const saved=scene.find(a=>a.entity===o.entity)?.transform || {x:24+i*240,y:100};
       const pos=c.local.drag?.entity===o.entity ? c.local.drag : saved;
       return {id:o.entity,tag:'div',entity:o.entity,
         style:{position:'absolute',left:pos.x+'px',top:pos.y+'px',width:'220px',padding:'18px',
                backgroundColor:'#fff6cc',border:'1px solid #d6bf71',borderRadius:'12px',
                cursor:'grab',userSelect:'none',touchAction:'none'},
         on:{pointerdown:'grab',pointermove:'move',pointerup:'drop',pointercancel:'cancel'},
         children:[{id:o.entity+'_title',tag:'h3',text:o.facets['core.name'].body.name},
                   {id:o.entity+'_body',tag:'p',text:o.facets['core.text'].body.text}]};
     })]};
 },
 handle(c,e) {
   const appearances=c.objects.ent_desk.facets['core.scene'].body.appearances;
   if(e.handler==='grab') {
     const t=appearances.find(a=>a.entity===e.entity)?.transform || {x:0,y:0};
     return {local:{drag:{entity:e.entity,x:t.x,y:t.y,dx:e.x-t.x,dy:e.y-t.y}},selected:e.entity};
   }
   if(e.handler==='cancel') return {local:{}};
   const d=c.local.drag;
   if(!d) return {};
   const x=Math.max(0,Math.min(c.viewport.width-220,e.x-d.dx));
   const y=Math.max(0,Math.min(c.viewport.height-120,e.y-d.dy));
   if(e.handler==='move') return {local:{drag:{...d,x,y}}};
   if(e.handler==='drop') return {local:{},effects:[{verb:'place',args:{entity:d.entity,
     scene:'ent_desk',transform:{x,y,scale:1}}}]};
   return {};
 }
})"""


def counter():
    return {
        "version": 1,
        "title": "Counter",
        "source": COUNTER,
        "bindings": {},
        "permissions": {"state": True},
        "state_schema": {"count": "integer"},
        "initial_state": {"count": 0},
        "actions": {
            "increment": {"description": "Increment this counter", "params": {"amount": "integer"}}
        },
    }


def drag(world):
    verbs.ensure_desk(world)
    refs = []
    for index, (title, text) in enumerate(
        (("Garden notes", "Plant rosemary."), ("Reading list", "Read chapter three."))
    ):
        ref = verbs.mint(world, "alex", {"core.name": {"name": title}, "core.text": {"text": text}})
        verbs.place(world, "alex", ref, transform={"x": 24 + index * 240, "y": 100})
        refs.append(ref)
    definition = {
        "version": 1,
        "title": "Movable notes",
        "source": DRAG,
        "bindings": {"ent_desk": ["core.scene"], **{r: ["core.name", "core.text"] for r in refs}},
        "permissions": {"place": {"scene": "ent_desk", "entities": refs}},
        "state_schema": {},
        "initial_state": {},
        "actions": {},
    }
    return refs, definition


def click_cases(count=1):
    return [{"event": {"node": "counter", "type": "click"}, "expect": {"state": {"count": count}}}]


def drag_cases(ref):
    return [
        {
            "event": {"node": ref, "type": "pointerdown", "x": 40, "y": 115},
            "expect": {"effect_count": 0},
        },
        {
            "event": {"node": ref, "type": "pointermove", "x": 180, "y": 230},
            "expect": {"effect_count": 0},
        },
        {
            "event": {"node": ref, "type": "pointerup", "x": 180, "y": 230},
            "expect": {
                "effect_count": 1,
                "placement": {
                    "scene": "ent_desk",
                    "entity": ref,
                    "transform": {"x": 164, "y": 215},
                },
            },
        },
    ]
