"use strict";
const $ = id => document.getElementById(id);
const num = n => numbers.format(n);
const compact = n => shortNumbers.format(n);
const shortDay = day => monthDays.format(new Date(day + "T00:00:00Z"));
translatePage();
let view="cloud", report, busy=false, requestSeq=0, settings=false;
let cloudProfiles=[], cloudRevision="";
function el(tag,txt,cls){
  const n=document.createElement(tag);
  if(txt!==undefined)n.textContent=txt;
  if(cls)n.className=cls;
  return n;
}
function say(text){$("notice").textContent=text;$("notice").title="";$("notice").hidden=!text;}
async function api(path,data){
  const res=await fetch(path,data===undefined?{}:{method:"POST",headers:{"Content-Type":"application/json","X-TokenScope-Request":"1"},body:JSON.stringify(data)});
  const json=await res.json();
  if(!res.ok){
    const error=new Error(statusLabel(json.error) || t("requestFailed"));
    error.detail=json.error;
    throw error;
  }
  return json;
}
function safe(fn){return async (...args)=>{try{await fn(...args);}catch(e){say(e.message);$("notice").title=e.detail||e.message;}};}
function params(){const p=new URLSearchParams({view});for(const k of ["range","start","end","tool","account","model"])if($(k).value)p.set(k,$(k).value);return p;}
function dayNow(){const d=new Date(); return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,10);}
function options(key,values){
  const box=$(key),old=box.value;
  const def=key==="model"&&view==="cloud"?t("unspecified"):t({tool:"allTools",account:"allAccounts",model:"allModels"}[key]);
  box.replaceChildren(new Option(def,""),...values.filter(v=>key!=="model"||view!=="cloud").map(v=>new Option(key==="model"?modelLabel(v):key==="account"?accountLabel(v):v,v)));
  if([...box.options].some(o=>o.value===old))box.value=old;
  box.disabled=key==="model"&&view==="cloud";
}
async function refresh(){
  const seq=++requestSeq;
  const r=await api("/api/report?"+params());
  if(seq!==requestSeq)return;
  report=r;
  renderReport(r);
}
function renderReport(r){
  Object.entries(r.dims).forEach(([k,v])=>options(k,v));
  const rows=[[t("total"),r.total,t("inRange")],[t("average"),r.average,t("calendarDays",{n:num(r.span)})],
    [t("peak"),r.peak,t("highest")],[t("active"),r.active,t("positive")]];
  $("metrics").replaceChildren(...rows.map(([name,value,caption],i)=>{
    const n=el("section"),strong=el("strong",value==null?"—":i===3?num(value):compact(value));
    strong.title=value==null?t("noCloud"):num(value);
    n.append(el("div",name,"kpi-title"),strong,el("small",value==null?t("noCloud"):caption));return n;
  }));
  renderCloudStatus();
  $("chart-range").textContent=r.start+" — "+r.end+" · "+t("recordedDays",{n:num(r.reported)});
  $("parts").textContent=r.parts?[["input","input_tokens"],["cacheRead","cached_tokens"],["cacheWrite","cache_write_tokens"],["output","output_tokens"]]
    .map(([label,key])=>t(label)+" "+num(r.parts[key])).join(" · "):t("cloudHint");
  $("records").textContent=t(view==="cloud"?"days":"events");
  const body=$("groups");body.replaceChildren(...r.groups.map(g=>{const row=el("tr");for(const v of [accountLabel(g.account),g.tool,modelLabel(g.model),num(g.records),num(g.tokens)])row.append(el("td",v));return row;}));
  if(!r.groups.length){const cell=el("td",t("noRecords"));cell.colSpan=5;const row=el("tr");row.append(cell);body.append(row);}
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
  if(!report.reported){box.replaceChildren(el("div",t("noRecords"),"empty"));return;}
  const W=Math.max(230,box.clientWidth),H=box.clientHeight||150,L=50,R=12,T=12,B=24;
  const n=svg("svg",{viewBox:"0 0 "+W+" "+H,role:"img","aria-label":t(trend?"trend":"daily")});
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
    n.append(svg("text",{x:x(i),y:H-3,"text-anchor":i===0?"start":i===days.length-1?"end":"middle"},shortDay(days[i].day)));}
  box.replaceChildren(n);
}
function plots(){
  if(!report||settings)return;
  graph("bars",false);graph("trend",true);
  const heat=$("heat");heat.replaceChildren();
  const first=new Date(report.start+"T00:00:00Z");
  const offset=(first.getUTCDay()+6)%7;
  for(const i of [0,2,4,6]){
    const s=weekdays.format(new Date(Date.UTC(2024,0,1+i)));
    const label=el("span",s,"weekday");label.style.gridArea=(i+2)+" / 1";heat.append(label);
  }
  const fragment=document.createDocumentFragment();
  for(const [i,d] of report.daily.entries()){
    const cell=el("span",undefined,"tile");
    const week=Math.floor((i+offset)/7),weekday=(i+offset)%7;
    cell.style.gridArea=(weekday+2)+" / "+(week+2);
    if(i===0||weekday===0&&week%4===0){
      const stamp=el("span",shortDay(d.day),"weekstamp");stamp.style.gridArea="1 / "+(week+2);fragment.append(stamp);
    }
    const intensity=(d.value||0)/Math.max(report.peak,1);
    if(intensity>0)cell.style.background=intensity>.75?"#167654":intensity>.4?"#55a780":intensity>.15?"#86c89d":"#b6dfc2";
    cell.title=d.day+" · "+(d.value===null?t("noRecords"):num(d.value)+" Token");
    fragment.append(cell);
  }
  heat.append(fragment);
}
function timeLabel(v){return v ? timestamps.format(new Date(v)) : t("noSuccess");}
function copyCloudStatus(p){
  const button=el("button",t("copy"));
  button.onclick=safe(async()=>{
    const version=(p.cloud_client||"").split(" · ");
    const lines=["TokenScope 1.4 · "+t("diagnostic"),t("status")+": "+statusLabel(p.cloud_status),
      t("attempt")+": "+timeLabel(p.cloud_attempt),t("success")+": "+timeLabel(p.cloud_at),
      "Codex: "+(version.length>1?version[0]:t("unknown")),t("recordedDays",{n:num(p.days_saved||0)})];
    if(p.rates.error)lines.push(t("quota")+": "+statusLabel(p.rates.error));
    for(const raw of [p.cloud_status,p.rates.error])if(raw&&statusLabel(raw)!==raw)lines.push(raw);
    await navigator.clipboard.writeText(lines.join("\n"));say(t("copied"));
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
    row.append(el("strong",accountLabel(p.name)+" · "+t("lifetime")+" · "+(lifetime==null?"—":num(lifetime))));
    const state=el("p",(!p.enabled?t("paused")+" · ":"")+statusLabel(p.cloud_status)+" · "+t("success")+" · "+timeLabel(p.cloud_at));
    state.title=p.cloud_status;row.append(state);
    const info=[p.account_hint,p.days_saved?t("recordedDays",{n:num(p.days_saved)})+" ("+p.first_day+" – "+p.last_day+")":t("noSaved")];
    row.append(el("small",info.filter(Boolean).join(" · ")));
    if(p.days_saved&&report?.reported===0&&$("range").value!=="all"){
      const all=el("button",t("allDates"));
      all.onclick=safe(async()=>{$("range").value="all";$("start-wrap").hidden=$("end-wrap").hidden=true;await refresh();});row.append(all);
    }
    if(!p.days_saved||p.auth_action||!p.enabled){
      const action=el("button",p.enabled&&p.auth_action?(p.auth_action==="install"?t("install"):t("signIn")):t("inspect"));
      action.onclick=()=>p.enabled&&p.auth_action?showAuth(p):navigate(true);row.append(action,copyCloudStatus(p));
    }
    return row;
  }));
  if(!selected.length)box.append(el("p",t("noAccount")));
}
const prompted=new Set();
let authProfile, loginTask={}, previousTicket="", issuing=false;
const authBox=$("auth-dialog");
function loginActive(){return ["starting","waiting","syncing"].includes(loginTask.state);}
function authControls(){
  const active=loginActive();
  $("auth-start").disabled=issuing||active;
  $("auth-cancel").hidden=!active||loginTask.profile!==authProfile?.id||loginTask.state==="syncing";
  $("auth-later").textContent=active?t("background"):t("later");
}
function showAuth(p){
  authProfile=p;
  prompted.add(p.id+":"+p.auth_action);
  const install=p.auth_action==="install";
  $("auth-title").textContent=install?t("install"):t("signIn");
  $("auth-description").textContent=install?t("installHint"):t("loginHint",{name:accountLabel(p.name)});
  $("auth-message").textContent=loginActive()?statusLabel(loginTask.message):"";
  $("auth-start").textContent=install?t("retry"):t("openLogin");
  const link=$("auth-link");link.removeAttribute("href");link.hidden=!install;
  if(install){link.href="https://apps.microsoft.com/detail/9plm9xgg6vks";link.textContent="Microsoft Store ↗";}
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
  $("auth-message").textContent=t("openingLogin");
  try{
    const result=await api("/api/login",{id:authProfile.id});
    if(result.url){
      const link=$("auth-link");link.href=result.url;link.textContent=t("openLogin")+" ↗";link.hidden=false;
      if(popup&&!popup.closed)popup.location.replace(result.url);
    }else if(popup)popup.close();
    await status();
  }catch(err){
    if(popup&&!popup.closed)popup.close();
    $("auth-message").textContent=err.message;$("auth-message").title=err.detail||err.message;
  }finally{issuing=false;authControls();}
});
let latestStatus;
function renderProfiles(data){
  $("sync-state").textContent=busy?t("syncing"):"";
  $("sync").disabled=busy;
  $("profiles").replaceChildren(...data.profiles.map(p=>{
    const card=el("div",undefined,"profile"),head=el("div",undefined,"profile-head");
    head.append(el("h2",accountLabel(p.name)),el("span",p.tool,"tag"));const toggle=el("button",p.enabled?t("pause"):t("enable"));
    toggle.onclick=safe(async()=>{await api("/api/toggle",{id:p.id});await status();});
    head.append(toggle);card.append(head,el("div",p.root,"path"));
    if(p.enabled&&p.cloud&&p.auth_action){
      const enter=el("button",p.auth_action==="install"?t("install"):t("signIn"));
      enter.onclick=()=>showAuth(p);card.append(enter);
    }
    if(p.cloud){
      const state=el("p",t("cloud")+" · "+statusLabel(p.cloud_status)+" · "+t("success")+" · "+timeLabel(p.cloud_at));
      state.title=p.cloud_status;card.append(state);
      if(p.cloud_client)card.append(el("small","Codex · "+p.cloud_client));
      if(p.cloud_attempt)card.append(el("small",t("attempt")+" · "+timeLabel(p.cloud_attempt)));
      if(p.account_hint)card.append(el("small",t("account")+" · "+p.account_hint));
      card.append(copyCloudStatus(p));
      if(p.summary.lifetimeTokens!=null)card.append(el("div",t("lifetime")+" · "+num(p.summary.lifetimeTokens)+" · "+t("peak")+" · "+(p.summary.peakDailyTokens==null?t("unknown"):num(p.summary.peakDailyTokens))));
      for(const k of ["primary","secondary"]){
        const r=p.rates[k];if(!r)continue;
        const window=r.windowDurationMins==null?t("quota"):minutes.format(r.windowDurationMins);
        card.append(el("small",window+" · "+t("used")+" "+(r.usedPercent==null?t("unknown"):percent.format(r.usedPercent/100))+(r.resetsAt?" · "+t("reset")+" "+timeLabel(r.resetsAt*1000):"")));
      }
      if(p.rates.error){const error=el("small",t("quota")+" · "+statusLabel(p.rates.error));error.title=p.rates.error;card.append(error);}
      if(p.rates.updated_at)card.append(el("small",t("quota")+" · "+timeLabel(p.rates.updated_at)));
    }
    if(p.logs){const scan=el("p",t("logs")+" · "+statusLabel(p.log_status)+" · "+t("lastScan")+" · "+timeLabel(p.logs_at));scan.title=p.log_status;card.append(scan);}
    return card;
  }));
}
async function status(){
  const data=await api("/api/status"),was=busy;busy=data.busy;
  cloudProfiles=data.profiles.filter(p=>p.cloud);
  const revision=JSON.stringify(cloudProfiles.map(p=>[p.id,p.cloud_at,p.cloud_status,p.days_saved,p.summary.lifetimeTokens]));
  const changed=cloudRevision!==""&&cloudRevision!==revision;
  cloudRevision=revision;renderCloudStatus();
  loginTask=data.login||{};
  latestStatus=data;renderProfiles(data);
  if((was&&!busy)||changed){await refresh();if(was&&!busy)say(t("synced"));}
  if(authBox.open){
    authControls();
    if(loginTask.profile===authProfile.id&&loginActive())$("auth-message").textContent=statusLabel(loginTask.message);
  }
  if(loginTask.ticket&&!loginActive()&&previousTicket!==loginTask.ticket){
    previousTicket=loginTask.ticket;say(statusLabel(loginTask.message));
    if(authBox.open&&authProfile.id===loginTask.profile){
      $("auth-message").textContent=statusLabel(loginTask.message);
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
  $("heading").textContent=$("crumb").textContent=settings?t("accounts"):t("overview");
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
  if($("range").value==="custom"&&$("start").value>$("end").value){say(t("badDate"));return;}say("");await refresh();
});
for(const fmt of ["json","csv"])$(fmt).onclick=()=>{location.href="/api/export?"+params()+"&format="+fmt;};
const theme=localStorage.getItem("tokenscope-theme")||localStorage.getItem("atlas-theme")||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
document.documentElement.dataset.theme=theme;
$("theme").onclick=()=>{const t=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=t;localStorage.setItem("tokenscope-theme",t);};
$("sync").onclick=safe(async()=>{await api("/api/sync",{});busy=true;await status();});
$("new-profile").onclick=()=>{$("form-error").textContent="";$("dialog").showModal();};$("cancel").onclick=()=>$("dialog").close();
const form=$("form");form.elements.tool.onchange=()=>{form.elements.cloud.disabled=form.elements.tool.value!=="Codex";};
form.onsubmit=async e=>{e.preventDefault();const f=form.elements;
  try{await api("/api/profile",{name:f.name.value,root:f.root.value,tool:f.tool.value,cloud:f.cloud.checked&&!f.cloud.disabled,logs:f.logs.checked});$("dialog").close();form.reset();f.cloud.disabled=false;await status();say(t("added"));}catch(err){$("form-error").textContent=err.message;$("form-error").title=err.detail||err.message;}
};
$("file").onchange=safe(async e=>{const file=e.target.files[0];if(!file)return;
  try{if(file.size>10*1024*1024)throw new Error(t("sizeLimit"));
    const res=await api("/api/import",{format:file.name.split(".").pop().toLowerCase(),content:await file.text()});
    $("import-result").textContent=t("imported",{n:num(res.read),m:num(res.added)});await refresh();
  }finally{e.target.value="";}
});
function renderLanguage(){
  translatePage();navigate(settings);
  if(report)renderReport(report);
  if(latestStatus)renderProfiles(latestStatus);
  if(authBox.open){
    const savedUrl=$("auth-link").href,hadLink=!$("auth-link").hidden;
    showAuth(authProfile);
    if(hadLink&&authProfile.auth_action!=="install"){
      $("auth-link").href=savedUrl;$("auth-link").textContent=t("openLogin")+" ↗";$("auth-link").hidden=false;
    }
  }
  say("");$("form-error").textContent="";$("import-result").textContent="";
}
$("language").addEventListener("change",event=>{selectLanguage(event.target.value);renderLanguage();});
window.addEventListener("languagechange",()=>{if(preference==="auto"){updateLanguage();renderLanguage();}});
let resizeTimer;window.addEventListener("resize",()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(plots,160);});
safe(async()=>{await status();await refresh();})();
const poll=setInterval(safe(status),4000);
$("stop-service").onclick=safe(async()=>{
  if(!confirm(t("stopConfirm")))return;
  await api("/api/stop",{});clearInterval(poll);
  say(t("stopped"));
  document.querySelectorAll("button,select,input").forEach(n=>n.disabled=true);
});

