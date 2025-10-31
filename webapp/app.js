/* =========================================================
   VORN WebApp — Unified Core
   ========================================================= */

   

console.log("✅ app.js loaded (VORN unified)");

/* ------------ GLOBAL FLAGS ------------ */
const DEBUG_UI = false; // ⬅️ turn off the green debug box

/* ------------ API CONFIG ------------ */
const COOLDOWN_SEC = 6 * 60 * 60; // 6 ժամ
const REWARD = 500;

// always call the same origin where the WebApp is served (Render)
const API_BASE = window.location.origin;
const API = {
  user: (uid) => `${API_BASE}/api/user/${uid}`,
  mine: `${API_BASE}/api/mine`,
  mineClick: `${API_BASE}/api/mine_click`,
  vornReward: `${API_BASE}/api/vorn_reward`,
  vornExchange: `${API_BASE}/api/vorn_exchange`,
  tasks: (uid) => `${API_BASE}/api/tasks?uid=${uid}`,
  attemptCreate: `${API_BASE}/api/task_attempt_create`,
  attemptVerify: `${API_BASE}/api/task_attempt_verify`
};


/* ------------ HELPERS ------------ */
function uidFromURL() {
  try {
    const s = new URLSearchParams(window.location.search);
    return parseInt(s.get("uid") || "0", 10) || 0;
  } catch { return 0; }
}
function nowSec() { return Math.floor(Date.now() / 1000); }

/* ------------ I18N CORE ------------ */
const texts = {
  
  en: { confirmText: "You have chosen English for the entire experience.\nYou cannot change it later.", confirmBtn: "Confirm", changeBtn: "Change", eggTip: "🥚 Tap the egg to hatch it!" },
  ru: { confirmText: "Вы выбрали русский язык для всей игры.\nВы не сможете изменить его позже.", confirmBtn: "Подтвердить", changeBtn: "Изменить", eggTip: "🥚 Коснитесь яйца, чтобы разбить его!" },
  hy: { confirmText: "Դուք ընտրել եք հայերենը ամբողջ խաղի համար։\nԴուք չեք կարող այն փոխել։", confirmBtn: "Հաստատել", changeBtn: "Փոխել", eggTip: "🥚 Սեղմիր ձվի վրա՝ բացելու համար։" },
  fr: { confirmText: "Vous avez choisi le français pour toute l'expérience.\nVous ne pouvez pas le changer plus tard.", confirmBtn: "Confirmer", changeBtn: "Changer", eggTip: "🥚 Touchez l'œuf pour l'éclore !" },
  es: { confirmText: "Has elegido español para toda la experiencia.\nNo podrás cambiarlo después.", confirmBtn: "Confirmar", changeBtn: "Cambiar", eggTip: "🥚 ¡Toca el huevo para abrirlo!" },
  de: { confirmText: "Du hast Deutsch für das gesamte Spiel gewählt.\nDu kannst es später nicht ändern.", confirmBtn: "Bestätigen", changeBtn: "Ändern", eggTip: "🥚 Tippe auf das Ei, um es zu öffnen!" },
  it: { confirmText: "Hai scelto l'italiano per l'intera esperienza.\nNon puoi cambiarlo in seguito.", confirmBtn: "Conferma", changeBtn: "Cambia", eggTip: "🥚 Tocca l'uovo per aprirlo!" },
  tr: { confirmText: "Tüm deneyim için Türkçe'yi seçtiniz.\nDaha sonra değiştiremezsiniz.", confirmBtn: "Onayla", changeBtn: "Değiş", eggTip: "🥚 Yumurtaya dokun, kır!" },
  fa: { confirmText: "شما فارسی را برای کل بازی انتخاب کرده‌اید.\nبعداً نمی‌توانید آن را تغییر دهید.", confirmBtn: "تأیید", changeBtn: "تغییر", eggTip: "🥚 روی تخم مرغ بزنید!" },
  ar: { confirmText: "لقد اخترت العربية للتجربة بأكملها.\nلا يمكنك تغييره لاحقاً.", confirmBtn: "تأكيد", changeBtn: "تغيير", eggTip: "🥚 اضغط على البيضة لتفقس!" },
  zh: { confirmText: "您选择了中文。\n以后无法更改。", confirmBtn: "确认", changeBtn: "更改", eggTip: "🥚 点击蛋孵化！" },
  ja: { confirmText: "日本語を選択しました。\n後で変更できません。", confirmBtn: "確認", changeBtn: "変更", eggTip: "🥚 卵をタップして孵化！" },
  ko: { confirmText: "한국어를 선택했습니다.\n나중에 변경할 수 없습니다.", confirmBtn: "확인", changeBtn: "변경", eggTip: "🥚 알을 눌러 부화시키세요!" },
  hi: { confirmText: "आपने पूरी गेम के लिए हिंदी चुनी है।\nआप बाद में इसे नहीं बदल सकते।", confirmBtn: "पुष्टि करें", changeBtn: "बदलें", eggTip: "🥚 अंडे को टैप करें!" },
  pt: { confirmText: "Você escolheu o português.\nNão poderá mudar depois.", confirmBtn: "Confirmar", changeBtn: "Mudar", eggTip: "🥚 Toque no ovo para chocar!" },
  el: { confirmText: "Επέλεξες τα ελληνικά.\nΔεν μπορείς να το αλλάξεις μετά.", confirmBtn: "Επιβεβαίωση", changeBtn: "Αλλαγή", eggTip: "🥚 Πάτα το αυγό!" },
  pl: { confirmText: "Wybrałeś język polski.\nNie możesz tego zmienić później.", confirmBtn: "Potwierdź", changeBtn: "Zmień", eggTip: "🥚 Dotknij jajka!" },
  nl: { confirmText: "Je hebt Nederlands gekozen.\nJe kunt dit later niet wijzigen.", confirmBtn: "Bevestigen", changeBtn: "Wijzigen", eggTip: "🥚 Tik op het ei!" },
  sv: { confirmText: "Du valde svenska.\nDu kan inte ändra det senare.", confirmBtn: "Bekräfta", changeBtn: "Byt", eggTip: "🥚 Tryck på ägget!" },
  ro: { confirmText: "Ai ales româna.\nNu o poți schimba mai târziu.", confirmBtn: "Confirmă", changeBtn: "Schimbă", eggTip: "🥚 Atinge oul!" },
  hu: { confirmText: "Magyar nyelvet választottál.\nKésőbb nem módosíthatod.", confirmBtn: "Megerősít", changeBtn: "Módosít", eggTip: "🥚 Érintsd meg a tojást!" },
  cs: { confirmText: "Vybral jsi češtinu.\nNelze to později změnit.", confirmBtn: "Potvrdit", changeBtn: "Změnit", eggTip: "🥚 Klepni na vejce!" },
  uk: { confirmText: "Ви обрали українську.\nНе можна буде змінити.", confirmBtn: "Підтвердити", changeBtn: "Змінити", eggTip: "🥚 Торкніться яйця!" },
  az: { confirmText: "Siz Azərbaycan dilini seçdiniz.\nSonradan dəyişmək mümkün deyil.", confirmBtn: "Təsdiq et", changeBtn: "Dəyiş", eggTip: "🥚 Yumurtaya toxun!" },
  ka: { confirmText: "შენ აირჩიე ქართული.\nშემდგომ ვერ შეცვლი.", confirmBtn: "დადასტურება", changeBtn: "შეცვლა", eggTip: "🥚 დააჭირე კვერცხს!" }
};

