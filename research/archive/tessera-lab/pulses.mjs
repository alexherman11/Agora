// One authority schedules contributed clocks; browsers never own simulation time.
// No catch-up bursts, callbacks, or repeated dispatch of a refused pulse.
import {canonical} from './engine.mjs';

export class PulseRunner {
  constructor(){this.schedules=new Map();this.diagnostics=[];}
  pump(engine,now){
    const live=new Set(Object.keys(engine.program.pulse));
    for(const id of this.schedules.keys())if(!live.has(id))this.schedules.delete(id);
    const due=[];
    for(const p of Object.values(engine.program.pulse)){
      const definition=canonical(p);let s=this.schedules.get(p.id);
      if(!s||s.definition!==definition){s={definition,active:false,next:Infinity,blocked:null};this.schedules.set(p.id,s);}
      try{
        if(!Number.isFinite(p.everyMs)||p.everyMs<50||p.everyMs>60000)throw Error('Pulse everyMs must be between 50 and 60000');
        const active=p.when===undefined||!!engine.eval(p.when);
        if(!active){s.active=false;s.blocked=null;s.next=Infinity;continue;}
        if(!s.active){s.active=true;s.next=now+p.everyMs;}
        if(!s.blocked&&now>=s.next){due.push({pulse:p,schedule:s,request:{action:p.action,args:engine.eval(p.args??{})}});s.next=now+p.everyMs;}
      }catch(e){s.blocked={code:'pulse-definition',id:p.id,message:e.message};}
    }
    let receipt=null;
    if(due.length){
      const commands=due.map(d=>d.request),result=engine.dispatch(commands);
      receipt={pulses:due.map(d=>d.pulse.id),commands,result};
      if(!result.ok)for(const d of due)d.schedule.blocked={code:'pulse-refused',id:d.pulse.id,conflict:result.conflict};
    }
    this.diagnostics=[...this.schedules.values()].flatMap(s=>s.blocked?[s.blocked]:[]);
    return receipt;
  }
}
