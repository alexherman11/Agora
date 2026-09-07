const fs=require('fs');
const {chromium}=require('C:/Users/Alex/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
(async()=>{
 const token=JSON.parse(fs.readFileSync('C:/Projects/Agora3/worlds/dev/keep.json','utf8')).operator;
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:960}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8790/#'+token);
 await page.frameLocator('iframe').locator('.message.assistant').first().waitFor();
 const frame=page.frames()[1];
 const result=await frame.evaluate(async()=>({
  markdown:typeof marked.parse==='function' && !!DOMPurify.sanitize,
  assistantMessages:document.querySelectorAll('.message.assistant').length,
  formattedElements:document.querySelectorAll('.message.assistant strong,.message.assistant ul,.message.assistant pre').length,
  activitySnapshots:!!(await call('chat.status')).activity,
  notes:document.querySelectorAll('.note').length
 }));
 if(!result.markdown||!result.activitySnapshots||!result.assistantMessages||errors.length)throw Error(JSON.stringify({result,errors}));
 await page.screenshot({path:__dirname+'/chat-live.png'});
 console.log(JSON.stringify({...result,errors}));
 await browser.close();
})().catch(e=>{console.error(e.message);process.exit(1)});