// ============================================================
// Safe language labels (no Intl.DisplayNames dependency)
// ============================================================
const LANG_LABELS = {
  en: "English",
  ru: "Русский",
  hy: "Հայերեն",
  fr: "Français",
  es: "Español",
  de: "Deutsch",
  it: "Italiano",
  tr: "Türkçe",
  fa: "فارسی",
  ar: "العربية",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  hi: "हिन्दी",
  pt: "Português",
  el: "Ελληνικά",
  pl: "Polski",
  nl: "Nederlands",
  sv: "Svenska",
  ro: "Română",
  hu: "Magyar",
  cs: "Čeština",
  uk: "Українська",
  az: "Azərbaycanca",
  ka: "ქართული"
};


/* -------- APPLY TRANSLATIONS -------- */
function applyI18N(lang) {
  // 🧠 Fallback եթե սխալ է ընտրված լեզուն
  if (!langButtonsDict || !texts[lang]) lang = "en";

  // Լեզուն դնում ենք որպես <html lang="">
  document.documentElement.setAttribute("lang", lang);

  // Լեզվով վերնագրեր / կոճակներ
  const tRef = langButtonsDict.tasksTitles.referral;
  const tTasks = langButtonsDict.tasksTitles;

  // Tasks մոդալ
  const tasksTitle = document.querySelector("#tasksModal h2");
  if (tasksTitle) tasksTitle.textContent = tTasks.main[lang] || tTasks.main.en;
  const tasksClose = document.getElementById("closeTasksBtn");
  if (tasksClose) tasksClose.textContent = langButtonsDict.referral?.close?.[lang] || "✖ Close";

  // Referrals մոդալ
  const refTitle = document.getElementById("referralTitle");
  if (refTitle) refTitle.textContent = tRef.title[lang] || tRef.title.en;
  const refCalc = document.getElementById("refPreviewBtn");
  if (refCalc) refCalc.textContent = tRef.calc[lang] || tRef.calc.en;
  const refClaim = document.getElementById("refClaimBtn");
  if (refClaim) refClaim.textContent = tRef.claim[lang] || tRef.claim.en;
  const refClose = document.getElementById("closeRefBtn");
  if (refClose) refClose.textContent = tRef.close[lang] || tRef.close.en;

  // Toast-երի լեզու նույնպես դնում ենք
  VORN.lang = lang;
  localStorage.setItem("vorn_lang", lang);
  console.log(`🌍 Language applied globally: ${lang}`);
}


const langButtonsDict = {
  continue: { en: "Continue", ru: "Продолжить", hy: "Շարունակել", tr: "Devam et", fa: "ادامه", es: "Continuar", fr: "Continuer", de: "Weiter", it: "Continua", zh: "继续", ja: "続行", ko: "계속", ar: "متابعة" },
  start:    { en: "Start",    ru: "Начать",      hy: "Սկսել",      tr: "Başlat",  fa: "شروع", es: "Empezar",  fr: "Commencer", de: "Starten", it: "Avvia", zh: "开始", ja: "開始", ko: "시작", ar: "ابدأ" },
  tasksTitles: {
    main:  { en: "⭐ Main Tasks", ru: "⭐ Основные задания", hy: "⭐ Հիմնական առաջադրանքներ", tr: "⭐ Ana Görevler", fa: "⭐ ماموریت‌های اصلی", es: "⭐ Tareas principales", fr: "⭐ Tâches principales" },
    daily: { en: "🌅 Daily Tasks", ru: "🌅 Ежедневные задания", hy: "🌅 Օրվա առաջադրանքներ", tr: "🌅 Günlük Görevler", fa: "🌅 ماموریت‌های روزانه", es: "🌅 Tareas diarias", fr: "🌅 Tâches quotidiennes" },
      referral: {
    title: {
      en: "🤝 Referrals", ru: "🤝 Рефералы", hy: "🤝 Ռեֆերալներ", 
      fr: "🤝 Parrainages", es: "🤝 Referencias", de: "🤝 Empfehlungen", it: "🤝 Inviti",
      tr: "🤝 Referanslar", fa: "🤝 دعوت‌ها", ar: "🤝 الإحالات", zh: "🤝 邀请", ja: "🤝 招待", ko: "🤝 추천",
      hi: "🤝 रेफरल्स", pt: "🤝 Indicações", el: "🤝 Παραπομπές", pl: "🤝 Polecenia", nl: "🤝 Verwijzingen",
      sv: "🤝 Hänvisningar", ro: "🤝 Recomandări", hu: "🤝 Meghívások", cs: "🤝 Pozvánky", uk: "🤝 Реферали",
      az: "🤝 Referallar", ka: "🤝 მოწვევები"
    },
    calc: {
      en: "🧮 Calculate", ru: "🧮 Посчитать", hy: "🧮 Հաշվել", 
      fr: "🧮 Calculer", es: "🧮 Calcular", de: "🧮 Berechnen", it: "🧮 Calcola",
      tr: "🧮 Hesapla", fa: "🧮 محاسبه", ar: "🧮 احسب", zh: "🧮 计算", ja: "🧮 計算", ko: "🧮 계산",
      hi: "🧮 गणना करें", pt: "🧮 Calcular", el: "🧮 Υπολογισμός", pl: "🧮 Oblicz", nl: "🧮 Berekenen",
      sv: "🧮 Beräkna", ro: "🧮 Calculează", hu: "🧮 Számítás", cs: "🧮 Spočítat", uk: "🧮 Порахувати",
      az: "🧮 Hesabla", ka: "🧮 გამოთვლა"
    },
    claim: {
      en: "💰 Claim", ru: "💰 Получить", hy: "💰 Վերցնել", 
      fr: "💰 Récupérer", es: "💰 Reclamar", de: "💰 Abholen", it: "💰 Richiedi",
      tr: "💰 Al", fa: "💰 دریافت", ar: "💰 استلام", zh: "💰 领取", ja: "💰 受け取る", ko: "💰 받기",
      hi: "💰 प्राप्त करें", pt: "💰 Receber", el: "💰 Λήψη", pl: "💰 Odbierz", nl: "💰 Ontvangen",
      sv: "💰 Hämta", ro: "💰 Primește", hu: "💰 Felvenni", cs: "💰 Získat", uk: "💰 Отримати",
      az: "💰 Al", ka: "💰 მიღება"
    },
    close: {
      en: "✖ Close", ru: "✖ Закрыть", hy: "✖ Փակել", 
      fr: "✖ Fermer", es: "✖ Cerrar", de: "✖ Schließen", it: "✖ Chiudi",
      tr: "✖ Kapat", fa: "✖ بستن", ar: "✖ إغلاق", zh: "✖ 关闭", ja: "✖ 閉じる", ko: "✖ 닫기",
      hi: "✖ बंद करें", pt: "✖ Fechar", el: "✖ Κλείσιμο", pl: "✖ Zamknij", nl: "✖ Sluiten",
      sv: "✖ Stäng", ro: "✖ Închide", hu: "✖ Bezárás", cs: "✖ Zavřít", uk: "✖ Закрити",
      az: "✖ Bağla", ka: "✖ დახურვა"
    }
  }

  }
 
};
function getSavedLang() {
  try { return localStorage.getItem("vorn_lang") || "en"; } catch { return "en"; }
}
function translated(key, lang) {
  const dict = langButtonsDict[key];
  return (dict && (dict[lang] || dict.en)) || key;
}

