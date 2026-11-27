"use strict";

const localeNames = {
  en: "English", "zh-CN": "简体中文", "zh-TW": "繁體中文", es: "Español",
  fr: "Français", de: "Deutsch", "pt-BR": "Português (Brasil)", it: "Italiano",
  ja: "日本語", ko: "한국어", ru: "Русский", ar: "العربية", hi: "हिन्दी", id: "Bahasa Indonesia"
};
const languageKey = "tokenscope-language";

function resolveLanguage(preferences) {
  for (const tag of preferences) {
    let locale;
    try { locale = new Intl.Locale(tag); } catch { continue; }
    if (locale.language === "zh") return locale.maximize().script === "Hant" ? "zh-TW" : "zh-CN";
    if (locale.language === "pt") return "pt-BR";
    if (Object.hasOwn(localeNames, locale.language)) return locale.language;
  }
  return "en";
}

function readLanguage() {
  try {
    const value = localStorage.getItem(languageKey);
    if (Object.hasOwn(localeNames, value)) return value;
  } catch {}
  return "auto";
}

let preference = readLanguage();
let language;
let numbers, shortNumbers, timestamps, weekdays, monthDays, minutes, percent;

function selectLanguage(value) {
  preference = Object.hasOwn(localeNames, value) ? value : "auto";
  try {
    if (preference === "auto") localStorage.removeItem(languageKey);
    else localStorage.setItem(languageKey, preference);
  } catch {}
  updateLanguage();
}

function updateLanguage() {
  language = preference === "auto"
    ? resolveLanguage([...(navigator.languages || []), navigator.language])
    : preference;
  document.documentElement.lang = language;
  document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  numbers = new Intl.NumberFormat(language, {maximumFractionDigits: 0});
  shortNumbers = new Intl.NumberFormat(language, {notation: "compact", maximumFractionDigits: 2});
  timestamps = new Intl.DateTimeFormat(language, {dateStyle: "short", timeStyle: "medium"});
  weekdays = new Intl.DateTimeFormat(language, {weekday: "narrow", timeZone: "UTC"});
  monthDays = new Intl.DateTimeFormat(language, {month: "numeric", day: "numeric", timeZone: "UTC"});
  minutes = new Intl.NumberFormat(language, {style: "unit", unit: "minute", unitDisplay: "short"});
  percent = new Intl.NumberFormat(language, {style: "percent", maximumFractionDigits: 2});
}

function t(key, values = {}) {
  const pattern = messages[language][key] ?? messages.en[key] ?? key;
  return pattern.replace(/\{(\w+)\}/g, (match, name) => values[name] ?? match);
}

function translatePage() {
  for (const node of document.querySelectorAll("[data-i18n]")) {
    const value = node.dataset.count;
    node.textContent = t(node.dataset.i18n, value ? {n: numbers.format(value)} : {});
  }
  for (const node of document.querySelectorAll("[data-i18n-aria]"))
    node.setAttribute("aria-label", t(node.dataset.i18nAria));
  for (const node of document.querySelectorAll("[data-i18n-placeholder]"))
    node.placeholder = t(node.dataset.i18nPlaceholder);
  document.title = "TokenScope · " + t("overview");
  const picker = document.getElementById("language");
  picker.replaceChildren(new Option(t("auto"), "auto"), ...Object.entries(localeNames).map(([id, name]) => {
    const option = new Option(name, id);
    option.lang = id;
    return option;
  }));
  picker.value = preference;
}

function accountLabel(name) {
  if (name === "当前 Codex") return t("localCodex");
  if (name === "本机 Claude") return t("localClaude");
  return name;
}

function modelLabel(name) {
  if (name === "未分模型") return t("unspecified");
  return name === "未知" ? t("unknown") : name;
}

// Stored collector messages also occur in databases created before localization.
// Keep the original diagnostic available when copying or inspecting a failure.
function statusLabel(raw) {
  if (!raw || language === "zh-CN") return raw || "";
  let match = raw.match(/^已获取 (\d+) 个日期$/);
  if (match) return t("recordedDays", {n: numbers.format(match[1])});
  match = raw.match(/^(\d+) 个文件 · 新增 (\d+) 条 · 跳过异常 (\d+) 处$/);
  if (match) return t("scan", {n:numbers.format(match[1]), m:numbers.format(match[2]), s:numbers.format(match[3])});
  if (raw.startsWith("登录已完成。")) return t("signIn") + " ✓ · " + statusLabel(raw.slice(6));
  if (!/\p{Script=Han}/u.test(raw)) return raw;
  match = raw.match(/^第 (\d+) 条记录：(.*)$/);
  if (match) return "#" + numbers.format(match[1]) + " · " + statusLabel(match[2]);
  const rules = [
    [/等待同步/, "waiting"], [/已连接云端/, "connectedEmpty"], [/此账号已暂停/, "paused"],
    [/未找到可用的本机 Codex/, "installHint"], [/在官方页面完成登录/, "loginWait"],
    [/正在连接 Codex/, "openingLogin"], [/正在同步/, "syncing"], [/已取消登录/, "loginCancelled"],
    [/超时/, "timeout"], [/尚未登录|尚未创建|登录已失效|登录未完成/, "signIn"],
    [/服务限流/, "limited"], [/拒绝访问|权限|日志读取失败/, "access"],
    [/身份|账号已切换|已关联其他|其他登录方式/, "changeAccount"],
    [/已有目录的绝对路径/, "badFolder"], [/账号名称或配置目录已存在/, "duplicate"], [/请选择采集来源/, "chooseSource"],
    [/登录|Codex|连接失败|云端采集|额度快照|账号云端汇总/, "badClient"],
    [/格式|导入|记录|字段|Token|整数|JSON|CSV|timestamp/, "badData"],
    [/日期范围|时间范围/, "badDate"], [/版本未知/, "unknown"]
  ];
  const key = rules.find(([pattern]) => pattern.test(raw))?.[1] || "requestFailed";
  const code = raw.match(/WinError \d+|HTTP \d{3}|-32601/);
  return t(key) + (code ? " (" + code[0] + ")" : "");
}

updateLanguage();
