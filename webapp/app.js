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
const API_BASE = window.location.origin.includes("web.app")
  ? "https://vorn-bot-nggr.onrender.com"
  : window.location.origin;
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

let exchangeBusy = false; // ⚙️ արգելում է կրկնակի սեղմումը


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



// Wallet temporarily disabled message
const walletMessages = {
  en: "⚠️ This function is temporarily disabled.",
  ru: "⚠️ Эта функция временно недоступна.",
  hy: "⚠️ Այս ֆունկցիան ժամանակավորապես անջատված է։",
  fr: "⚠️ Cette fonction est temporairement désactivée.",
  es: "⚠️ Esta función está temporalmente deshabilitada.",
  de: "⚠️ Diese Funktion ist vorübergehend deaktiviert.",
  it: "⚠️ Questa funzione è temporaneamente disabilitata.",
  tr: "⚠️ Bu özellik geçici olarak devre dışı.",
  fa: "⚠️ این قابلیت موقتاً غیرفعال است.",
  ar: "⚠️ هذه الميزة معطلة مؤقتًا.",
  zh: "⚠️ 此功能暂时不可用。",
  ja: "⚠️ この機能は一時的に無効になっています。",
  ko: "⚠️ 이 기능은 일시적으로 비활성화되어 있습니다.",
  hi: "⚠️ यह सुविधा अस्थायी रूप से बंद है।",
  pt: "⚠️ Esta função está temporariamente desativada.",
  el: "⚠️ Αυτή η λειτουργία είναι προσωρινά απενεργοποιημένη.",
  pl: "⚠️ Ta funkcja jest tymczasowo wyłączona.",
  nl: "⚠️ Deze functie is tijdelijk uitgeschakeld.",
  sv: "⚠️ Den här funktionen är tillfälligt avstängd.",
  ro: "⚠️ Această funcție este dezactivată temporar.",
  hu: "⚠️ Ez a funkció átmenetileg le van tiltva.",
  cs: "⚠️ Tato funkce je dočasně vypnuta.",
  uk: "⚠️ Ця функція тимчасово вимкнена.",
  az: "⚠️ Bu funksiya müvəqqəti olaraq deaktiv edilib.",
  ka: "⚠️ ეს ფუნქცია დროებით გათიშულია."
};