/* ------------ VORN STATE ------------ */
const VORN = {
  uid: 0,
  lang: "en",
  balance: 0,
  vornBalance: 0,
  lastMine: 0,
  timer: null,
  els: {
    feather: null, mineBtn: null, btnTasks: null, tasksModal: null, tasksList: null, closeTasksBtn: null,
    introVideo: null, introSlides: null, slideImage: null, slideNextBtn: null,
    startBtn: null, introText: null, startContainer: null, modalLang: null,
    confirmLangModal: null, confirmLangTitle: null, confirmLangText: null,
    confirmLangBtn: null, changeLangBtn: null, langGrid: null
  },
  energy: { max: 100, regenPerSec: 2, value: 100, hideTimer: null, regenTimer: null, mClicks: [] },
  tasks: { main: [], daily: [] },

  /* -------- INIT -------- */
  async init() {
    console.log("⚙️ VORN.init()");
    console.log("🧠 UID from URL:", uidFromURL());
    this.bindEls();
    this.buildLanguageGrid();
    this.uid = uidFromURL();
    this.lang = getSavedLang();

    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";


    // Start button (one-time open language)
    if (this.els.startBtn) {
      this.els.startBtn.addEventListener("click", () => {
        this.els.introText && (this.els.introText.style.display = "none");
        this.els.startContainer && (this.els.startContainer.style.display = "none");
        this.els.modalLang && this.els.modalLang.classList.remove("hidden");
      }, { once: true });
    }

    

    this.bindTasksModal();
    await this.ensureVideoPlays();

    // Fallback: hard-wire start if overlays delayed
    this.wireStartButton();

    if (this.uid) {
  // 🧠 Preload user & tasks asynchronously
  this.loadUser(); // no await — runs in background
  this.preloadTasks();
  this.startMineTicker();
}


  
 else {
      console.warn("⚠️ No uid in URL");
    }

    this.mountDebugOverlay();
    this.mountCanvasBackground();
    this.applyI18N && this.applyI18N();
  },


  buildLanguageGrid() {
  const grid = document.getElementById("lang-grid");
  if (!grid) {
    console.warn("⚠️ lang-grid not found");
    return;
  }

  grid.innerHTML = "";

  // Քո ամբողջ 25 լեզուների ցանկը՝ առանց կորուստի
  const LANGS = {
    en: "English",
    ru: "Русский",
    hy: "Հայերեն",
    fr: "Français",
    es: "Español",
    de: "Deutsch",
    it: "Italiano",
    tr: "Türkçe",
    fa: "فارسی",
    ar: "العربية",
    zh: "中文",
    ja: "日本語",
    ko: "한국어",
    hi: "हिन्दी",
    pt: "Português",
    el: "Ελληνικά",
    pl: "Polski",
    nl: "Nederlands",
    sv: "Svenska",
    ro: "Română",
    hu: "Magyar",
    cs: "Čeština",
    uk: "Українська",
    az: "Azərbaycanca",
    ka: "ქართული"
  };

  Object.entries(LANGS).forEach(([code, name]) => {
    const btn = document.createElement("button");
    btn.className = "lang-btn";
    btn.textContent = name;
    btn.onclick = () => this.showConfirmLang(code);
    grid.appendChild(btn);
  });

  console.log("✅ Language grid created:", Object.keys(LANGS).length, "languages");
},



  bindEls() {
    this.els.mineBtn = document.getElementById("btnMine");
    // ✅ Exchange button safe rebind
this.els.exchangeBtn = document.getElementById("btnExchange");
if (this.els.exchangeBtn) {
  this.els.exchangeBtn.onclick = null; // remove old listeners
  this.els.exchangeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    this.onExchange();
  });
}

    this.els.feather = document.getElementById("featherCount");
    this.els.btnTasks = document.getElementById("btnTasks");
    this.els.tasksModal = document.getElementById("tasksModal");
    this.els.tasksList = document.getElementById("tasksList");
    this.els.closeTasksBtn = document.getElementById("closeTasksBtn");
    this.els.introVideo = document.getElementById("introVideo");
    this.els.introSlides = document.getElementById("introSlides");
    this.els.slideImage = document.getElementById("slideImage");
    this.els.slideNextBtn = document.getElementById("slideNextBtn");
    this.els.startBtn = document.getElementById("startBtn");
    this.els.introText = document.querySelector(".intro-text");
    this.els.startContainer = document.getElementById("startContainer");
    this.els.modalLang = document.getElementById("languageModal");
    this.els.confirmLangModal = document.getElementById("confirmLangModal");
    this.els.confirmLangTitle = document.getElementById("confirmLangTitle");
    this.els.confirmLangText = document.getElementById("confirmLangText");
    this.els.confirmLangBtn = document.getElementById("confirmLangBtn");
    this.els.changeLangBtn = document.getElementById("changeLangBtn");
    this.els.langGrid = document.getElementById("lang-grid");

    // Mine button
    if (this.els.mineBtn) {
      this.els.mineBtn.addEventListener("click", () => this.onMineClick());
    }

    // 🔹 Referral elements
    this.els.btnReferral = document.getElementById("btnReferral");
    this.els.refModal = document.getElementById("referralsModal");
    this.els.refTop3 = document.getElementById("refTop3");
    this.els.refList = document.getElementById("refList");
    this.els.refResult = document.getElementById("refResult");
    this.els.refPreviewBtn = document.getElementById("refPreviewBtn");
    this.els.refClaimBtn = document.getElementById("refClaimBtn");
    this.els.closeRefBtn = document.getElementById("closeRefBtn");

    if (this.els.btnReferral && this.els.refModal) {
    this.els.btnReferral.addEventListener("click", async () => {
    this.openReferrals();
  });
  }
  if (this.els.closeRefBtn) {
  this.els.closeRefBtn.addEventListener("click", () => {
    this.els.refModal.classList.add("hidden");
  });
  }
  if (this.els.refPreviewBtn) {
  this.els.refPreviewBtn.addEventListener("click", () => this.refPreview());
  }
  if (this.els.refClaimBtn) {
  this.els.refClaimBtn.addEventListener("click", () => this.refClaim());
  }

},



  async openReferrals() {
    if (!this.uid) return;
    try {
      // inside openReferrals()
        const r = await fetch(`${API_BASE}/api/referrals?uid=${this.uid}`);  // ← was /api/referrals/${this.uid}
        const d = await r.json();

      if (!d.ok) throw new Error(d.error || "referrals failed");

      // Top-3 trophies
      const list = d.list || [];
      const top3 = list.slice(0, 3);
      const trophy = (rank) => rank === 1 ? "🥇" : rank === 2 ? "🥈" : "🥉";
      const color = (rank) => rank === 1 ? "gold" : rank === 2 ? "silver" : "#cd7f32";

      this.els.refTop3.innerHTML = top3.map(x => `
        <div class="ref-trophy" style="border-color:${color(x.rank)}">
          <div class="ref-trophy-medal">${trophy(x.rank)}</div>
          <div class="ref-trophy-name">${x.username}</div>
          <div class="ref-trophy-stats">🪶 ${x.feathers} &nbsp; 🜂 ${x.vorn.toFixed(2)}</div>
        </div>
      `).join("");

      // full list
      this.els.refList.innerHTML = list.map(x => `
        <div class="ref-row">
          <div class="ref-rank">${x.rank}</div>
          <div class="ref-user">${x.username}</div>
          <div class="ref-stats">🪶 ${x.feathers} &nbsp; 🜂 ${x.vorn.toFixed(2)}</div>
        </div>
      `).join("") || `<div class="muted">No invited users yet.</div>`;

      this.els.refResult.textContent = "";
      this.els.refClaimBtn.classList.add("hidden");
      this.els.refModal.classList.remove("hidden");
    } catch (e) {
      console.error("referrals open failed:", e);
      this.showMessage("error", "error");
    }

    // ✅ Թարգմանում ենք ռեֆերալի պատուհանը ըստ լեզվի
const lang = this.lang || getSavedLang();
const refDict = langButtonsDict.tasksTitles.referral;
document.getElementById("referralTitle").textContent = refDict.title[lang] || refDict.title.en;
document.getElementById("refPreviewBtn").textContent = refDict.calc[lang] || refDict.calc.en;
document.getElementById("refClaimBtn").textContent = refDict.claim[lang] || refDict.claim.en;
document.getElementById("closeRefBtn").textContent = refDict.close[lang] || refDict.close.en;


  },



 async refPreview() {
  try {
    const r = await fetch(`${API_BASE}/api/referrals/preview?uid=${this.uid}`); // ← new
    const d = await r.json();
    if (!d.ok) throw new Error(d.error || "preview failed");

    const cf = d.cashback_feathers || 0;
    const cv = d.cashback_vorn || 0;
    this.els.refResult.textContent =
      (this.lang === "ru") ? `💡 По расчёту: ${cf} 🪶 и ${cv.toFixed(4)} 🜂`
      : (this.lang === "hy") ? `💡 Ըստ հաշվարկի՝ ${cf} 🪶 և ${cv.toFixed(4)} 🜂`
      : `💡 You can claim ${cf} 🪶 and ${cv.toFixed(4)} 🜂`;
    if (cf > 0 || cv > 0) this.els.refClaimBtn.classList.remove("hidden");
    else this.els.refClaimBtn.classList.add("hidden");
  } catch (e) {
    console.error("ref preview failed:", e);
    this.els.refResult.textContent =
      (this.lang === "ru") ? "⚠️ Нет суммы для расчёта."
      : (this.lang === "hy") ? "⚠️ Չկա որևէ գումար հաշվարկելու։"
      : "⚠️ Nothing to calculate.";
    this.els.refClaimBtn.classList.add("hidden");
  }
},



