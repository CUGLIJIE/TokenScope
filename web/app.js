"use strict";
const $ = id => document.getElementById(id);
const nf = new Intl.NumberFormat("zh-CN",{maximumFractionDigits:0});
const num = n => nf.format(n);
const compact = n => n>=1e8 ? +(n/1e8).toFixed(2)+" 亿" : n>=1e4 ? +(n/1e4).toFixed(2)+" 万" : num(n);
let view="cloud", report, busy=false, requestSeq=0, settings=false;
let cloudProfiles=[], cloudRevision="";
function el(tag,txt,cls){
  const n=document.createElement(tag);
  if(txt!==undefined)n.textContent=txt;
  if(cls)n.className=cls;
  return n;
}
function say(text){$("notice").textContent=text;$("notice").hidden=!text;}
async function api(path,data){
  const res=await fetch(path,data===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json","X-TokenScope-Request":"1"},body:JSON.stringify(data)});
  const json=await res.json();
  if(!res.ok)throw new Error(json.error||"请求失败");
  return json;
}
function safe(fn){return async (...args)=>{try{await fn(...args);}catch(e){say(e.message);}};}
function params(){const p=new URLSearchParams({view});for(const k of ["range","start","end","tool","account","model"])if($(k).value)p.set(k,$(k).value);return p;}
function dayNow(){const d=new Date(); return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);}
function options(key,values){
  const box=$(key),old=box.value;
  const def=key==="model"&&view==="cloud"?"未分模型":"全部"+({tool:"工具",account:"账号",model:"模型"}[key]);
  box.replaceChildren(new Option(def,""),...values.filter(v=>key!=="model"||view!=="cloud").map(v=>new Option(v,v)));
  if([...box.options].some(o=>o.value===old))box.value=old;
  box.disabled=key==="model"&&view==="cloud";
}
async function refresh(){
  const seq=++requestSeq;
  const r=await api("/api/report?"+params());
  if(seq!==requestSeq)return;
  report=r;
  Object.entries(r.dims).forEach(([k,v])=>options(k,v));
  const rows=[["Token 总量",r.total,"选中范围内的已记录用量"],["日均用量",r.average,"按 "+r.span+" 个日历日计算"],["单日峰值",r.peak,"选中范围内最高的一天"],["活跃天数",r.active,"有 Token 消耗的日期"]];
  $("metrics").replaceChildren(...rows.map(([name,value,caption],i)=>{
    const n=el("section"),strong=el("strong",value==null?"—":i===3?num(value)+" 天":compact(value));
    strong.title=value==null?"尚无可统计的云端日记录":num(value);
    n.append(el("div",name,"kpi-title"),strong,el("small",value==null?"所选区间缺少云端日记录":caption));return n;
  }));
  renderCloudStatus();
  $("chart-range").textContent=r.start+" — "+r.end+" · "+r.reported+" 天有记录";
  $("parts").textContent=r.parts?["输入 "+num(r.parts.input_tokens),"其中缓存读取 "+num(r.parts.cached_tokens),"缓存写入 "+num(r.parts.cache_write_tokens),"输出 "+num(r.parts.output_tokens)].join("　·　"):"云端提供每日总量，未提供每日模型、输入、输出和缓存拆分。";
  $("records").textContent=view==="cloud"?"日记录数":"事件数";
  const body=$("groups");body.replaceChildren(...r.groups.map(g=>{const row=el("tr");for(const v of [g.account,g.tool,g.model,num(g.records),num(g.tokens)])row.append(el("td",v));return row;}));
  if(!r.groups.length){const cell=el("td","所选范围暂无记录");cell.colSpan=5;const row=el("tr");row.append(cell);body.append(row);}
  plots();
}
function svg(tag,attrs,txt){
  const n=document.createElementNS("http://www.w3.org/2000/svg",tag);
  for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);
  if(txt!==undefined)n.textContent=txt;
  return n;
}
function graph(id,trend){
  const box=$(id),days=report.daily;
  if(!report.reported){box.replaceChildren(el("div","此范围暂无用量记录","empty"));return;}
  const W=Math.max(230,box.clientWidth),H=box.clientHeight||150,L=50,R=12,T=12,B=24;
  const n=svg("svg",{viewBox:"0 0 "+W+" "+H,role:"img","aria-label":trend?"逐月累计趋势":"每日 Token 柱状图"});
  let running=0,month="";
  const values=days.map(d=>{const m=d.day.slice(0,7);if(m!==month){running=0;month=m;}running+=d.value||0;return trend?running:d.value;});
  const max=Math.max(1,...values);
  const x=i=>L+(i+.5)*(W-L-R)/days.length;
  const y=v=>H-B-(H-B-T)*v/max;
  for(const f of [0,.5,1]){
    n.append(svg("line",{x1:L,y1:y(max*f),x2:W-R,y2:y(max*f),stroke:"var(--grid)","stroke-dasharray":f?"3 4":"0"}));
    n.append(svg("text",{x:L-6,y:y(max*f)+3,"text-anchor":"end"},compact(max*f)));
  }
  let series=[];
  function line(){if(series.length){n.append(svg("polyline",{points:series.join(" "),fill:"none",stroke:"var(--bar)","stroke-width":2.5,"stroke-linejoin":"round"}));series=[];}}
  days.forEach((d,i)=>{
    const value=values[i],px=x(i);
    if(trend){
      if(i&&days[i-1].day.slice(0,7)!==d.day.slice(0,7))line();
      series.push(px+","+y(value));
      if(days.length<=400){const dot=svg("circle",{cx:px,cy:y(value),r:days.length<=35?2.4:1.5,fill:"var(--bar)"});dot.append(svg("title",{},d.day+" · "+num(value)));n.append(dot);}
    }else if(value!==null){
      const w=Math.min(34,(W-L-R)/days.length*.75);
      const bar=svg("rect",{x:px-w/2,y:y(value),width:w,height:Math.max(value?1:0,H-B-y(value)),rx:Math.min(w/4,3),fill:"var(--bar)"});
      bar.append(svg("title",{},d.day+" · "+num(value)+" Token"));n.append(bar);
    }
  });
  line();
  const labels=Math.min(days.length,Math.max(2,Math.floor((W-L-R)/100)));
  for(let j=0;j<labels;j++){const i=Math.round(j*(days.length-1)/Math.max(1,labels-1));
    n.append(svg("text",{x:x(i),y:H-3,"text-anchor":i===0?"start":i===days.length-1?"end":"middle"},days[i].day.slice(5)));}
  box.replaceChildren(n);
}
function plots(){
  if(!report||settings)return;
  graph("bars",false);graph("trend",true);
  const heat=$("heat");heat.replaceChildren();
  const first=new Date(report.start+"T00:00:00Z");
  const offset=(first.getUTCDay()+6)%7;
  for(const [i,s] of [[0,"一"],[2,"三"],[4,"五"],[6,"日"]]){
    const label=el("span",s,"weekday");label.style.gridArea=(i+2)+" / 1";heat.append(label);
  }
  const fragment=document.createDocumentFragment();
  for(const [i,d] of report.daily.entries()){
    const cell=el("span",undefined,"tile");
    const week=Math.floor((i+offset)/7),weekday=(i+offset)%7;
    cell.style.gridArea=(weekday+2)+" / "+(week+2);
    if(i===0||weekday===0&&week%4===0){
      const stamp=el("span",d.day.slice(5),"weekstamp");stamp.style.gridArea="1 / "+(week+2);fragment.append(stamp);
    }
    const intensity=(d.value||0)/Math.max(report.peak,1);
    if(intensity>0)cell.style.background=intensity>.75?"#167654":intensity>.4?"#55a780":intensity>.15?"#86c89d":"#b6dfc2";
    cell.title=d.day+" · "+(d.value===null?"无记录":num(d.value)+" Token");
    fragment.append(cell);
  }
  heat.append(fragment);
}
function timeLabel(v){return v?new Date(v).toLocaleString("zh-CN",{hour12:false}):"尚无成功记录";}
function copyCloudStatus(p){
  const button=el("button","复制云端诊断");
  button.onclick=safe(async()=>{
    const version=(p.cloud_client||"").split(" · ");
    const lines=["TokenScope 1.4 · 云端诊断","状态："+p.cloud_status,
      "最近尝试："+(p.cloud_attempt||"尚无记录"),"上次成功："+(p.cloud_at||"尚无记录"),
      "Codex 版本："+(version.length>1?version[0]:"未识别"),"已保存日记录："+(p.days_saved||0)];
    if(p.rates.error)lines.push("额度查询："+p.rates.error);
    await navigator.clipboard.writeText(lines.join("\n"));say("云端诊断已复制。");
  });
  return button;
}
function renderCloudStatus(){
  const box=$("cloud-overview");
  box.hidden=view!=="cloud";
  if(box.hidden)return;
  const selected=cloudProfiles.filter(p=>!$("account").value||p.name===$("account").value);
  box.replaceChildren(...selected.map(p=>{
    const row=el("div",undefined,"cloud-row");
    const lifetime=p.summary.lifetimeTokens;
    row.append(el("strong",p.name+" · 账号历史累计 "+(lifetime==null?"尚未取得":num(lifetime)+" Token")));
    row.append(el("p",(!p.enabled?"采集已暂停 · ":"")+p.cloud_status+"　｜　上次成功 "+timeLabel(p.cloud_at)));
    const info=[p.account_hint,p.days_saved?"已保存 "+p.days_saved+" 天（"+p.first_day+" 至 "+p.last_day+"）":"尚无已保存的云端日记录"];
    row.append(el("small",info.filter(Boolean).join(" · ")));
    if(p.days_saved&&report?.reported===0&&$("range").value!=="all"){
      const all=el("button","查看全部日期");
      all.onclick=safe(async()=>{$("range").value="all";$("start-wrap").hidden=$("end-wrap").hidden=true;await refresh();});row.append(all);
    }
    if(!p.days_saved||p.auth_action||!p.enabled){
      const action=el("button",p.enabled&&p.auth_action?(p.auth_action==="install"?"安装 ChatGPT 桌面版":"登录 ChatGPT"):"查看账号与客户端");
      action.onclick=()=>p.enabled&&p.auth_action?showAuth(p):navigate(true);row.append(action,copyCloudStatus(p));
    }
    return row;
  }));
  if(!selected.length)box.append(el("p","尚未配置云端账号。可在「账号与数据」添加 Codex 云端来源。"));
}
const prompted=new Set();
let authProfile, loginTask={}, previousTicket="", issuing=false;
const authBox=$("auth-dialog");
function loginActive(){return ["starting","waiting","syncing"].includes(loginTask.state);}
function authControls(){
  const active=loginActive();
  $("auth-start").disabled=issuing||active;
  $("auth-cancel").hidden=!active||loginTask.profile!==authProfile?.id||loginTask.state==="syncing";
  $("auth-later").textContent=active?"后台等待":"稍后";
}
function showAuth(p){
  authProfile=p;
  prompted.add(p.id+":"+p.auth_action);
  const install=p.auth_action==="install";
  $("auth-title").textContent=install?"安装 ChatGPT 桌面版":"登录 ChatGPT";
  $("auth-description").textContent=install?"云端同步需要本机的 Codex 客户端。请安装 ChatGPT Windows 桌面版并打开一次，然后回到此处重新检测。也可以点「稍后」继续查看本地数据。":
    "使用 ChatGPT 连接「"+p.name+"」。请在官方页面完成登录，返回后会自动同步用量。";
  $("auth-message").textContent=loginActive()?loginTask.message:"";
  $("auth-start").textContent=install?"已安装，重新检测":"打开官方登录页";
  const link=$("auth-link");link.removeAttribute("href");link.hidden=!install;
  if(install){link.href="https://apps.microsoft.com/detail/9plm9xgg6vks";link.textContent="前往 Microsoft Store 安装 ChatGPT ↗";}
  authControls();
  if(!authBox.open)authBox.showModal();
}
$("auth-later").onclick=()=>authBox.close();
$("auth-cancel").onclick=safe(async()=>{await api("/api/login/cancel",{ticket:loginTask.ticket});await status();});
$("auth-start").onclick=safe(async()=>{
  if(authProfile.auth_action==="install"){
    await api("/api/sync",{});prompted.delete(authProfile.id+":install");
    authBox.close();await status();return;
  }
  issuing=true;authControls();
  const popup=window.open("about:blank","_blank");
  if(popup)popup.opener=null;
  $("auth-message").textContent="正在请求官方登录页…";
  try{
    const result=await api("/api/login",{id:authProfile.id});
    if(result.url){
      const link=$("auth-link");link.href=result.url;link.textContent="重新打开官方登录页 ↗";link.hidden=false;
      if(popup&&!popup.closed)popup.location.replace(result.url);
    }else if(popup)popup.close();
    await status();
  }catch(err){
    if(popup&&!popup.closed)popup.close();
    $("auth-message").textContent=err.message;
  }finally{issuing=false;authControls();}
});
async function status(){
  const data=await api("/api/status"),was=busy;busy=data.busy;
  cloudProfiles=data.profiles.filter(p=>p.cloud);
  const revision=JSON.stringify(cloudProfiles.map(p=>[p.id,p.cloud_at,p.cloud_status,p.days_saved,p.summary.lifetimeTokens]));
  const changed=cloudRevision!==""&&cloudRevision!==revision;
  cloudRevision=revision;renderCloudStatus();
  loginTask=data.login||{};
  $("sync-state").textContent=busy?"正在采集…":"";
  $("sync").disabled=busy;
  $("profiles").replaceChildren(...data.profiles.map(p=>{
    const card=el("div",undefined,"profile"),head=el("div",undefined,"profile-head");
    head.append(el("h2",p.name),el("span",p.tool,"tag"));const toggle=el("button",p.enabled?"暂停采集":"启用采集");
    toggle.onclick=safe(async()=>{await api("/api/toggle",{id:p.id});await status();});
    head.append(toggle);card.append(head,el("div",p.root,"path"));
    if(p.enabled&&p.cloud&&p.auth_action){
      const enter=el("button",p.auth_action==="install"?"安装 ChatGPT 桌面版":"登录 ChatGPT");
      enter.onclick=()=>showAuth(p);card.append(enter);
    }
    if(p.cloud){card.append(el("p","云端 · "+p.cloud_status+"　｜　上次成功 "+timeLabel(p.cloud_at)));
      if(p.cloud_client)card.append(el("small","Codex 客户端 · "+p.cloud_client));
      if(p.cloud_attempt)card.append(el("small","最近尝试 · "+timeLabel(p.cloud_attempt)));
      if(p.account_hint)card.append(el("small","最近核对的登录账号 · "+p.account_hint));
      card.append(copyCloudStatus(p));
      if(p.summary.lifetimeTokens!=null)card.append(el("div","账号历史累计 "+num(p.summary.lifetimeTokens)+" Token　·　历史单日峰值 "+(p.summary.peakDailyTokens==null?"未知":num(p.summary.peakDailyTokens))));
      for(const k of ["primary","secondary"]){const r=p.rates[k];if(r)card.append(el("small",(r.windowDurationMins==null?"额度窗口":r.windowDurationMins+" 分钟窗口")+" · 已用 "+(r.usedPercent??"未知")+"%"+(r.resetsAt?" · 重置于 "+timeLabel(r.resetsAt*1000):"")));}
      if(p.rates.error)card.append(el("small","额度 · "+p.rates.error));
      if(p.rates.updated_at)card.append(el("small","额度快照 · "+timeLabel(p.rates.updated_at)));
    }
    if(p.logs)card.append(el("p","本机 · "+p.log_status+"　｜　上次扫描 "+timeLabel(p.logs_at)));
    return card;
  }));
  if((was&&!busy)||changed){await refresh();if(was&&!busy)say("本轮同步已结束。");}
  if(authBox.open){
    authControls();
    if(loginTask.profile===authProfile.id&&loginActive())$("auth-message").textContent=loginTask.message;
  }
  if(loginTask.ticket&&!loginActive()&&previousTicket!==loginTask.ticket){
    previousTicket=loginTask.ticket;say(loginTask.message);
    if(authBox.open&&authProfile.id===loginTask.profile){
      $("auth-message").textContent=loginTask.message;
      $("auth-link").hidden=true;$("auth-link").removeAttribute("href");
      if(loginTask.state==="done")authBox.close();
    }
    await refresh();
  }
  if(!busy&&!issuing&&!loginActive()&&!authBox.open&&!$("dialog").open){
    const pending=data.profiles.find(p=>p.enabled&&p.cloud&&p.auth_action&&!prompted.has(p.id+":"+p.auth_action));
    if(pending)showAuth(pending);
  }
}
function navigate(toSettings){
  settings=toSettings;$("dashboard").hidden=settings;$("settings").hidden=!settings;
  $("nav-home").classList.toggle("selected",!settings);$("nav-data").classList.toggle("selected",settings);
  $("heading").textContent=$("crumb").textContent=settings?"账号与数据":"用量总览";
  if(!settings)plots();
}
function switchView(next){
  view=next;$("cloud-tab").classList.toggle("on",view==="cloud");$("detail-tab").classList.toggle("on",view==="detail");
  for(const k of ["tool","account","model"])$(k).value="";
  return refresh();
}
$("nav-home").onclick=()=>navigate(false);$("nav-data").onclick=safe(async()=>{navigate(true);await status();});
$("cloud-tab").onclick=safe(()=>switchView("cloud"));$("detail-tab").onclick=safe(()=>switchView("detail"));
$("start").value=$("end").value=dayNow();
for(const k of ["range","start","end","tool","account","model"])$(k).onchange=safe(async()=>{
  $("start-wrap").hidden=$("end-wrap").hidden=$("range").value!=="custom";
  if($("range").value==="custom"&&$("start").value>$("end").value){say("开始日期须早于或等于结束日期。");return;}say("");await refresh();
});
for(const fmt of ["json","csv"])$(fmt).onclick=()=>{location.href="/api/export?"+params()+"&format="+fmt;};
const theme=localStorage.getItem("tokenscope-theme")||localStorage.getItem("atlas-theme")||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
document.documentElement.dataset.theme=theme;
$("theme").onclick=()=>{const t=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=t;localStorage.setItem("tokenscope-theme",t);};
$("sync").onclick=safe(async()=>{await api("/api/sync",{});busy=true;await status();});
$("new-profile").onclick=()=>{$("form-error").textContent="";$("dialog").showModal();};$("cancel").onclick=()=>$("dialog").close();
const form=$("form");form.elements.tool.onchange=()=>{form.elements.cloud.disabled=form.elements.tool.value!=="Codex";};
form.onsubmit=async e=>{e.preventDefault();const f=form.elements;
  try{await api("/api/profile",{name:f.name.value,root:f.root.value,tool:f.tool.value,cloud:f.cloud.checked&&!f.cloud.disabled,logs:f.logs.checked});$("dialog").close();form.reset();f.cloud.disabled=false;await status();say("账号已添加。点击「同步数据」可立即采集。");}catch(err){$("form-error").textContent=err.message;}
};
$("file").onchange=safe(async e=>{const file=e.target.files[0];if(!file)return;
  try{if(file.size>10*1024*1024)throw new Error("单次导入上限 10 MiB");
    const res=await api("/api/import",{format:file.name.split(".").pop().toLowerCase(),content:await file.text()});
    $("import-result").textContent="已读取 "+res.read+" 条，新增 "+res.added+" 条。请在「本地与导入」查看。";await refresh();
  }finally{e.target.value="";}
});
let resizeTimer;window.addEventListener("resize",()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(plots,160);});
safe(async()=>{await status();await refresh();})();
const poll=setInterval(safe(status),4000);
$("stop-service").onclick=safe(async()=>{
  if(!confirm("退出 TokenScope 本地服务？已同步的数据会保留。"))return;
  await api("/api/stop",{});clearInterval(poll);
  say("本地服务已退出。再次打开 TokenScope 可继续使用。");
  document.querySelectorAll("button,select,input").forEach(n=>n.disabled=true);
});