// 🌐 25 լեզվով Info բովանդակություն (լրիվ տարբերակներ)
const infoData = {
  en: `
  <h3>🌌 Welcome</h3>
  <p>Welcome to <b>VORN</b> — a world where consistency, focus, and inner calm turn into real progress.</p>
  <h3>⚙️ Who We Are</h3>
  <p><b>VORN Dev Team</b> blends technology, psychology, and design to build a fair, inspiring click-mining experience.</p>
  <h3>🌱 Why Stay Active</h3>
  <p>Everything depends on you. Daily actions compound; the more consistent you are, the stronger your results.</p>
  <h3>⚔️ Rules</h3>
  <p>Be honest. No bots, scripts, multi-accounts, or exploits. Respect other players and the community.</p>
  <h3>🛡 Security & Control</h3>
  <p>We protect accounts and fight abuse. Suspicious activity is monitored and limited automatically.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Any cheating slows or blocks progress. Fair play is rewarded, always.</p>
  <h3>📜 Policies</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Privacy Policy</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Terms of Use</a></p>
  <h3>🌙 Support</h3>
  <p>Step by step you build your future. Support: <b>@VORNsupportbot</b></p>
  `,

  ru: `
  <h3>🌌 Добро пожаловать</h3>
  <p>Добро пожаловать в <b>VORN</b> — мир, где последовательность, фокус и спокойствие превращаются в прогресс.</p>
  <h3>⚙️ Кто мы</h3>
  <p><b>VORN Dev Team</b> сочетает технологии, психологию и дизайн, чтобы создать честный и вдохновляющий клик-майнинг.</p>
  <h3>🌱 Зачем быть активным</h3>
  <p>Все зависит от тебя. Ежедневные действия накапливаются; чем стабильнее ты, тем сильнее результат.</p>
  <h3>⚔️ Правила</h3>
  <p>Играй честно. Без ботов, скриптов, мультиаккаунтов и эксплойтов. Уважай других.</p>
  <h3>🛡 Безопасность и контроль</h3>
  <p>Мы защищаем аккаунты и боремся с нарушениями. Подозрительная активность ограничивается автоматически.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Любой обман замедляет или блокирует прогресс. Честная игра всегда вознаграждается.</p>
  <h3>📜 Политики</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Политика конфиденциальности</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Условия использования</a></p>
  <h3>🌙 Поддержка</h3>
  <p>Шаг за шагом ты строишь будущее. Support: <b>@VORNsupportbot</b></p>
  `,

  hy: `
  <h3>🌌 Բարի գալուստ</h3>
  <p>Բարի գալուստ <b>VORN</b>՝ մի աշխարհ, որտեղ հետևողականությունը, կենտրոնացումը և ներքին հանդարտությունը դառնում են առաջընթաց։</p>
  <h3>⚙️ Ով ենք մենք</h3>
  <p><b>VORN Dev Team</b> համադրում է տեխնոլոգիան, հոգեբանությունը և դիզայնը՝ ստեղծելով արդար ու ոգեշնչող click-mining փորձ։</p>
  <h3>🌱 Ինչու մնալ ակտիվ</h3>
  <p>Ամեն ինչ կախված է քեզանից։ Օրվա պարզ քայլերը կուտակվում են, հետևողականությունը բերում է ուժեղ արդյունք։</p>
  <h3>⚔️ Խաղի կանոնները</h3>
  <p>Խաղա ազնվորեն․ առանց բոտերի, սկրիպտերի, բազմահաշիվների ու խոցելիությունների օգտագորման։ Հարգիր մյուսներին։</p>
  <h3>🛡 Անվտանգություն և վերահսկողություն</h3>
  <p>Պաշտպանում ենք հաշիվները և պայքարում խախտումների դեմ․ կասկածելի ակտիվությունը սահմանափակվում է ավտոմատ։</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Խարդախությունը դանդաղեցնում կամ արգելափակում է առաջընթացը․ ազնիվ խաղը միշտ պարգևատրվում է։</p>
  <h3>📜 Քաղաքականություններ</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Privacy Policy</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Terms of Use</a></p>
  <h3>🌙 Սպասարկում</h3>
  <p>Քայլ առ քայլ կառուցում ես ապագադ։ Support՝ <b>@VORNsupportbot</b></p>
  `,

  fr: `
  <h3>🌌 Bienvenue</h3>
  <p>Bienvenue dans <b>VORN</b> — cohérence, focus et calme intérieur se transforment en progrès réel.</p>
  <h3>⚙️ Qui sommes-nous</h3>
  <p><b>VORN Dev Team</b> réunit technologie, psychologie et design pour une expérience honnête et motivante.</p>
  <h3>🌱 Pourquoi rester actif</h3>
  <p>Tout dépend de toi. Les actions quotidiennes s’additionnent et renforcent tes résultats.</p>
  <h3>⚔️ Règles</h3>
  <p>Joue honnêtement. Pas de bots, scripts, multi-comptes ni d’exploits. Respecte la communauté.</p>
  <h3>🛡 Sécurité & contrôle</h3>
  <p>Nous protégeons les comptes et détectons les abus. L’activité suspecte est limitée automatiquement.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>La triche ralentit ou bloque le progrès. Le jeu équitable est récompensé.</p>
  <h3>📜 Politiques</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Politique de confidentialité</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Conditions d’utilisation</a></p>
  <h3>🌙 Support</h3>
  <p>Pas à pas, tu construis ton futur. Support : <b>@VORNsupportbot</b></p>
  `,

  es: `
  <h3>🌌 Bienvenido</h3>
  <p>Bienvenido a <b>VORN</b>: constancia, enfoque y calma interior se convierten en progreso.</p>
  <h3>⚙️ Quiénes somos</h3>
  <p><b>VORN Dev Team</b> une tecnología, psicología y diseño para una experiencia justa e inspiradora.</p>
  <h3>🌱 Por qué ser activo</h3>
  <p>Todo depende de ti. Las acciones diarias se acumulan y potencian tus resultados.</p>
  <h3>⚔️ Reglas</h3>
  <p>Juega limpio: sin bots, scripts, multicuentas ni exploits. Respeta a los demás.</p>
  <h3>🛡 Seguridad y control</h3>
  <p>Protegemos cuentas y detectamos abusos. La actividad sospechosa se limita automáticamente.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Hacer trampa frena o bloquea tu progreso. El juego justo es recompensado.</p>
  <h3>📜 Políticas</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Política de privacidad</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Términos de uso</a></p>
  <h3>🌙 Soporte</h3>
  <p>Paso a paso construyes tu futuro. Soporte: <b>@VORNsupportbot</b></p>
  `,

  de: `
  <h3>🌌 Willkommen</h3>
  <p>Willkommen bei <b>VORN</b> — Beständigkeit, Fokus und innere Ruhe werden zu echtem Fortschritt.</p>
  <h3>⚙️ Wer wir sind</h3>
  <p><b>VORN Dev Team</b> vereint Technologie, Psychologie und Design für ein faires, motivierendes Erlebnis.</p>
  <h3>🌱 Warum aktiv bleiben</h3>
  <p>Alles liegt an dir. Tägliche Taten summieren sich und stärken dein Ergebnis.</p>
  <h3>⚔️ Regeln</h3>
  <p>Spiel fair. Keine Bots, Scripts, Multi-Accounts oder Exploits. Respektiere andere.</p>
  <h3>🛡 Sicherheit & Kontrolle</h3>
  <p>Wir schützen Accounts und bekämpfen Missbrauch. Verdächtiges wird automatisch begrenzt.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Cheaten bremst oder blockiert den Fortschritt. Faires Spiel wird belohnt.</p>
  <h3>📜 Richtlinien</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Datenschutz</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Nutzungsbedingungen</a></p>
  <h3>🌙 Support</h3>
  <p>Schritt für Schritt baust du deine Zukunft. Support: <b>@VORNsupportbot</b></p>
  `,

  it: `
  <h3>🌌 Benvenuto</h3>
  <p>Benvenuto in <b>VORN</b> — coerenza, focus e calma interiore diventano progresso reale.</p>
  <h3>⚙️ Chi siamo</h3>
  <p><b>VORN Dev Team</b> unisce tecnologia, psicologia e design per un’esperienza giusta e motivante.</p>
  <h3>🌱 Perché restare attivo</h3>
  <p>Tutto dipende da te. Le azioni quotidiane si sommano e rafforzano i risultati.</p>
  <h3>⚔️ Regole</h3>
  <p>Gioca onestamente: niente bot, script, multi-account o exploit. Rispetta gli altri.</p>
  <h3>🛡 Sicurezza & controllo</h3>
  <p>Tuteliamo gli account e rileviamo abusi. Le attività sospette vengono limitate automaticamente.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Barare rallenta o blocca i progressi. Il gioco leale è ricompensato.</p>
  <h3>📜 Policy</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Privacy Policy</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Termini d’uso</a></p>
  <h3>🌙 Supporto</h3>
  <p>Passo dopo passo costruisci il tuo futuro. Supporto: <b>@VORNsupportbot</b></p>
  `,

  tr: `
  <h3>🌌 Hoş geldin</h3>
  <p><b>VORN</b>’a hoş geldin — istikrar, odak ve iç huzur gerçek ilerlemeye dönüşür.</p>
  <h3>⚙️ Biz kimiz</h3>
  <p><b>VORN Dev Team</b> teknoloji, psikoloji ve tasarımı birleştirerek adil ve ilham verici bir deneyim sunar.</p>
  <h3>🌱 Neden aktif kalmalı</h3>
  <p>Her şey sana bağlı. Günlük eylemler birikir; istikrar sonuçları güçlendirir.</p>
  <h3>⚔️ Kurallar</h3>
  <p>Dürüst oyna. Bot, script, çoklu hesap ve açık istismarı yok. Topluma saygı göster.</p>
  <h3>🛡 Güvenlik & kontrol</h3>
  <p>Hesapları koruyor, kötüye kullanımı tespit ediyoruz. Şüpheli etkinlik otomatik sınırlandırılır.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Hile ilerlemeni yavaşlatır veya engeller. Adil oyun ödüllendirilir.</p>
  <h3>📜 Politikalar</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Gizlilik Politikası</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Kullanım Şartları</a></p>
  <h3>🌙 Destek</h3>
  <p>Adım adım geleceğini inşa ediyorsun. Destek: <b>@VORNsupportbot</b></p>
  `,

  fa: `
  <div dir="rtl">
  <h3>🌌 خوش آمدید</h3>
  <p>به <b>VORN</b> خوش آمدید — ثبات، تمرکز و آرامش درونی به پیشرفت واقعی تبدیل می‌شود.</p>
  <h3>⚙️ ما که هستیم</h3>
  <p><b>VORN Dev Team</b> فناوری، روان‌شناسی و طراحی را ترکیب می‌کند تا تجربه‌ای عادلانه و الهام‌بخش بسازد.</p>
  <h3>🌱 چرا فعال بمانیم</h3>
  <p>همه چیز به شما بستگی دارد. اقدامات روزانه جمع می‌شوند و نتیجه را قوی‌تر می‌کنند.</p>
  <h3>⚔️ قوانین</h3>
  <p>صادقانه بازی کنید. بدون بات، اسکریپت، چندحسابی یا سوءاستفاده. به دیگران احترام بگذارید.</p>
  <h3>🛡 امنیت و کنترل</h3>
  <p>ما از حساب‌ها حفاظت می‌کنیم و تقلب را شناسایی می‌کنیم. فعالیت مشکوک به‌طور خودکار محدود می‌شود.</p>
  <h3>🚫 ضد ماین / ضد تسک</h3>
  <p>تقلب پیشرفت را کند یا مسدود می‌کند. بازی منصفانه همیشه پاداش می‌گیرد.</p>
  <h3>📜 سیاست‌ها</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">حریم خصوصی</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">شرایط استفاده</a></p>
  <h3>🌙 پشتیبانی</h3>
  <p>گام به گام آینده‌ات را می‌سازی. پشتیبانی: <b>@VORNsupportbot</b></p>
  </div>
  `,

  ar: `
  <div dir="rtl">
  <h3>🌌 أهلاً بك</h3>
  <p>مرحبًا في <b>VORN</b> — الثبات والتركيز والهدوء الداخلي تتحول إلى تقدم حقيقي.</p>
  <h3>⚙️ من نحن</h3>
  <p><b>VORN Dev Team</b> تجمع بين التقنية وعلم النفس والتصميم لتجربة عادلة وملهمة.</p>
  <h3>🌱 لماذا تبقى نشطًا</h3>
  <p>كل شيء يعتمد عليك. الأفعال اليومية تتراكم وتقوي النتائج.</p>
  <h3>⚔️ القواعد</h3>
  <p>العب بنزاهة. لا للروبوتات أو السكربتات أو تعدد الحسابات أو الاستغلال. احترم الآخرين.</p>
  <h3>🛡 الأمان والتحكم</h3>
  <p>نحمي الحسابات ونرصد سوء الاستخدام. النشاط المريب يُقيّد تلقائيًا.</p>
  <h3>🚫 مضاد التعدين / المهام</h3>
  <p>الغش يبطئ أو يوقف تقدّمك. اللعب العادل مُكافأ دائمًا.</p>
  <h3>📜 السياسات</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">سياسة الخصوصية</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">شروط الاستخدام</a></p>
  <h3>🌙 الدعم</h3>
  <p>خطوة بخطوة تصنع مستقبلك. الدعم: <b>@VORNsupportbot</b></p>
  </div>
  `,

  zh: `
  <h3>🌌 欢迎</h3>
  <p>欢迎来到 <b>VORN</b> —— 坚持、专注与内在平静将化为真正的进步。</p>
  <h3>⚙️ 我们是谁</h3>
  <p><b>VORN Dev Team</b> 融合科技、心理与设计，打造公平且激励人的体验。</p>
  <h3>🌱 为什么保持活跃</h3>
  <p>一切取决于你。日常行动会累积并强化你的成果。</p>
  <h3>⚔️ 规则</h3>
  <p>公平游玩。禁止机器人、脚本、多账号与漏洞利用。尊重他人。</p>
  <h3>🛡 安全与控制</h3>
  <p>我们保护账号，自动检测并限制可疑行为。</p>
  <h3>🚫 反挖矿 / 反任务滥用</h3>
  <p>作弊会减缓甚至阻止进度。公平永远会被奖励。</p>
  <h3>📜 政策</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">隐私政策</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">使用条款</a></p>
  <h3>🌙 支持</h3>
  <p>一步一步建设你的未来。支持：<b>@VORNsupportbot</b></p>
  `,

  ja: `
  <h3>🌌 ようこそ</h3>
  <p><b>VORN</b>へようこそ。継続・集中・内なる静けさが本当の進歩に繋がります。</p>
  <h3>⚙️ 私たちについて</h3>
  <p><b>VORN Dev Team</b>は技術・心理・デザインを融合し、公正でモチベーションの上がる体験を提供します。</p>
  <h3>🌱 なぜアクティブに</h3>
  <p>すべてはあなた次第。日々の行動が積み重なり、結果を強くします。</p>
  <h3>⚔️ ルール</h3>
  <p>公正に。ボット・スクリプト・複数アカウント・不正利用は禁止。互いを尊重。</p>
  <h3>🛡 セキュリティと管理</h3>
  <p>アカウントを保護し、不正を自動検知・制限します。</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>不正は進捗を遅らせ、停止させることがあります。フェアプレイは常に報われます。</p>
  <h3>📜 ポリシー</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">プライバシーポリシー</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">利用規約</a></p>
  <h3>🌙 サポート</h3>
  <p>一歩ずつ未来を築こう。サポート：<b>@VORNsupportbot</b></p>
  `,

  ko: `
  <h3>🌌 환영합니다</h3>
  <p><b>VORN</b>에 오신 것을 환영합니다. 꾸준함·집중·내적 평온이 진짜 성과로 이어집니다.</p>
  <h3>⚙️ 소개</h3>
  <p><b>VORN Dev Team</b>은 기술·심리·디자인을 결합해 공정하고 동기부여가 되는 경험을 만듭니다.</p>
  <h3>🌱 왜 활동적으로</h3>
  <p>모든 것은 당신에게 달려 있습니다. 매일의 행동이 누적되어 결과를 강화합니다.</p>
  <h3>⚔️ 규칙</h3>
  <p>정직하게 플레이. 봇/스크립트/멀티계정/익스플로잇 금지. 다른 이용자 존중.</p>
  <h3>🛡 보안 & 통제</h3>
  <p>계정을 보호하고 부정행위를 자동 감지·제한합니다.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>치팅은 진행을 늦추거나 막습니다. 공정한 플레이는 보상됩니다.</p>
  <h3>📜 정책</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">개인정보 처리방침</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">이용약관</a></p>
  <h3>🌙 지원</h3>
  <p>한 걸음씩 미래를 쌓아가세요. 지원: <b>@VORNsupportbot</b></p>
  `,

  hi: `
  <h3>🌌 स्वागत है</h3>
  <p><b>VORN</b> में आपका स्वागत है — निरंतरता, फोकस और आंतरिक शांति असली प्रगति बनती है।</p>
  <h3>⚙️ हम कौन हैं</h3>
  <p><b>VORN Dev Team</b> तकनीक, मनोविज्ञान और डिज़ाइन को मिलाकर निष्पक्ष और प्रेरक अनुभव बनाती है।</p>
  <h3>🌱 सक्रिय क्यों रहें</h3>
  <p>सब कुछ आप पर निर्भर है। रोज़ के छोटे कदम जुड़कर परिणाम को मजबूत बनाते हैं.</p>
  <h3>⚔️ नियम</h3>
  <p>ईमानदारी से खेलें: बॉट, स्क्रिप्ट, मल्टी-अकाउंट या एक्सप्लॉइट नहीं। सभी का सम्मान करें।</p>
  <h3>🛡 सुरक्षा व नियंत्रण</h3>
  <p>हम अकाउंट सुरक्षित रखते हैं और दुरुपयोग का स्वतः पता लगाते हैं।</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>चीटिंग प्रगति को धीमा या रोक सकती है। निष्पक्ष खेल को हमेशा पुरस्कृत किया जाता है।</p>
  <h3>📜 नीतियाँ</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">गोपनीयता नीति</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">उपयोग की शर्तें</a></p>
  <h3>🌙 सपोर्ट</h3>
  <p>कदम-दर-कदम अपना भविष्य बनाइए। सपोर्ट: <b>@VORNsupportbot</b></p>
  `,

  pt: `
  <h3>🌌 Bem-vindo</h3>
  <p>Bem-vindo ao <b>VORN</b> — consistência, foco e calma interior viram progresso real.</p>
  <h3>⚙️ Quem somos</h3>
  <p><b>VORN Dev Team</b> une tecnologia, psicologia e design para uma experiência justa e motivadora.</p>
  <h3>🌱 Por que ser ativo</h3>
  <p>Tudo depende de você. Ações diárias se somam e fortalecem seus resultados.</p>
  <h3>⚔️ Regras</h3>
  <p>Jogue limpo. Sem bots, scripts, múltiplas contas ou exploits. Respeite a comunidade.</p>
  <h3>🛡 Segurança & controle</h3>
  <p>Protegemos contas e detectamos abusos. Atividade suspeita é limitada automaticamente.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Trapacear atrasa ou bloqueia seu progresso. O jogo justo é recompensado.</p>
  <h3>📜 Políticas</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Política de Privacidade</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Termos de Uso</a></p>
  <h3>🌙 Suporte</h3>
  <p>Passo a passo você constrói seu futuro. Suporte: <b>@VORNsupportbot</b></p>
  `,

  el: `
  <h3>🌌 Καλωσόρισες</h3>
  <p>Καλωσόρισες στο <b>VORN</b> — συνέπεια, εστίαση και εσωτερική ηρεμία γίνονται πρόοδος.</p>
  <h3>⚙️ Ποιοι είμαστε</h3>
  <p>Η <b>VORN Dev Team</b> συνδυάζει τεχνολογία, ψυχολογία και design για δίκαιη και εμπνευσμένη εμπειρία.</p>
  <h3>🌱 Γιατί να μείνεις ενεργός</h3>
  <p>Όλα εξαρτώνται από εσένα. Οι καθημερινές πράξεις συσσωρεύονται και δυναμώνουν το αποτέλεσμα.</p>
  <h3>⚔️ Κανόνες</h3>
  <p>Παίξε τίμια. Όχι bots, scripts, πολλαπλοί λογαριασμοί ή exploits. Σεβασμός στην κοινότητα.</p>
  <h3>🛡 Ασφάλεια & έλεγχος</h3>
  <p>Προστατεύουμε λογαριασμούς και εντοπίζουμε κατάχρηση. Ύποπτη δραστηριότητα περιορίζεται αυτόματα.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Η απάτη καθυστερεί ή μπλοκάρει την πρόοδο. Το fair play ανταμείβεται.</p>
  <h3>📜 Πολιτικές</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Πολιτική Απορρήτου</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Όροι Χρήσης</a></p>
  <h3>🌙 Υποστήριξη</h3>
  <p>Βήμα-βήμα χτίζεις το μέλλον σου. Support: <b>@VORNsupportbot</b></p>
  `,

  pl: `
  <h3>🌌 Witaj</h3>
  <p>Witaj w <b>VORN</b> — konsekwencja, fokus i spokój wewnętrzny zamieniają się w realny postęp.</p>
  <h3>⚙️ Kim jesteśmy</h3>
  <p><b>VORN Dev Team</b> łączy technologię, psychologię i design dla uczciwego, motywującego doświadczenia.</p>
  <h3>🌱 Dlaczego być aktywnym</h3>
  <p>Wszystko zależy od ciebie. Codzienne działania kumulują się i wzmacniają wynik.</p>
  <h3>⚔️ Zasady</h3>
  <p>Graj uczciwie. Bez botów, skryptów, multi-kont i exploitów. Szanuj innych.</p>
  <h3>🛡 Bezpieczeństwo i kontrola</h3>
  <p>Chronimy konta, wykrywamy nadużycia. Podejrzana aktywność jest automatycznie ograniczana.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Oszustwo spowalnia lub blokuje postęp. Uczciwa gra jest nagradzana.</p>
  <h3>📜 Zasady serwisu</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Polityka prywatności</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Regulamin</a></p>
  <h3>🌙 Wsparcie</h3>
  <p>Krok po kroku budujesz przyszłość. Wsparcie: <b>@VORNsupportbot</b></p>
  `,

  nl: `
  <h3>🌌 Welkom</h3>
  <p>Welkom bij <b>VORN</b> — consistentie, focus en innerlijke rust worden echte vooruitgang.</p>
  <h3>⚙️ Wie wij zijn</h3>
  <p><b>VORN Dev Team</b> combineert technologie, psychologie en design voor een eerlijke, motiverende ervaring.</p>
  <h3>🌱 Waarom actief blijven</h3>
  <p>Alles hangt van jou af. Dagelijkse acties stapelen op en versterken je resultaat.</p>
  <h3>⚔️ Regels</h3>
  <p>Speel eerlijk. Geen bots, scripts, meerdere accounts of exploits. Respecteer anderen.</p>
  <h3>🛡 Veiligheid & controle</h3>
  <p>We beschermen accounts en detecteren misbruik. Verdachte activiteit wordt automatisch beperkt.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Vals spelen vertraagt of blokkeert vooruitgang. Eerlijk spel wordt beloond.</p>
  <h3>📜 Beleid</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Privacybeleid</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Gebruiksvoorwaarden</a></p>
  <h3>🌙 Support</h3>
  <p>Stap voor stap bouw je je toekomst. Support: <b>@VORNsupportbot</b></p>
  `,

  sv: `
  <h3>🌌 Välkommen</h3>
  <p>Välkommen till <b>VORN</b> — konsekvens, fokus och inre lugn blir verkliga framsteg.</p>
  <h3>⚙️ Vilka vi är</h3>
  <p><b>VORN Dev Team</b> förenar teknik, psykologi och design för en rättvis och motiverande upplevelse.</p>
  <h3>🌱 Varför vara aktiv</h3>
  <p>Allt hänger på dig. Dagliga handlingar byggs på och stärker resultatet.</p>
  <h3>⚔️ Regler</h3>
  <p>Spela rättvist. Inga bots, skript, flera konton eller exploits. Respektera andra.</p>
  <h3>🛡 Säkerhet & kontroll</h3>
  <p>Vi skyddar konton och upptäcker missbruk. Misstänkt aktivitet begränsas automatiskt.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Fusk bromsar eller stoppar din utveckling. Rättvist spel belönas.</p>
  <h3>📜 Policyer</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Integritetspolicy</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Användarvillkor</a></p>
  <h3>🌙 Support</h3>
  <p>Steg för steg bygger du din framtid. Support: <b>@VORNsupportbot</b></p>
  `,

  ro: `
  <h3>🌌 Bine ai venit</h3>
  <p>Bine ai venit în <b>VORN</b> — consecvența, concentrarea și calmul interior devin progres real.</p>
  <h3>⚙️ Cine suntem</h3>
  <p><b>VORN Dev Team</b> îmbină tehnologia, psihologia și designul pentru o experiență corectă și motivantă.</p>
  <h3>🌱 De ce să rămâi activ</h3>
  <p>Totul depinde de tine. Acțiunile zilnice se adună și îți întăresc rezultatele.</p>
  <h3>⚔️ Reguli</h3>
  <p>Joacă cinstit: fără boți, scripturi, conturi multiple sau exploatări. Respectă comunitatea.</p>
  <h3>🛡 Securitate & control</h3>
  <p>Protejăm conturile și detectăm abuzurile. Activitatea suspectă este limitată automat.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Trișatul îți încetinește sau blochează progresul. Jocul corect este recompensat.</p>
  <h3>📜 Politici</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Politica de confidențialitate</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Termeni de utilizare</a></p>
  <h3>🌙 Suport</h3>
  <p>Pas cu pas îți construiești viitorul. Suport: <b>@VORNsupportbot</b></p>
  `,

  hu: `
  <h3>🌌 Üdv</h3>
  <p>Üdv a <b>VORN</b> világában — a következetesség, fókusz és belső nyugalom valódi haladássá válnak.</p>
  <h3>⚙️ Kik vagyunk</h3>
  <p>A <b>VORN Dev Team</b> technológiát, pszichológiát és designt ötvöz egy tisztességes, motiváló élményért.</p>
  <h3>🌱 Miért maradj aktív</h3>
  <p>Minden rajtad múlik. A napi tettek összeadódnak, erősítve az eredményt.</p>
  <h3>⚔️ Szabályok</h3>
  <p>Játssz tisztán: nincs bot, script, több fiók vagy exploit. Tiszteld a többieket.</p>
  <h3>🛡 Biztonság & kontroll</h3>
  <p>Védjük a fiókokat és észleljük a visszaéléseket. A gyanús aktivitás automatikusan korlátozott.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Csalás lassítja vagy blokkolja a haladást. A fair játék jutalmazott.</p>
  <h3>📜 Irányelvek</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Adatvédelmi irányelv</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Felhasználási feltételek</a></p>
  <h3>🌙 Támogatás</h3>
  <p>Lépésről lépésre építed a jövőd. Support: <b>@VORNsupportbot</b></p>
  `,

  cs: `
  <h3>🌌 Vítej</h3>
  <p>Vítej ve <b>VORN</b> — konzistence, fokus a vnitřní klid se mění v reálný pokrok.</p>
  <h3>⚙️ Kdo jsme</h3>
  <p><b>VORN Dev Team</b> spojuje technologie, psychologii a design pro férový a motivující zážitek.</p>
  <h3>🌱 Proč být aktivní</h3>
  <p>Všechno záleží na tobě. Každodenní kroky se sčítají a posilují výsledky.</p>
  <h3>⚔️ Pravidla</h3>
  <p>Hraj férově. Žádní boti, skripty, multiúčty ani exploity. Respektuj ostatní.</p>
  <h3>🛡 Bezpečnost & kontrola</h3>
  <p>Chráníme účty a detekujeme zneužití. Podezřelá aktivita je automaticky omezena.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Podvádění zpomaluje nebo blokuje postup. Férová hra je odměňována.</p>
  <h3>📜 Zásady</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Zásady ochrany osobních údajů</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Podmínky použití</a></p>
  <h3>🌙 Podpora</h3>
  <p>Krok za krokem stavíš svou budoucnost. Support: <b>@VORNsupportbot</b></p>
  `,

  uk: `
  <h3>🌌 Ласкаво просимо</h3>
  <p>Вітаємо у <b>VORN</b> — послідовність, фокус та внутрішній спокій стають реальним прогресом.</p>
  <h3>⚙️ Хто ми</h3>
  <p><b>VORN Dev Team</b> поєднує технології, психологію та дизайн для чесного, мотивуючого досвіду.</p>
  <h3>🌱 Чому бути активним</h3>
  <p>Все залежить від тебе. Щоденні дії накопичуються та підсилюють результат.</p>
  <h3>⚔️ Правила</h3>
  <p>Грай чесно. Без ботів, скриптів, мультиакаунтів і експлойтів. Поважай інших.</p>
  <h3>🛡 Безпека та контроль</h3>
  <p>Ми захищаємо акаунти й виявляємо зловживання. Підозрілу активність обмежуємо автоматично.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Шахрайство сповільнює або блокує прогрес. Чесна гра винагороджується.</p>
  <h3>📜 Політики</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Політика конфіденційності</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">Умови використання</a></p>
  <h3>🌙 Підтримка</h3>
  <p>Крок за кроком ти будуєш майбутнє. Support: <b>@VORNsupportbot</b></p>
  `,

  az: `
  <h3>🌌 Xoş gəldin</h3>
  <p><b>VORN</b> dünyasına xoş gəldin — davamlılıq, fokus və daxili sakitlik real irəliləyişə çevrilir.</p>
  <h3>⚙️ Biz kimik</h3>
  <p><b>VORN Dev Team</b> texnologiya, psixologiya və dizaynı birləşdirir və ədalətli, motivasiyaedici təcrübə yaradır.</p>
  <h3>🌱 Niyə aktiv qalmalısan</h3>
  <p>Hər şey səndən asılıdır. Gündəlik addımlar toplanır və nəticəni gücləndirir.</p>
  <h3>⚔️ Qaydalar</h3>
  <p>Dürüst oyna: bot, skript, çox hesab və exploit yoxdur. İstifadəçilərə hörmət et.</p>
  <h3>🛡 Təhlükəsizlik və nəzarət</h3>
  <p>Hesabları qoruyuruq, sui-istifadəni aşkar edirik. Şübhəli fəaliyyət avtomatik məhdudlaşdırılır.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>Fırıldaqçı hərəkətlər irəliləyişi ləngidir və ya dayandırır. Dürüst oyun həmişə mükafatlandırılır.</p>
  <h3>📜 Siyasətlər</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">Məxfilik siyasəti</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">İstifadə şərtləri</a></p>
  <h3>🌙 Dəstək</h3>
  <p>Addım-addım gələcəyini qurursan. Dəstək: <b>@VORNsupportbot</b></p>
  `,

  ka: `
  <h3>🌌 კეთილი იყოს შენი მობრძანება</h3>
  <p>კეთილი იყოს შენი მობრძანება <b>VORN</b>-ში — თანმიმდევრულობა, ფოკუსი და შინაგანი სიმშვიდე რეალურ პროგრესად იქცევა.</p>
  <h3>⚙️ ვინ ვართ ჩვენ</h3>
  <p><b>VORN Dev Team</b> აერთიანებს ტექნოლოგიას, ფსიქოლოგიას და დიზაინს სამართლიანი და შთამაგონებელი გამოცდილებისთვის.</p>
  <h3>🌱 რატომ უნდა იყო აქტიური</h3>
  <p>ყველაფერი შენზეა დამოკიდებული. ყოველდღიური ქმედებები გროვდება და აძლიერებს შედეგს.</p>
  <h3>⚔️ წესები</h3>
  <p>ითამაშე სამართლიანად: არავითარი ბოტები, სკრიპტები, მრავალანგარიში ან ექსპლოიტი. პატივი ეცი სხვებს.</p>
  <h3>🛡 უსაფრთხოება და კონტროლი</h3>
  <p>ვიცავთ ანგარიშებს და ვამჩნევთ ბოროტად გამოყენებას. საეჭვო აქტივობა ავტომატურად იზღუდება.</p>
  <h3>🚫 Anti-Mine / Anti-Task</h3>
  <p>თაღლითობა აფერხებს ან აჩერებს პროგრესს. სამართლიანი თამაში ყოველთვის ფასდება.</p>
  <h3>📜 პოლიტიკა</h3>
  <p><a href="https://vorn-studio.github.io/vornbot.github.io/privacy.html" target="_blank">კონფიდენციალურობა</a><br>
     <a href="https://vorn-studio.github.io/vornbot.github.io/terms.html" target="_blank">გამოყენების პირობები</a></p>
  <h3>🌙 მხარდაჭერა</h3>
  <p>ნაბიჯ-ნაბიჯ შენ ქმნი მომავალს. მხარდაჭერა: <b>@VORNsupportbot</b></p>
  `
};