async refClaim() {
  try {
    const r = await fetch(`${API_BASE}/api/referrals/claim`, { // ← was /api/referral_claim
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ uid: this.uid })                   // ← key is uid
    });
    const d = await r.json();
    if (!d.ok) { this.showMessage("error","error"); return; }

    this.balance = d.new_balance ?? this.balance;
    this.vornBalance = d.new_vorn ?? this.vornBalance;
    document.getElementById("featherCount")?.textContent = String(this.balance);
    document.getElementById("foodCount")?.textContent = (this.vornBalance).toFixed(2);

    const msg =
      (this.lang === "ru") ? `✅ Получено ${d.cashback_feathers} 🪶 и ${Number(d.cashback_vorn).toFixed(4)} 🜂`
      : (this.lang === "hy") ? `✅ Վերցրեցիր ${d.cashback_feathers} 🪶 և ${Number(d.cashback_vorn).toFixed(4)} 🜂`
      : `✅ Claimed ${d.cashback_feathers} 🪶 and ${Number(d.cashback_vorn).toFixed(4)} 🜂`;
    this.els.refResult.textContent = msg;

    this.els.refClaimBtn.classList.add("hidden");
    this.showMessage("success_exchange","success");
  } catch (e) {
    console.error("ref claim failed:", e);
    this.showMessage("error","error");
  }
},




  /* -------- USER / SERVER -------- */
  async loadUser() {
    try {
      console.log("🌐 Loading user:", API.user(this.uid));
      const r = await fetch(API.user(this.uid));
      const data = await r.json();
      console.log("✅ User data:", data);

      if (data && data.user_id) {
        this.balance = data.balance ?? 0;
        this.lastMine = data.last_mine ?? 0;
        this.vornBalance = data.vorn_balance ?? 0;
const vornEl = document.getElementById("foodCount");
if (vornEl) vornEl.textContent = (this.vornBalance).toFixed(2);
        this.vornBalance = data.vorn_balance ?? 0;
const foodEl = document.getElementById("foodCount");
if (foodEl) foodEl.textContent = this.vornBalance.toFixed(2);

        const serverLang = (data.language || "").toLowerCase();
        if (serverLang && texts[serverLang]) {
          this.lang = serverLang;
          localStorage.setItem("vorn_lang", this.lang);
        }

        this.els.feather && (this.els.feather.textContent = String(this.balance));
        setTimeout(() => this.paintMineButton(), 200);
      } else {
        console.warn("⚠️ Invalid user data:", data);
      }
    } catch (e) {
      console.error("🔥 loadUser failed:", e);
    }

    const nameEl = document.getElementById("username");
if (nameEl) nameEl.textContent = `Player ${this.uid}`;

// ✅ Դնում ենք նույն լեզուն նաև ինտերֆեյսի վրա
if (this.lang) document.documentElement.setAttribute("lang", this.lang);


// ✅ Պահպանում ենք լեզուն որպես active
document.documentElement.setAttribute("lang", this.lang);
console.log("🌐 Language set to:", this.lang);
// 🌍 Թարգմանությունները կիրառում ենք ամբողջ ինտերֆեյսին
applyI18N(this.lang);

},

  async preloadTasks() {
  try {
    const res = await fetch(`${API_BASE}/api/tasks?uid=${this.uid}`);
    this.tasks = await res.json();
    console.log("⚡ Prefetched tasks:", this.tasks);
  } catch (e) {
    console.warn("⚠️ Preload tasks failed", e);
  }
},


