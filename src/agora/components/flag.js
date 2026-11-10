export default {mount(api,s){
  return api.part('icon','span',{class:'flag','aria-label':'Priority '+s.priority,style:{color:['red','orange','blue','grey'].map(k=>api.P.tokens[k])[(+s.priority||4)-1]}},'⚑');
}};