// 🔁 Օգնական՝ RTL լեզուներ
const RTL_LANGS = new Set(["ar","fa"]);


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
  console.log("🧱 Building language grid (on-demand)…");

  const LANGS = {
    en: "English", ru: "Русский", hy: "Հայերեն", fr: "Français", es: "Español",
    de: "Deutsch", it: "Italiano", tr: "Türkçe", fa: "فارسی", ar: "العربية",
    zh: "中文", ja: "日本語", ko: "한국어", hi: "हिन्दी", pt: "Português",
    el: "Ελληνικά", pl: "Polski", nl: "Nederlands", sv: "Svenska",
    ro: "Română", hu: "Magyar", cs: "Čeština", uk: "Українська",
    az: "Azərbaycanca", ka: "ქართული"
  };

  // այստեղ գտնում ենք grid-ը հենց այն պահին, երբ մենյուն բացվում է
  const grid = document.getElementById("lang-grid");
  if (!grid) {
    console.error("❌ lang-grid not found when building!");
    return;
  }

  grid.innerHTML = "";
  Object.entries(LANGS).forEach(([code, name]) => {
    const btn = document.createElement("button");
    btn.className = "lang-btn";
    btn.textContent = name;
    btn.onclick = () => VORN.showConfirmLang(code);
    grid.appendChild(btn);
  });

  console.log(`✅ Language grid filled with ${Object.keys(LANGS).length} buttons`);
},




  bindEls() {
    // 🜂 EXCHANGE button
this.els.exchangeBtn = document.getElementById("btnExchange");
this.els.mineBtn = document.getElementById("btnMine");
if (this.els.exchangeBtn) {
  this.els.exchangeBtn.onclick = null; // հանում ենք հին listener-ները
  this.els.exchangeBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    e.stopPropagation();

    console.log("🟢 EXCHANGE button clicked");

    try {
      const uid = this.uid || VORN.uid;
      if (!uid) {
        this.showMessage("⚠️ Cannot find user ID", "error");
        return;
      }

      // disable while processing
      this.els.exchangeBtn.disabled = true;
      this.els.exchangeBtn.textContent = "⏳";

      const resp = await fetch(`${API_BASE}/api/vorn_exchange`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: uid })
      });

      const data = await resp.json();
      console.log("EXCHANGE RESP:", data);

   if (data.ok) {
  this.balance = data.new_balance;
  this.vornBalance = data.new_vorn;

  document.getElementById("featherCount").textContent =
    Number(data.new_balance).toLocaleString("en-US");
  document.getElementById("foodCount").textContent =
    Number(data.new_vorn).toFixed(2);

  // ✅ օգտագործում ենք թարգմանվող բանալին
  this.showMessage("success_exchange", "success");
} else {
  // ✅ backend-ի կոդացված սխալի քարտեզավորում → թարգմանվող բանալու
  if (data.error === "not_enough_feathers") {
    this.showMessage("not_enough", "error");
  } else {
    this.showMessage("error", "error");
  }
}


      this.els.exchangeBtn.textContent = "🔁";
      this.els.exchangeBtn.disabled = false;
    } catch (err) {
      console.error("Exchange error:", err);
      this.showMessage("🔥 Server error", "error");
      this.els.exchangeBtn.textContent = "🔁";
      this.els.exchangeBtn.disabled = false;
    }
  