async onMineClick() {
  if (this._mineInProgress) return; // ⛔ prevent double click
  this._mineInProgress = true;

  if (this.secsUntilReady() > 0) {
    this.showMessage("wait_mine", "warning");
    this._mineInProgress = false;
    return;
  }

  this.els.mineBtn.disabled = true;
  try {
    console.log("🪶 Mine button clicked — sending /api/mine");
    const r = await fetch(API.mine, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.uid })
    });
    const data = await r.json();

    if (data.ok) {
      // ✅ Server confirmed reward
      this.balance = data.balance ?? this.balance;
      if (this.els.feather) this.els.feather.textContent = String(this.balance);
      this.lastMine = data.last_mine ?? Math.floor(Date.now() / 1000);
      this.flashMine();
      this.paintMineButton();
      this.showMessage("success_exchange", "success", 1200);
    } else if (data.cooldown) {
      this.showMessage("wait_mine", "warning");
    } else {
      this.showMessage("error", "error");
    }
  } catch (e) {
    console.error("🔥 /api/mine failed:", e);
    this.showMessage("error", "error");
  } finally {
    this._mineInProgress = false;
    this.els.mineBtn.disabled = false;
  }
},





  /* -------- MINE UI -------- */
  secsUntilReady() {
    if (!this.lastMine) return 0;
    const left = COOLDOWN_SEC - (nowSec() - this.lastMine);
    return Math.max(0, left);
  },
  pctReady() {
    const left = this.secsUntilReady();
    const done = COOLDOWN_SEC - left;
    return Math.max(0, Math.min(100, (done / COOLDOWN_SEC) * 100));
  },
  paintMineButton() {
    const btn = this.els.mineBtn;
    if (!btn) return;
    const left = this.secsUntilReady();
    const pct = this.pctReady();
    btn.style.setProperty("--pct", pct.toFixed(2));
    if (left <= 0) btn.classList.add("ready"); else btn.classList.remove("ready");
  },
  startMineTicker() {
    if (this.timer) clearInterval(this.timer);
    this.paintMineButton();
    this.timer = setInterval(() => this.paintMineButton(), 1000);
  },
  flashMine() {
    if (!this.els.mineBtn) return;
    this.els.mineBtn.classList.add("ready");
    setTimeout(()=> this.els.mineBtn.classList.remove("ready"), 350);
  },

  /* -------- INTRO / LANGUAGE FLOW -------- */
 /* buildLanguageGrid() {
  const grid = document.getElementById("lang-grid");
  if (!grid) {
    console.warn("⚠️ lang-grid not found");
    return;
  }

  grid.innerHTML = "";
  const LANGS = {
    en: "English",
    ru: "Русский",
    hy: "Հայերեն",
    fr: "Français",
    es: "Español",
    de: "Deutsch",
    it: "Italiano",
    tr: "Türkçe",
    fa: "فارسی",
    ar: "العربية",
    zh: "中文",
    ja: "日本語",
    ko: "한국어"
  };

  Object.entries(LANGS).forEach(([code, name]) => {
    const btn = document.createElement("button");
    btn.className = "lang-btn";
    btn.textContent = name;
    btn.onclick = () => this.showConfirmLang(code);
    grid.appendChild(btn);
  });

  console.log("✅ Language grid created:", Object.keys(LANGS).length, "languages");
}, */



  showConfirmLang(code) {
    const t = texts[code] || texts.en;
    if (!this.els.confirmLangModal) return;

    this.els.modalLang && this.els.modalLang.classList.add("hidden");

    this.els.confirmLangTitle && (this.els.confirmLangTitle.textContent = "✅");
    this.els.confirmLangText && (this.els.confirmLangText.textContent = t.confirmText);
    this.els.confirmLangBtn && (this.els.confirmLangBtn.textContent = t.confirmBtn);
    this.els.changeLangBtn && (this.els.changeLangBtn.textContent = t.changeBtn);
    // safety: փակել ուրիշ մոդալները, եթե բաց են
    document.getElementById("tasksModal")?.classList.add("hidden");
    document.getElementById("referralsModal")?.classList.add("hidden");
    this.els.confirmLangModal.classList.remove("hidden");

    if (this._confirmHandlersBound) return;
    this._confirmHandlersBound = true;

    this.els.confirmLangBtn && this.els.confirmLangBtn.addEventListener("click", async () => {
  this.els.confirmLangModal.classList.add("hidden");
  this.lang = code;
  localStorage.setItem("vorn_lang", this.lang);

  // ✅ ուղարկում ենք լեզուն սերվերին, որ միշտ հիշի
  if (this.uid) {
    try {
      await fetch(`${API_BASE}/api/set_language`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ user_id: this.uid, language: this.lang })
      });
    } catch (e) { console.warn("set_language failed:", e); }
  }

  this.startSlidesFlow(this.lang);
});


    this.els.changeLangBtn && this.els.changeLangBtn.addEventListener("click", () => {
      this.els.confirmLangModal.classList.add("hidden");
      this.els.modalLang && this.els.modalLang.classList.remove("hidden");
    });

    const closeLangBtn = document.getElementById("closeLangBtn");
    closeLangBtn && closeLangBtn.addEventListener("click", () => {
      this.els.modalLang && this.els.modalLang.classList.add("hidden");
    }, { once: true });
  },

  startSlidesFlow(selectedLangCode) {
    console.log("🚀 startSlidesFlow:", selectedLangCode);
    const slides = [
      "/webapp/assets/slide1.png",
      "/webapp/assets/slide2.png",
      "/webapp/assets/slide3.png"
    ];

    const introSlides = this.els.introSlides;
    const slideImage  = this.els.slideImage;
    const slideNextBtn = this.els.slideNextBtn;
    if (!introSlides || !slideImage || !slideNextBtn) {
      console.error("❌ Slide DOM elements not found");
      return;
    }

    this.els.introVideo && this.els.introVideo.classList.add("hidden");
    document.querySelectorAll(".modal").forEach(m => m.classList.add("hidden"));

    introSlides.classList.remove("hidden");

    let slideIndex = 0;
    slideImage.src = slides[slideIndex];
    slideNextBtn.textContent = translated("continue", selectedLangCode);

    slideNextBtn.onclick = () => {
      slideIndex++;
      if (slideIndex < slides.length) {
        slideImage.classList.add("fade-out");
        setTimeout(() => {
          slideImage.src = slides[slideIndex];
          slideImage.classList.remove("fade-out");
          slideImage.classList.add("fade-in");
          if (slideIndex === slides.length - 1) {
            slideNextBtn.textContent = translated("start", selectedLangCode);
          }
        }, 300);
      } else {
        introSlides.classList.add("hidden");
        this.openMainInterface();
        applyI18N(selectedLangCode);
      }
    };
  },

  openMainInterface() {
    console.log("🎮 Opening main interface...");
    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
    window.scrollTo(0, 0);

      // 🩹 Hide Start button & intro elements when main UI opens
  const startBtn = document.getElementById("startBtn");
  const startContainer = document.getElementById("startContainer");
  const introText = document.querySelector(".intro-text");
  startBtn && (startBtn.style.display = "none");
  startContainer && (startContainer.style.display = "none");
  introText && (introText.style.display = "none");


    const introVideo = document.getElementById("introVideo");
    const introSlides = document.getElementById("introSlides");
    const modals = document.querySelectorAll(".modal");
    introVideo && introVideo.classList.add("hidden");
    introSlides && introSlides.classList.add("hidden");
    modals.forEach(m => m.classList.add("hidden"));

    const bg = document.getElementById("mainBgVideo");
    const bgSource = bg?.querySelector("source");
    if (bg && bgSource) {
      bg.load();
      bg.classList.remove("hidden");
      bg.play?.().catch(()=> console.log("⚠️ Autoplay blocked"));
    }

    const mainUI = document.getElementById("mainUI");
    if (mainUI) {
      mainUI.classList.remove("hidden");
      setTimeout(()=> mainUI.classList.add("visible"), 50);
    }

    this.initMiningDOM();
    // ✅ Rebind UI elements after DOM is visible
    this.bindEls();

  },

  async ensureVideoPlays() {
    const introVideo = this.els.introVideo;
    if (!introVideo) return;
    // never intercept clicks
    introVideo.style.pointerEvents = "none";
    try { await introVideo.play(); }
    catch (err) {
      console.log("⚠️ Autoplay blocked. Hiding intro video.");
      introVideo.classList.add("hidden");
      const startBtn = this.els.startBtn;
      if (startBtn) {
        startBtn.classList.remove("hidden");
        startBtn.style.opacity = "1";
        startBtn.style.pointerEvents = "auto";
      }
    }
  },

  wireStartButton() {
  const bind = () => {
    const startBtn = document.getElementById("startBtn");
    const langModal = document.getElementById("languageModal");
    const introText = document.querySelector(".intro-text");
    const startCtr = document.getElementById("startContainer");

    if (startBtn && langModal) {
      startBtn.replaceWith(startBtn.cloneNode(true));
      const btn = document.getElementById("startBtn");
      btn.style.zIndex = "1000";
      btn.addEventListener("click", () => {
        introText && (introText.style.display = "none");
        startCtr && (startCtr.style.display = "none");

        // 🟢 Ահա սա է հիմնական տողը, որ բացում է լեզուների մենյուն
        langModal.classList.remove("hidden");
        console.log("✅ START → languageModal opened");
      });
      return true;
    }
    return false;
  };

  if (bind()) return;
  let tries = 0;
  const t = setInterval(() => {
    tries++;
    if (bind() || tries > 10) clearInterval(t);
  }, 200);
},


  /* -------- TASKS MODAL (Multilingual) -------- */
bindTasksModal() {
  const { btnTasks, tasksModal, tasksList, closeTasksBtn } = this.els;
  if (!btnTasks || !tasksModal || !tasksList || !closeTasksBtn) return;
  

  btnTasks.addEventListener("click", async () => {
  // Պատուհանը բացում ենք միայն կոճակից
  tasksModal.classList.remove("hidden");

  // Եթե արդեն ունենք նախաբեռնված՝ նկարում միայն render
  if (this.tasks && (this.tasks.main?.length || this.tasks.daily?.length)) return;

  try {
    const res = await fetch(`${API_BASE}/api/tasks?uid=${this.uid}`);
    this.tasks = await res.json();
  } catch (e) {
    console.warn("⚠️ Preload tasks failed", e);
  }
});



  // --- render only ---
  const renderTasks = (data) => {
    const lang = this.lang || getSavedLang();
    const titleMain  = langButtonsDict.tasksTitles.main[lang]  || langButtonsDict.tasksTitles.main.en;
    const titleDaily = langButtonsDict.tasksTitles.daily[lang] || langButtonsDict.tasksTitles.daily.en;

    tasksList.innerHTML = "";
    const addSection = (headerText, list) => {
  if (!list || !list.length) return;

  const h = document.createElement("h3");
  h.className = "task-section-title";
  h.textContent = headerText;
  tasksList.appendChild(h);

  list.forEach(t => {
    const div = document.createElement("div");
    div.className = "task-item";
    const title = t.link
      ? `<a href="${t.link}" target="_blank">${t.title}</a>`
      : t.title;
    const btn = t.completed
      ? `<button class="task-btn done" disabled>✅ Done</button>`
      : `<button class="task-perform-btn" data-task-id="${t.id}" data-link="${t.link || ""}">🚀 Perform</button>`;

    div.innerHTML = `
      <div class="task-left">
        <span>${title}</span>
        <span class="task-reward">
          +${t.reward_feather} 🪶 ${t.reward_vorn > 0 ? `+${t.reward_vorn} 🜂` : ""}
        </span>
      </div>
      ${btn}
    `;
    tasksList.appendChild(div);
  });
};


    addSection(titleMain, data.main);
    const divider = document.createElement("div");
    divider.className = "task-divider"; divider.innerHTML = "<hr>";
    tasksList.appendChild(divider);
    addSection(titleDaily, data.daily);
  };

  btnTasks.addEventListener("click", async () => {
    tasksModal.classList.remove("hidden");
    if (this.tasks && (this.tasks.main?.length || this.tasks.daily?.length)) {
      renderTasks(this.tasks);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/tasks?uid=${this.uid}`);
      const data = await res.json();
      this.tasks = data;
      renderTasks(data);
    } catch (err) {
      console.error("🔥 Failed to load tasks", err);
    }
  });

  // ✅ Perform flow (always attached)
  tasksList.addEventListener("click", async (ev) => {
    const btn = ev.target.closest(".task-perform-btn");
    if (!btn) return;

    const taskId = +btn.dataset.taskId;
    const link   = btn.dataset.link || "";
    btn.disabled = true;

    try {
      const r1 = await fetch(`${API_BASE}/api/task_attempt_create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: this.uid, task_id: taskId })
      });
      const d1 = await r1.json();
      if (!d1.ok) { btn.disabled = false; return alert("⚠️ Failed to start task"); }

      const token = d1.token;
      if (link) window.open(link, "_blank");

      setTimeout(async () => {
        const r2 = await fetch(`${API_BASE}/api/task_attempt_verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: this.uid, task_id: taskId, token })
        });
        const d2 = await r2.json();
        if (d2.ok) {
          this.balance = d2.new_balance;
          this.vornBalance = d2.new_vorn;
          document.getElementById("featherCount").textContent = d2.new_balance;
          document.getElementById("foodCount").textContent = d2.new_vorn.toFixed(2);
          btn.textContent = "✅ Claimed";
          btn.classList.add("done");
        } else {
          btn.textContent = "⚠️ Try again";
          btn.disabled = false;
        }
      }, 4000);
    } catch (e) {
      console.error("🔥 perform flow failed:", e);
      btn.disabled = false;
    }
  });

  closeTasksBtn.addEventListener("click", () => {
    this.els.tasksModal.classList.add("hidden");
  });
},



  /* -------- CLICK-MINING (energy HUD) -------- */
  initMiningDOM() {
    console.log("⚙️ initMiningDOM called");
    window._clickZone = document.getElementById('clickZone');
    window._featherEl = document.getElementById('featherCount');
    window._foodEl    = document.getElementById('foodCount');
    window._eBar      = document.getElementById('energyBar');
    window._eFill     = document.getElementById('energyFill');

    this.updateHUD();
    this.paintEnergy();

    if (window._clickZone) {
      console.log("✅ clickZone found, adding listener...");
      window._clickZone.addEventListener('click', () => this.onNestClick(), { passive: true });
    } else {
      console.warn('❌ clickZone not found at initMiningDOM');
    }

    if (this.energy.regenTimer) clearInterval(this.energy.regenTimer);
    this.energy.regenTimer = setInterval(() => this.regenEnergyTick(), 1000);
  },
  updateHUD() {
    if (window._featherEl) window._featherEl.textContent = String(this.balance);
    if (window._foodEl) window._foodEl.textContent = "0"; // placeholder
  },
  paintEnergy() {
    if (!window._eFill) return;
    const pct = Math.max(0, Math.min(100, (this.energy.value / this.energy.max) * 100));
    _eFill.style.width = pct + '%';
    let grad;
    if (pct >= 70) grad = 'linear-gradient(90deg, #00ff88, #00ccff)';
    else if (pct >= 35) grad = 'linear-gradient(90deg, #ffd54a, #ffae00)';
    else grad = 'linear-gradient(90deg, #ff6a6a, #ff2a2a)';
    _eFill.style.background = grad;
  },
  revealEnergyOnTripleClick() {
    const now = Date.now();
    this.energy.mClicks.push(now);
    this.energy.mClicks = this.energy.mClicks.filter(t => now - t <= 800);
    if (this.energy.mClicks.length >= 3) this.showEnergyBar();
  },
  showEnergyBar() {
    if (!window._eBar) return;
    _eBar.classList.remove('hidden');
    _eBar.classList.add('show');
    if (this.energy.hideTimer) clearTimeout(this.energy.hideTimer);
    this.energy.hideTimer = setTimeout(()=> this.hideEnergyBar(), 2500);
  },
  hideEnergyBar() {
    if (!window._eBar) return;
    _eBar.classList.remove('show');
  },
  bumpEnergyBarVisibility() {
    this.showEnergyBar();
    if (this.energy.hideTimer) clearTimeout(this.energy.hideTimer);
    this.energy.hideTimer = setTimeout(()=> this.hideEnergyBar(), 2500);
  },
  async onNestClick() {
    console.log("🪶 Crow clicked! Energy:", this.energy.value);
    if (this._lastClick && Date.now() - this._lastClick < 200) return;
this._lastClick = Date.now();

    this.revealEnergyOnTripleClick();
    if (this.energy.value <= 0) { this.bumpEnergyBarVisibility(); return; }

    this.energy.value -= 1;
    this.balance += 1;
    this.updateHUD();
    this.paintEnergy();
    this.bumpEnergyBarVisibility();

    try {
      if (!this.uid) return console.warn("⚠️ No UID found in URL");

// 🪶 lightweight crow-click mining — always adds +1 and saves to DB
const r = await fetch(API.mineClick, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ user_id: this.uid })
});
const data = await r.json();
if (data.ok) {
  // սերվերի balance-ը authoritative է
  this.balance = (typeof data.balance === "number") ? data.balance : this.balance;
  const fEl = document.getElementById("featherCount");
  if (fEl) fEl.textContent = String(this.balance);
}



    } catch (err) {
      console.error("🔥 Failed to call /api/mine:", err);
    }

    const pf = document.getElementById('progressFill');
if (pf) {
  let cur = parseFloat(pf.style.width || '0');
  cur += 0.2;

  if (cur >= 100) {
  pf.style.width = '0%';
  try {
    console.log("🜂 Sending /api/vorn_reward …");
    const r = await fetch(API.vornReward, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.uid, amount: 0.02 })
    });
    const data = await r.json();
    if (data.ok) {
      console.log(`✅ +${data.vorn_added} VORN, new total ${data.vorn_balance}`);
      const el = document.getElementById("foodCount");
      if (el) el.textContent = (Number(data.vorn_balance)).toFixed(2);
    } else {
      console.warn("⚠️ /api/vorn_reward responded with error:", data);
    }
  } catch (err) {
    console.error("🔥 Failed to add VORN reward:", err);
  }
} else {
  pf.style.width = cur + '%';
}

}

  },
  regenEnergyTick() {
    this.energy.value = Math.min(this.energy.max, this.energy.value + this.energy.regenPerSec);
    this.paintEnergy();
  },

  async onExchange() {
  if (!this.uid) return alert("⚠️ User not found!");
  try {
    const r = await fetch(`${API_BASE}/api/vorn_exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.uid })
    });
    const data = await r.json();
    if (data.ok) {
      // թարմացնենք local state-ը և UI-ն
      this.balance = data.new_balance;
      this.vornBalance = data.new_vorn ?? 0;

      const featherEl = document.getElementById("featherCount");
      const vornEl = document.getElementById("foodCount");
      if (featherEl) featherEl.textContent = String(this.balance);
      if (vornEl) vornEl.textContent = (this.vornBalance).toFixed(2);

      this.showMessage("success_exchange", "success");
    } else {
      this.showMessage("not_enough", "error");
    }
  } catch (e) {
    console.error("🔥 Exchange failed:", e);
    this.showMessage("error", "error");
  }
},