// 💰 Wallet (connect) button — temporarily disabled notice
this.els.btnWallet = document.getElementById("btnWallet");
if (this.els.btnWallet) {
  this.els.btnWallet.onclick = () => {
    const lang = this.lang || getSavedLang() || "en";
    const text = walletMessages[lang] || walletMessages.en;
    this.showMessage(text, "info", 2800);
  };
}



  });

// 💰 Wallet (connect) button
this.els.btnWallet = document.getElementById("btnWallet");
if (this.els.btnWallet) {
  this.els.btnWallet.onclick = () => {
    const lang = this.lang || getSavedLang() || "en";
    const text = walletMessages[lang] || walletMessages.en;
    this.showMessage(text, "info", 2800);
  };
}

// ℹ️ Info button — multilingual info modal
this.els.btnInfo = document.getElementById("btnInfo");
if (this.els.btnInfo) {
  this.els.btnInfo.onclick = () => {
    const lang = this.lang || getSavedLang() || "en";
    const infoModal = document.getElementById("infoModal");
    const infoText  = document.getElementById("infoText");
    const infoTitle = document.getElementById("infoTitle");
    const closeBtn  = document.getElementById("closeInfoBtn");

    if (!infoModal || !infoText) return;

    // Language titles
    const titles = { en:"ℹ️ Information", ru:"ℹ️ Информация", hy:"ℹ️ Տեղեկություն" };
    infoTitle.textContent = titles[lang] || titles.en;

    // RTL language support
    const RTL_LANGS = new Set(["ar","fa"]);
    if (RTL_LANGS.has(lang)) infoText.setAttribute("dir","rtl");
    else infoText.removeAttribute("dir");

    // Full 25-language data
    infoText.innerHTML = infoData[lang] || infoData.en;

    // Show modal
    infoModal.classList.remove("hidden");
    closeBtn.onclick = () => infoModal.classList.add("hidden");
  };
}


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
    this.els.refLevelWrap = document.getElementById("refLevelWrap");
    this.els.refLevelFill = document.getElementById("refLevelFill");
    this.els.refLevelLabel = document.getElementById("refLevelLabel");
    this.els.refLevelReward = document.getElementById("refLevelReward");
    this.els.refLevelTicks = document.getElementById("refLevelTicks");
    this.els.refLevelHint = document.getElementById("refLevelHint");


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

        // === Referral Level calculation ===
// 1) invite count
const invited = (d.invited_count != null) ? d.invited_count : ((d.list && d.list.length) ? d.list.length : 0);

// 2) level sizing rules (փոխես՝ եթե ունես կոնկրետ լիմիտներ)
const LEVEL_SIZE = 5;               // քանի հրավիրյալ է պետք հաջորդ level-ին անցնելու համար
const REWARD_PER_LEVEL = 5000;      // օրինակ՝ յուրաքանչյուր լվլի համար 5000 🪶

const level = Math.floor(invited / LEVEL_SIZE);
const inLevel = invited % LEVEL_SIZE;
const progress = Math.min(100, Math.round((inLevel / LEVEL_SIZE) * 100));
const needForNext = LEVEL_SIZE - inLevel;

// 3) UI fill
if (this.els.refLevelWrap) {
  // լցնենք progress-ը
  if (this.els.refLevelFill) this.els.refLevelFill.style.width = `${progress}%`;

  // վերնագիրը և reward-ը
  if (this.els.refLevelLabel) this.els.refLevelLabel.textContent = `Level ${level}`;
  if (this.els.refLevelReward) this.els.refLevelReward.textContent = `+${(level * REWARD_PER_LEVEL).toLocaleString()} 🪶`;

  // ticks (0..LEVEL_SIZE)
  if (this.els.refLevelTicks) {
    const ticks = [];
    for (let i = 0; i <= LEVEL_SIZE; i++) {
      ticks.push(`<span>${i}</span>`);
    }
    this.els.refLevelTicks.innerHTML = ticks.join("");
  }

  // Hint — քանի մարդ է պետք հաջորդ level-ին
  if (this.els.refLevelHint) {
    this.els.refLevelHint.textContent = needForNext === 0
      ? "✅ Maxed for this cycle — invite more to reach the next level!"
      : `Invite ${needForNext} more to reach Level ${level + 1}`;
  }
}


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
       // === REFERRAL LEVEL RENDER ===
      const invitedCount = Array.isArray(list) ? list.length : 0;
      renderRefLevel(invitedCount, this.lang || getSavedLang());
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
    this._exchangeBusy = false;
    const el = document.getElementById("featherCount");