/* -------- BEAUTIFUL MULTILINGUAL TOAST -------- */
showMessage(key, type = "info", duration = 2600) {
  // Թարգմանությունների հավաքածու
  const messages = {
    not_enough: {
      en: "⚠️ Not enough feathers to exchange!",
      ru: "⚠️ Недостаточно перьев для обмена!",
      hy: "⚠️ Փետուրները բավարար չեն փոխանակման համար։"
    },
    success_exchange: {
      en: "✅ Exchanged 50000 🪶 → +1 🜂",
      ru: "✅ Обменено 50000 🪶 → +1 🜂",
      hy: "✅ Փոխանակվեց 50000 🪶 → +1 🜂"
    },
    wait_mine: {
      en: "⏳ Please wait before next mining.",
      ru: "⏳ Подожди перед следующим майнингом.",
      hy: "⏳ Սպասիր մինչև հաջորդ մայնինգը։"
    },
    error: {
      en: "🔥 Something went wrong!",
      ru: "🔥 Произошла ошибка!",
      hy: "🔥 Ինչ-որ բան սխալ է տեղի ունեցել։"
    }
  };

  // ընտրում ենք օգտատիրոջ լեզուն
  const lang = (this.lang && texts[this.lang]) ? this.lang : getSavedLang();
  const text = (messages[key] && (messages[key][lang] || messages[key].en)) || key;

  // հին toast-ը ջնջում ենք
  const old = document.querySelector(".vorn-toast");
  if (old) old.remove();

  // ստեղծում ենք նոր toast
  const toast = document.createElement("div");
  toast.className = `vorn-toast ${type}`;
  toast.innerHTML = text;
  document.body.appendChild(toast);

  // Fade-in
  setTimeout(() => toast.classList.add("visible"), 50);

  // Fade-out
  setTimeout(() => {
    toast.classList.remove("visible");
    setTimeout(() => toast.remove(), 600);
  }, duration);
},


  /* -------- CANVAS / PARALLAX -------- */
  mountCanvasBackground() {
    (function(){
      const cnv = document.getElementById('vornCanvas');
      if(!cnv) return;
      const ctx = cnv.getContext('2d');

      let DPR = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
      let W = 0, H = 0;

      let parX = 0, parY = 0, targetParX = 0, targetParY = 0;

      const STARS = [], DUST = [], FOG = [], RIPPLES = [];
      const FOCUS = { x: 0.5, y: 0.62 };

      function resize(){
        W = cnv.width  = Math.floor(window.innerWidth * DPR);
        H = cnv.height = Math.floor(window.innerHeight * DPR);
        cnv.style.width = window.innerWidth + 'px';
        cnv.style.height= window.innerHeight + 'px';
        initStars(); initFog(); initDust();
      }
      function rand(a,b){ return a + Math.random()*(b-a); }
      function initStars(){
        STARS.length = 0;
        const count = Math.floor((W*H) / (7000 * DPR));
        for(let i=0;i<count;i++){
          STARS.push({ x: Math.random()*W, y: Math.random()*H, r: rand(0.6, 1.8)*DPR, a: rand(0.4, 0.9), spx: rand(-0.03, 0.03)*DPR, spy: rand(0.02, 0.06)*DPR });
        }
      }
      function initFog(){
        FOG.length = 3;
        for(let i=0;i<3;i++){
          FOG[i] = { x: rand(0.2*W, 0.8*W), y: rand(0.4*H, 0.8*H), r: rand(220, 380)*DPR, a: rand(0.08, 0.16), dx: rand(-0.12,0.12)*DPR, dy: rand(-0.08,0.08)*DPR, hue: rand(270, 300) };
        }
      }
      function initDust(){
        DUST.length = 0;
        const count = Math.floor((W*H) / (45000 * DPR));
        for(let i=0;i<count;i++){
          const base = Math.random();
          DUST.push({ x: rand(0.35*W, 0.65*W), y: rand(0.45*H, 0.8*H), r: rand(1.2, 2.4)*DPR, a: rand(0.2, 0.5), vy: rand(-0.12, -0.04)*DPR, life: rand(3, 8)*1000, born: performance.now() - base*4000, hue: Math.random()<0.5 ? 48 : 280 });
        }
      }
      function ease(a,b,t){ return a + (b-a)*t; }

      window.addEventListener('mousemove', (e)=>{
        const nx = (e.clientX / window.innerWidth )*2 - 1;
        const ny = (e.clientY / window.innerHeight)*2 - 1;
        targetParX = nx * 0.6; targetParY = ny * 0.6;
        document.body.style.transform = `translate(${(nx*5).toFixed(2)}px, ${(ny*5).toFixed(2)}px)`;
      }, {passive:true});

      window.addEventListener('deviceorientation', (e)=>{
        const nx = Math.max(-1, Math.min(1, (e.gamma||0)/30));
        const ny = Math.max(-1, Math.min(1, (e.beta ||0)/30));
        targetParX = nx * 0.6; targetParY = ny * 0.6;
      }, {passive:true});

      const mineBtn = document.getElementById('btnMine');
      if(mineBtn){
        mineBtn.addEventListener('click', ()=>{
          const cx = FOCUS.x * W;
          const cy = FOCUS.y * H;
          RIPPLES.push({ x: cx, y: cy, r: 10*DPR, max: Math.hypot(W,H)*0.35, a: 0.35 });
        }, {passive:true});
      }

      function draw(){
        requestAnimationFrame(draw);
        parX = ease(parX, targetParX, 0.08);
        parY = ease(parY, targetParY, 0.08);

        ctx.clearRect(0,0,W,H);

        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        for(const s of STARS){
          s.x += s.spx + parX*0.2; s.y += s.spy + parY*0.1;
          if(s.x < -10) s.x = W+10; if(s.x > W+10) s.x = -10; if(s.y > H+10) s.y = -10;
          ctx.globalAlpha = s.a; ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI*2);
          ctx.fillStyle = 'rgba(255,255,255,1)'; ctx.fill();
        }
        ctx.restore();

        ctx.save();
        for(const f of FOG){
          f.x += f.dx + parX*0.5; f.y += f.dy + parY*0.3;
          if(f.x < -200) f.x = W+200; if(f.x > W+200) f.x = -200;
          if(f.y < -200) f.y = H+200; if(f.y > H+200) f.y = -200;
          const g = ctx.createRadialGradient(f.x, f.y, 0, f.x, f.y, f.r);
          const col = `hsla(${f.hue}, 70%, 60%, ${f.a})`;
          g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)');
          ctx.fillStyle = g; ctx.beginPath(); ctx.arc(f.x, f.y, f.r, 0, Math.PI*2); ctx.fill();
        }
        ctx.restore();

        const gx = 0.5 * W + parX*8*DPR;
        const gy = 0.62 * H + parY*6*DPR;
        const t = (performance.now()/1000);
        const baseR = Math.min(W,H) * 0.18;
        const pulse = (Math.sin(t*0.8)*0.08 + 0.12);
        const rGlow = baseR * (1.0 + pulse);

        ctx.save();
        let g1 = ctx.createRadialGradient(gx, gy, 0, gx, gy, rGlow);
        g1.addColorStop(0, 'rgba(168, 119, 255, 0.28)');
        g1.addColorStop(0.6, 'rgba(255, 215, 0, 0.10)');
        g1.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.globalCompositeOperation = 'lighter';
        ctx.fillStyle = g1; ctx.beginPath(); ctx.arc(gx, gy, rGlow, 0, Math.PI*2); ctx.fill();
        ctx.restore();

        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        for(const d of DUST){
          const age = performance.now() - d.born;
          if(age > d.life){
            d.x = gx + ((Math.random()*120)-60)*DPR;
            d.y = gy + (20 + Math.random()*60)*DPR;
            d.born = performance.now(); d.life = (3000 + Math.random()*5000);
          }else{
            d.y += d.vy + parY*0.03;
          }
          const alpha = d.a * (1.0 - age/d.life);
          ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, Math.PI*2);
          ctx.fillStyle = `hsla(${d.hue}, 80%, 60%, ${alpha})`; ctx.fill();
        }
        ctx.restore();

        for(let i=RIPPLES.length-1; i>=0; i--){
          const rp = RIPPLES[i];
          rp.r += 6*DPR; rp.a *= 0.97;
          ctx.beginPath(); ctx.arc(rp.x, rp.y, rp.r, 0, Math.PI*2);
          ctx.strokeStyle = `rgba(168,119,255,${rp.a})`;
          ctx.lineWidth = 2*DPR; ctx.stroke();
          if(rp.r > rp.max || rp.a < 0.02) RIPPLES.splice(i,1);
        }
      }
      window.addEventListener('resize', resize);
      resize(); requestAnimationFrame(draw);
    })();

    // dynamic light particles on click
    (function(){
      document.addEventListener('mousemove', (e)=>{
        const x = (e.clientX / window.innerWidth)*100;
        const y = (e.clientY / window.innerHeight)*100;
        document.body.style.setProperty('--lx', x + '%');
        document.body.style.setProperty('--ly', y + '%');
      }, {passive:true});

      const mineBtn = document.getElementById('btnMine');
      if(mineBtn){
        mineBtn.addEventListener('click', ()=>{
          const container = document.createElement('div');
          container.classList.add('mine-particles');
          document.body.appendChild(container);
          for(let i=0; i<12; i++){
            const p = document.createElement('div');
            p.classList.add('mine-spark');
            p.style.left = '50%'; p.style.bottom = '28%';
            p.style.setProperty('--dx', (Math.random()*2-1)*120 + 'px');
            p.style.setProperty('--dy', (-Math.random()*120-40) + 'px');
            p.style.setProperty('--dur', (2 + Math.random()*2)+'s');
            container.appendChild(p);
          }
          setTimeout(()=>container.remove(), 4000);
        });
      }
    })();
  },

  /* -------- DEBUG OVERLAY -------- */
  mountDebugOverlay() {
    if (!DEBUG_UI) return;
    (function(){
      const box = document.createElement('div');
      box.style.position = 'fixed';
      box.style.bottom = '10px';
      box.style.left = '10px';
      box.style.padding = '6px 10px';
      box.style.border = '1px solid rgba(255,255,255,0.2)';
      box.style.background = 'rgba(0,0,0,0.5)';
      box.style.color = '#0f0';
      box.style.fontFamily = 'monospace';
      box.style.fontSize = '12px';
      box.style.borderRadius = '6px';
      box.style.zIndex = '9999';
      document.body.appendChild(box);

      setInterval(()=>{
        const bal = VORN?.balance ?? 0;
        const left = VORN?.secsUntilReady?.() ?? 0;
        const pct = VORN?.pctReady?.() ?? 0;
        box.innerHTML = `🪶 ${bal} | cooldown: ${left}s | pct: ${pct.toFixed(1)}% | lang: ${VORN.lang}`;
      }, 1000);
    })();
  }
};