if (el) el.textContent = String(this.balance);
    const food = document.getElementById("foodCount");
if (food) food.textContent = this.vornBalance.toFixed(2);


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
        this.lastMine    = Number(data.last_mine ?? 0);
this.vornBalance = Number(data.vorn_balance ?? 0);

const vornEl = document.getElementById("foodCount");
if (vornEl) vornEl.textContent = this.vornBalance.toFixed(2);

document.getElementById("featherCount").textContent = Number(data.balance ?? 0).toLocaleString("en-US");
document.getElementById("username").textContent     = String(data.username ?? "");

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
  if (this._mineInProgress) return;
  this._mineInProgress = true;

  // ⏳ client-side cooldown check
  if (this.secsUntilReady() > 0) {
    this.showMessage("wait_mine", "info", 1600);
    this._mineInProgress = false;
    return;
  }

  // disable кнопка, чтоб չկրկնվի
  this.els.mineBtn && (this.els.mineBtn.disabled = true);

  try {
    console.log("🪶 Mine button clicked — sending /api/mine");
    const r = await fetch(API.mine, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: this.uid })
    });
    const data = await r.json();

    if (data && data.ok) {
      // balance
      this.balance = Number(data.balance ?? this.balance ?? 0);
      const fEl = document.getElementById("featherCount");
      if (fEl) fEl.textContent = this.balance.toLocaleString("en-US");

      // cooldown՝ վերցնենք սերվերից, թե չէ՝ հիմա
      if (typeof data.last_mine === "number") {
        this.lastMine = Number(data.last_mine);
      } else {
        this.lastMine = nowSec();
      }

      // repaint mine progress immediately
      this.paintMineButton();
      this.flashMine();

      // success toast
      this.showMessage("mine_success", "success", 1400);
    } else {
      // եթե սերվերը վերադարձրել է cooldown/seconds_left — UI-ն ճիշտ նկարենք
      const left = Number(data?.seconds_left ?? 0);
      if (left > 0) {
        // վերականգնում ենք lastMine-ը այնպես, որ մնացած վայրկյանները երևան progress-ում
        this.lastMine = nowSec() - (COOLDOWN_SEC - left);
        this.paintMineButton();
        this.showMessage("wait_mine", "info", 1600);
      } else {
        this.showMessage("error", "error", 1600);
      }
    }
  } catch (e) {
    console.error("🔥 /api/mine failed:", e);
    this.showMessage("error", "error", 1600);
  } finally {
    this._mineInProgress = false;
    if (this.els.mineBtn) this.els.mineBtn.disabled = false;
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
  const btn = this.els.mineBtn || document.getElementById("btnMine");
  if (!btn) return;

  const left = this.secsUntilReady();
  const pct  = this.pctReady().toFixed(2) + "%";

  btn.style.setProperty("--pct", pct);
  btn.style.setProperty("--mine-pct", pct);

  // ✅ Գույնի վիճակ — եթե progress-ը լրացել է
  if (this.secsUntilReady() <= 0) {
    btn.classList.add("ready");
    btn.style.setProperty("--mine-pct", "100%");
  } else {
    btn.classList.remove("ready");
  }
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
  if (window._foodEl) window._foodEl.textContent = this.vornBalance.toFixed(2);
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

  async onExchangeClick() {
  console.log("🟢 Exchange button clicked");

  const uid = this.uid || UID; // քո user ID-ն
  if (!uid) {
    this.toast("User not loaded yet.");
    return;
  }

  // Գտնում ենք կոճակը
  const btn = document.getElementById("exchangeBtn");
  if (!btn) {
    console.warn("⚠️ Exchange button not found!");
    return;
  }

  // Կանխում ենք կրկնակի սեղմումները
  if (btn.disabled) return;
  btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/vorn_exchange`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: uid })
    });

    const data = await res.json();
    console.log("EXCHANGE RESP:", data);

    if (!data.ok) {
   console.log("⚠️ Exchange error:", data.error); // debug only
   if (data.error === "not_enough_feathers") {
       this.showMessage("not_enough", "error");
   } else {
       this.toast("❌ " + (data.error || "Exchange failed"));
   }
   return;
}



    // Թարմացնում ենք քո թվերը
    this.balance = Number(data.new_balance || 0);
    this.vornBalance = Number(data.new_vorn || 0);

    // Թարմացնում ենք DOM-ը (քո քանակները էկրանի վրա)
    const featherEl = document.getElementById("featherCount");
    const vornEl = document.getElementById("foodCount");
    if (featherEl) featherEl.textContent = this.balance.toLocaleString("en-US");
    if (vornEl) vornEl.textContent = this.vornBalance.toFixed(4);

    this.showMessage("success_exchange", "success");

  } catch (err) {
    console.error("Exchange failed:", err);
    this.toast("⚠️ Ошибка соединения.");
  } finally {
    // միշտ բացում ենք կոճակը նորից
    btn.disabled = false;
  }
},







/* -------- BEAUTIFUL MULTILINGUAL TOAST -------- */
showMessage(key, type = "info", duration = 2600) {
  // Թարգմանությունների հավաքածու
   const messages = {
    not_enough: {
      en: "⚠️ Not enough feathers to exchange!",
      ru: "⚠️ Недостаточно перьев для обмена!",
      hy: "⚠️ Փետուրները բավարար չեն փոխանակման համար։",
      fr: "⚠️ Pas assez de plumes pour échanger !",
      es: "⚠️ ¡No hay suficientes plumas para intercambiar!",
      de: "⚠️ Nicht genug Federn zum Tauschen!",
      it: "⚠️ Piume insufficienti per lo scambio!",
      tr: "⚠️ Takas için yeterli tüy yok!",
      fa: "⚠️ پر کافی برای مبادله وجود ندارد!",
      ar: "⚠️ لا توجد ريش كافية للتبادل!",
      zh: "⚠️ 羽毛不足以兑换！",
      ja: "⚠️ 交換する羽が足りません！",
      ko: "⚠️ 교환할 깃털이 부족합니다!",
      hi: "⚠️ एक्सचेंज करने के लिए पर्याप्त पंख नहीं हैं!",
      pt: "⚠️ Penas insuficientes para trocar!",
      el: "⚠️ Δεν υπάρχουν αρκετά φτερά για ανταλλαγή!",
      pl: "⚠️ Za mało piór do wymiany!",
      nl: "⚠️ Niet genoeg veren om te ruilen!",
      sv: "⚠️ Inte tillräckligt med fjädrar för att byta!",
      ro: "⚠️ Nu sunt suficiente pene pentru schimb!",
      hu: "⚠️ Nincs elég toll a cseréhez!",
      cs: "⚠️ Nedostatek per pro výměnu!",
      uk: "⚠️ Недостатньо пір'я для обміну!",
      az: "⚠️ Dəyişmək üçün kifayət qədər lələk yoxdur!",
      ka: "⚠️ საკმარისი ბუმბული არ არის გასაცვლელად!"
    },

    success_exchange: {
      en: "✅ Exchanged 50000 🪶 → +1 🜂",
      ru: "✅ Обменено 50000 🪶 → +1 🜂",
      hy: "✅ Փոխանակվեց 50000 🪶 → +1 🜂",
      fr: "✅ Échangées 50000 🪶 → +1 🜂",
      es: "✅ Intercambiadas 50000 🪶 → +1 🜂",
      de: "✅ Getauscht 50000 🪶 → +1 🜂",
      it: "✅ Scambiate 50000 🪶 → +1 🜂",
      tr: "✅ 50000 🪶 takas edildi → +1 🜂",
      fa: "✅ 50000 🪶 مبادله شد → +1 🜂",
      ar: "✅ تم تبادل 50000 🪶 → +1 🜂",
      zh: "✅ 兑换 50000 🪶 → +1 🜂",
      ja: "✅ 交換 50000 🪶 → +1 🜂",
      ko: "✅ 교환됨 50000 🪶 → +1 🜂",
      hi: "✅ एक्सचेंज 50000 🪶 → +1 🜂",
      pt: "✅ Trocadas 50000 🪶 → +1 🜂",
      el: "✅ Ανταλλάχθηκαν 50000 🪶 → +1 🜂",
      pl: "✅ Wymieniono 50000 🪶 → +1 🜂",
      nl: "✅ Gewisseld 50000 🪶 → +1 🜂",
      sv: "✅ Bytte 50000 🪶 → +1 🜂",
      ro: "✅ Schimbate 50000 🪶 → +1 🜂",
      hu: "✅ Kicserélve 50000 🪶 → +1 🜂",
      cs: "✅ Vyměněno 50000 🪶 → +1 🜂",
      uk: "✅ Обміняно 50000 🪶 → +1 🜂",
      az: "✅ 50000 🪶 dəyişdirildi → +1 🜂",
      ka: "✅ გადაცვლილია 50000 🪶 → +1 🜂"
    },

    mine_success: {
      en: "✅ Feathers claimed!",
      ru: "✅ Перья получены!",
      hy: "✅ Փետուրները վերցված են!",
      es: "✅ ¡Plumas recogidas!",
      fr: "✅ Plumes récupérées !",
      de: "✅ Federn eingesammelt!",
      it: "✅ Piume raccolte!",
      pt: "✅ Penas coletadas!",
      tr: "✅ Tüyler toplandı!",
      ar: "✅ تم جمع الريش!",
      fa: "✅ پرها دریافت شدند!",
      zh: "✅ 羽毛已领取！",
      ja: "✅ 羽が獲得されました！",
      ko: "✅ 깃털을 받았습니다!",
      hi: "✅ पंख एकत्रित किए गए!",
      id: "✅ Bulu telah diklaim!",
      ms: "✅ Bulu berjaya dikumpul!",
      th: "✅ ได้รับขนนกแล้ว!",
      vi: "✅ Lông vũ đã được nhận!",
      pl: "✅ Pióra zebrane!",
      uk: "✅ Пір’я отримано!",
      cs: "✅ Peří získáno!",
      ro: "✅ Pene colectate!",
      el: "✅ Τα φτερά συλλέχθηκαν!",
      hu: "✅ Tollak begyűjtve!",
      sr: "✅ Перје је преузето!"
    },


    wait_mine: {
      en: "⏳ Please wait before next mining.",
      ru: "⏳ Подожди перед следующим майнингом.",
      hy: "⏳ Սպասիր մինչև հաջորդ մայնինգը։",
      fr: "⏳ Veuillez attendre avant le prochain minage.",
      es: "⏳ Espera antes de la próxima minería.",
      de: "⏳ Bitte warte vor dem nächsten Mining.",
      it: "⏳ Attendi prima del prossimo mining.",
      tr: "⏳ Lütfen bir sonraki madencilik için bekleyin.",
      fa: "⏳ لطفاً قبل از استخراج بعدی صبر کنید.",
      ar: "⏳ يرجى الانتظار قبل التعدين التالي.",
      zh: "⏳ 请等待下一次挖矿。",
      ja: "⏳ 次のマイニングまでお待ちください。",
      ko: "⏳ 다음 채굴까지 잠시 기다려 주세요.",
      hi: "⏳ कृपया अगले माइनिंग से पहले प्रतीक्षा करें।",
      pt: "⏳ Aguarde antes da próxima mineração.",
      el: "⏳ Παρακαλώ περίμενε πριν το επόμενο mining.",
      pl: "⏳ Poczekaj przed następnym wydobyciem.",
      nl: "⏳ Wacht even voor de volgende mining.",
      sv: "⏳ Vänta före nästa gruvdrift.",
      ro: "⏳ Așteaptă înainte de următoarea minare.",
      hu: "⏳ Kérlek várj a következő bányászat előtt.",
      cs: "⏳ Počkej před dalším těžením.",
      uk: "⏳ Зачекай перед наступним майнінгом.",
      az: "⏳ Növbəti qazmadan əvvəl gözləyin.",
      ka: "⏳ მოიცადე შემდეგი მაინინგამდე."
    },

    error: {
      en: "🔥 Something went wrong!",
      ru: "🔥 Произошла ошибка!",
      hy: "🔥 Ինչ-որ բան սխալ է տեղի ունեցել։",
      fr: "🔥 Une erreur s'est produite !",
      es: "🔥 ¡Algo salió mal!",
      de: "🔥 Etwas ist schief gelaufen!",
      it: "🔥 Qualcosa è andato storto!",
      tr: "🔥 Bir şeyler ters gitti!",
      fa: "🔥 مشکلی پیش آمد!",
      ar: "🔥 حدث خطأ ما!",
      zh: "🔥 出了点问题！",
      ja: "🔥 何かがうまくいかなかった！",
      ko: "🔥 문제가 발생했습니다!",
      hi: "🔥 कुछ गलत हो गया!",
      pt: "🔥 Algo deu errado!",
      el: "🔥 Κάτι πήγε στραβά!",
      pl: "🔥 Coś poszło nie tak!",
      nl: "🔥 Er is iets misgegaan!",
      sv: "🔥 Något gick fel!",
      ro: "🔥 Ceva a mers greșit!",
      hu: "🔥 Valami elromlott!",
      cs: "🔥 Něco se pokazilo!",
      uk: "🔥 Щось пішло не так!",
      az: "🔥 Nəsə səhv oldu!",
      ka: "🔥 რაღაც არასწორად მოხდა!"
    },

    wallet_disabled: {
      en: "⚠️ This function is temporarily disabled.",
      ru: "⚠️ Эта функция временно недоступна.",
      hy: "⚠️ Այս ֆունկցիան ժամանակավորապես անջատված է։",
      fr: "⚠️ Cette fonction est temporairement désactivée.",
      es: "⚠️ Esta función está temporalmente deshabilitada.",
      de: "⚠️ Diese Funktion ist vorübergehend deaktiviert.",
      it: "⚠️ Questa funzione è temporaneamente disabilitata.",
      tr: "⚠️ Bu özellik geçici olarak devre dışı.",
      fa: "⚠️ این قابلیت موقتاً غیرفعال است.",
      ar: "⚠️ هذه الميزة معطلة مؤقتًا.",
      zh: "⚠️ 此功能暂时不可用。",
      ja: "⚠️ この機能は一時的に無効になっています。",
      ko: "⚠️ 이 기능은 일시적으로 비활성화되어 있습니다.",
      hi: "⚠️ यह सुविधा अस्थायी रूप से बंद है।",
      pt: "⚠️ Esta função está temporariamente desativada.",
      el: "⚠️ Αυτή η λειτουργία είναι προσωρινά απενεργοποιημένη.",
      pl: "⚠️ Ta funkcja jest tymczasowo wyłączона.",
      nl: "⚠️ Deze functie is tijdelijk uitgeschakeld.",
      sv: "⚠️ Den här funktionen är tillfälligt avstängd.",
      ro: "⚠️ Această funcție este dezactivată temporar.",
      hu: "⚠️ Ez a funkció átmenetileg le van tiltva.",
      cs: "⚠️ Tato funkce je dočasně vypnuta.",
      uk: "⚠️ Ця функція тимчасово вимкнена.",
      az: "⚠️ Bu funksiya müvəqqəti olaraq deaktiv edilib.",
      ka: "⚠️ ეს ფუნქცია დროებით გათიშულია."
    },
  
  };


  
 const lang = (this.lang && messages[key] && messages[key][this.lang]) ? this.lang : getSavedLang();
let text = key;

if (messages[key]) {
  if (messages[key][lang]) text = messages[key][lang];
  else if (messages[key]["en"]) text = messages[key]["en"];
}

// հին toast-ը ջնջում ենք
const old = document.querySelector(".vorn-toast");
if (old) old.remove();

// ստեղծում ենք նոր toast
const toast = document.createElement("div");
toast.className = "vorn-toast " + type;
toast.innerHTML = text;
document.body.appendChild(toast);

// Fade-in/out
setTimeout(function() {
  toast.classList.add("visible");
}, 50);

setTimeout(function() {
  toast.classList.remove("visible");
  setTimeout(function() { toast.remove(); }, 600);
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

// ✅ Safe delayed ready signal
window.addEventListener("load", () => {
  setTimeout(() => {
    if (window.VORN && typeof VORN.buildLanguageGrid === "function") {
      console.log("📣 VORN fully ready → emitting event");
      VORN.startMineTicker();
      document.dispatchEvent(new Event("vorn_ready"));
      window.dispatchEvent(new Event("vorn_ready"));
    } else {
      console.warn("⚠️ VORN not ready after load");
    }
  }, 1200); // փոքր ուշացում՝ որպեսզի Render-ում էլ լիովին բեռնվի
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

  
// === REFERRAL LEVEL LOGIC ===
const REF_LEVELS = [0, 5, 15, 30, 60, 100]; 

function computeRefLevel(invitedCount){
  let level = 0, next = REF_LEVELS[1] || 0;
  for (let i = 0; i < REF_LEVELS.length; i++){
    if (invitedCount >= REF_LEVELS[i]) {
      level = i;
      next = REF_LEVELS[i + 1] ?? REF_LEVELS[i];
    }
  }
  const curBase = REF_LEVELS[level] || 0;
  const need = Math.max(0, next - curBase);
  const have = Math.max(0, invitedCount - curBase);
  const pct = need > 0 ? Math.min(100, Math.round(have / need * 100)) : 100;
  return { level, pct, have, need, next };
}

function renderRefLevel(invitedCount, lang){
  const bar  = document.getElementById("refLevelBar");
  const lab  = document.getElementById("refLevelLabel");
  const stat = document.getElementById("refLevelStat");
  const nxt  = document.getElementById("refNextReward");
  if (!bar || !lab || !stat || !nxt) return;

  const { level, pct, have, need, next } = computeRefLevel(invitedCount);
  bar.style.width = pct + "%";
  stat.textContent = `${invitedCount} հրավիրված`;
  lab.textContent = `Մակարդակ ${level} • ${have}/${need > 0 ? need : have}`;
  nxt.textContent = next > REF_LEVELS[level]
    ? `Հաջորդ պարգևը՝ ${next} հրավիրվածի դեպքում`
    : `Առավելագույն մակարդակ`;
}