/* ------------ BOOTSTRAP ------------ */
document.addEventListener("DOMContentLoaded", () => {
  console.log("🌐 Connecting to API_BASE:", API_BASE);
  VORN.init();
  applyI18N(getSavedLang());
});




// Telegram WebApp scroll-lock helper
document.addEventListener("DOMContentLoaded", () => {
  window.scrollTo(0, 0);
  setTimeout(() => { window.scrollTo(0, 0); }, 800);
  console.log("🩹 Scroll-lock fix applied (Telegram)");
});

// 🧩 Referral link display and copy (uses backend API)
document.addEventListener("DOMContentLoaded", async () => {
  const refLinkText = document.getElementById("refLinkText");
  const copyBtn = document.getElementById("copyRefLinkBtn");
  if (!refLinkText || !copyBtn) return;

  const uid = uidFromURL();
  let link = "";
  try {
    const r = await fetch(`${API_BASE}/api/ref_link/${uid}`);
    const d = await r.json();
    if (d.ok && d.link) link = d.link;   // ← always "https://t.me/<bot>?start=ref_<uid>"
  } catch (e) { console.warn("ref link fetch failed:", e); }

  if (!link) {
    // fallback just in case
    const botUsername = "VORNCoinbot";
    link = `https://t.me/${botUsername}?start=ref_${uid}`;
  }
  refLinkText.textContent = link;

  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(link);
      copyBtn.textContent = "✅ Copied!";
      setTimeout(() => (copyBtn.textContent = "📋 Copy Link"), 1500);
    } catch {
      alert("⚠️ Copy failed, copy manually.");
    }
  });
});




