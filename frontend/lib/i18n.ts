export type LocaleStatus='complete'|'beta'|'planned'|'legal_review_required';
export type LocaleDefinition={code:string;nativeName:string;englishName:string;status:LocaleStatus};

export const locales:LocaleDefinition[]=[
 {code:'en',nativeName:'English',englishName:'English',status:'complete'},
 {code:'es',nativeName:'Español',englishName:'Spanish',status:'beta'},
 {code:'de',nativeName:'Deutsch',englishName:'German',status:'planned'},
 {code:'pl',nativeName:'Polski',englishName:'Polish',status:'beta'},
 {code:'fr',nativeName:'Français',englishName:'French',status:'beta'},
 {code:'uk',nativeName:'Українська',englishName:'Ukrainian',status:'planned'},
 {code:'it',nativeName:'Italiano',englishName:'Italian',status:'planned'},
 {code:'pt-PT',nativeName:'Português (Portugal)',englishName:'Portuguese (Portugal)',status:'planned'},
 {code:'pt-BR',nativeName:'Português (Brasil)',englishName:'Portuguese (Brazil)',status:'planned'},
 {code:'bg',nativeName:'Български',englishName:'Bulgarian',status:'planned'},
 {code:'hr',nativeName:'Hrvatski',englishName:'Croatian',status:'planned'},
 {code:'cs',nativeName:'Čeština',englishName:'Czech',status:'planned'},
 {code:'da',nativeName:'Dansk',englishName:'Danish',status:'planned'},
 {code:'nl',nativeName:'Nederlands',englishName:'Dutch',status:'planned'},
 {code:'et',nativeName:'Eesti',englishName:'Estonian',status:'planned'},
 {code:'fi',nativeName:'Suomi',englishName:'Finnish',status:'planned'},
 {code:'el',nativeName:'Ελληνικά',englishName:'Greek',status:'planned'},
 {code:'hu',nativeName:'Magyar',englishName:'Hungarian',status:'planned'},
 {code:'ga',nativeName:'Gaeilge',englishName:'Irish',status:'planned'},
 {code:'lv',nativeName:'Latviešu',englishName:'Latvian',status:'planned'},
 {code:'lt',nativeName:'Lietuvių',englishName:'Lithuanian',status:'planned'},
 {code:'mt',nativeName:'Malti',englishName:'Maltese',status:'planned'},
 {code:'ro',nativeName:'Română',englishName:'Romanian',status:'planned'},
 {code:'sk',nativeName:'Slovenčina',englishName:'Slovak',status:'planned'},
 {code:'sl',nativeName:'Slovenščina',englishName:'Slovenian',status:'planned'},
 {code:'sv',nativeName:'Svenska',englishName:'Swedish',status:'planned'},
 {code:'sq',nativeName:'Shqip',englishName:'Albanian',status:'planned'},
 {code:'be',nativeName:'Беларуская',englishName:'Belarusian',status:'planned'},
 {code:'bs',nativeName:'Bosanski',englishName:'Bosnian',status:'planned'},
 {code:'ca',nativeName:'Català',englishName:'Catalan',status:'planned'},
 {code:'cy',nativeName:'Cymraeg',englishName:'Welsh',status:'planned'},
 {code:'eu',nativeName:'Euskara',englishName:'Basque',status:'planned'},
 {code:'gl',nativeName:'Galego',englishName:'Galician',status:'planned'},
 {code:'is',nativeName:'Íslenska',englishName:'Icelandic',status:'planned'},
 {code:'mk',nativeName:'Македонски',englishName:'Macedonian',status:'planned'},
 {code:'nb',nativeName:'Norsk bokmål',englishName:'Norwegian Bokmål',status:'planned'},
 {code:'nn',nativeName:'Norsk nynorsk',englishName:'Norwegian Nynorsk',status:'planned'},
 {code:'sr-Cyrl',nativeName:'Српски',englishName:'Serbian (Cyrillic)',status:'planned'},
 {code:'sr-Latn',nativeName:'Srpski',englishName:'Serbian (Latin)',status:'planned'},
 {code:'tr',nativeName:'Türkçe',englishName:'Turkish',status:'planned'},
 {code:'ka',nativeName:'ქართული',englishName:'Georgian',status:'planned'},
 {code:'hy',nativeName:'Հայերեն',englishName:'Armenian',status:'planned'},
 {code:'lb',nativeName:'Lëtzebuergesch',englishName:'Luxembourgish',status:'planned'},
 {code:'cnr',nativeName:'Crnogorski',englishName:'Montenegrin',status:'planned'},
];

const en={tagline:'Evidence-led short-form trend intelligence with responsible creative guidance.',product:'Product',overview:'Overview',dashboard:'Dashboard',pricing:'Pricing',company:'Company',about:'About',contact:'Contact',trust:'Trust',methodology:'Methodology',ai:'AI Disclosure',security:'Security',responsible:'Responsible Disclosure',accessibility:'Accessibility',legal:'Legal',terms:'Terms',privacy:'Privacy',cookies:'Cookies',acceptable:'Acceptable Use',copyright:'Copyright',billing:'Billing',follow:'Follow SignalScope',comingSoon:'Coming soon',independent:'Independent product — not affiliated with TikTok or ByteDance.',coverage:'Coverage reflects a configured monitored sample and is not exhaustive.',dataMode:'Data mode: Demo · simulated provider data',draft:'Draft policies effective',legalOverview:'Legal overview',noTracking:'No non-essential tracking detected; no consent control is shown.',language:'Language',available:'Available',beta:'Beta',planned:'Planned',betaNotice:'Beta language: shared navigation is translated; page content may fall back to English.',englishReference:'English remains the reference draft for legal content.'};
export type Messages=typeof en;

export const dictionaries:Record<string,Messages>={
 en,
 es:{tagline:'Inteligencia de tendencias de vídeo corto basada en evidencia y con orientación creativa responsable.',product:'Producto',overview:'Descripción',dashboard:'Panel',pricing:'Precios',company:'Empresa',about:'Acerca de',contact:'Contacto',trust:'Confianza',methodology:'Metodología',ai:'Divulgación IA',security:'Seguridad',responsible:'Divulgación responsable',accessibility:'Accesibilidad',legal:'Legal',terms:'Términos',privacy:'Privacidad',cookies:'Cookies',acceptable:'Uso aceptable',copyright:'Propiedad intelectual',billing:'Facturación',follow:'Sigue a SignalScope',comingSoon:'Próximamente',independent:'Producto independiente; no está afiliado con TikTok ni ByteDance.',coverage:'La cobertura corresponde a una muestra monitorizada configurada y no es exhaustiva.',dataMode:'Modo de datos: demostración · datos simulados',draft:'Políticas preliminares vigentes desde',legalOverview:'Centro legal',noTracking:'No se detectó seguimiento no esencial; no se muestra un control de consentimiento.',language:'Idioma',available:'Disponible',beta:'Beta',planned:'Planificado',betaNotice:'Idioma beta: la navegación compartida está traducida; el contenido puede aparecer en inglés.',englishReference:'El inglés sigue siendo el borrador de referencia para el contenido legal.'},
 de:{tagline:'Evidenzbasierte Kurzvideo-Trendinformationen mit verantwortungsvoller Kreativberatung.',product:'Produkt',overview:'Übersicht',dashboard:'Dashboard',pricing:'Preise',company:'Unternehmen',about:'Über uns',contact:'Kontakt',trust:'Vertrauen & Transparenz',methodology:'Datenquellen und Methodik',ai:'Hinweise zu KI und automatisierter Analyse',security:'Sicherheit',responsible:'Verantwortungsvolle Offenlegung',accessibility:'Erklärung zur Barrierefreiheit',legal:'Rechtliches',terms:'Allgemeine Geschäftsbedingungen',privacy:'Datenschutzerklärung',cookies:'Cookie- und Local-Storage-Richtlinie',acceptable:'Richtlinie zur zulässigen Nutzung',copyright:'Urheberrechts- und Takedown-Richtlinie',billing:'Preise, Abrechnung und Kündigung',follow:'SignalScope folgen',comingSoon:'Demnächst',independent:'Unabhängiges Produkt – keine Verbindung zu TikTok oder ByteDance.',coverage:'Die Abdeckung basiert auf einer konfigurierten überwachten Stichprobe und ist nicht vollständig.',dataMode:'Datenmodus: Demo · simulierte Anbieterdaten',draft:'Entwurfsrichtlinien gültig ab',legalOverview:'Rechtlicher Überblick',noTracking:'Kein nicht notwendiges Tracking erkannt; keine Einwilligungssteuerung angezeigt.',language:'Sprache',available:'Verfügbar',beta:'Beta',planned:'Geplant',betaNotice:'Beta-Sprache: Gemeinsame Navigation ist übersetzt; Seiteninhalte können auf Englisch zurückfallen.',englishReference:'Englisch bleibt der Referenzentwurf für rechtliche Inhalte.'},
 pl:{tagline:'Oparta na dowodach analiza trendów krótkich materiałów z odpowiedzialnymi wskazówkami kreatywnymi.',product:'Produkt',overview:'Przegląd',dashboard:'Panel',pricing:'Cennik',company:'Firma',about:'O nas',contact:'Kontakt',trust:'Zaufanie',methodology:'Metodologia',ai:'Informacje AI',security:'Bezpieczeństwo',responsible:'Odpowiedzialne zgłaszanie',accessibility:'Dostępność',legal:'Dokumenty prawne',terms:'Regulamin',privacy:'Prywatność',cookies:'Cookies',acceptable:'Dozwolone użycie',copyright:'Prawa autorskie',billing:'Rozliczenia',follow:'Obserwuj SignalScope',comingSoon:'Wkrótce',independent:'Niezależny produkt — niezwiązany z TikTok ani ByteDance.',coverage:'Zakres obejmuje skonfigurowaną monitorowaną próbę i nie jest wyczerpujący.',dataMode:'Tryb danych: demo · symulowane dane dostawcy',draft:'Projekty polityk obowiązujące od',legalOverview:'Centrum prawne',noTracking:'Nie wykryto zbędnego śledzenia; panel zgód nie jest wyświetlany.',language:'Język',available:'Dostępne',beta:'Beta',planned:'Planowane',betaNotice:'Język beta: wspólna nawigacja jest przetłumaczona; treść stron może pozostać po angielsku.',englishReference:'Angielska wersja pozostaje projektem referencyjnym dla treści prawnych.'},
 fr:{tagline:'Veille des tendances vidéo fondée sur les preuves, avec des conseils créatifs responsables.',product:'Produit',overview:'Aperçu',dashboard:'Tableau',pricing:'Tarifs',company:'Entreprise',about:'À propos',contact:'Contact',trust:'Confiance',methodology:'Méthodologie',ai:'Information IA',security:'Sécurité',responsible:'Divulgation responsable',accessibility:'Accessibilité',legal:'Juridique',terms:'Conditions',privacy:'Confidentialité',cookies:'Cookies',acceptable:'Usage acceptable',copyright:'Droits d’auteur',billing:'Facturation',follow:'Suivre SignalScope',comingSoon:'Bientôt disponible',independent:'Produit indépendant — non affilié à TikTok ou ByteDance.',coverage:'La couverture correspond à un échantillon surveillé configuré et n’est pas exhaustive.',dataMode:'Mode de données : démo · données simulées',draft:'Projets de politiques en vigueur le',legalOverview:'Centre juridique',noTracking:'Aucun suivi non essentiel détecté ; aucun contrôle de consentement affiché.',language:'Langue',available:'Disponible',beta:'Bêta',planned:'Prévu',betaNotice:'Langue bêta : la navigation partagée est traduite ; le contenu peut rester en anglais.',englishReference:'L’anglais reste le projet de référence pour le contenu juridique.'},
 uk:{tagline:'Аналітика трендів коротких відео на основі доказів із відповідальними творчими рекомендаціями.',product:'Продукт',overview:'Огляд',dashboard:'Панель',pricing:'Ціни',company:'Компанія',about:'Про нас',contact:'Контакти',trust:'Довіра та прозорість',methodology:'Джерела даних і методологія',ai:'Інформація про ШІ та автоматизований аналіз',security:'Безпека',responsible:'Відповідальне розкриття',accessibility:'Заява про доступність',legal:'Правова інформація',terms:'Умови використання',privacy:'Політика конфіденційності',cookies:'Політика cookies і локального сховища',acceptable:'Політика прийнятного використання',copyright:'Політика авторських прав і видалення',billing:'Ціни, оплата та скасування',follow:'Стежити за SignalScope',comingSoon:'Незабаром',independent:'Незалежний продукт — не пов’язаний із TikTok або ByteDance.',coverage:'Охоплення відображає налаштовану контрольовану вибірку й не є вичерпним.',dataMode:'Режим даних: демо · змодельовані дані',draft:'Проєкти політик чинні з',legalOverview:'Правовий центр',noTracking:'Необов’язкове відстеження не виявлено; елемент згоди не показується.',language:'Мова',available:'Доступно',beta:'Бета',planned:'Заплановано',betaNotice:'Бета-мова: спільну навігацію перекладено; вміст сторін може залишатися англійською.',englishReference:'Англійська версія залишається еталонним проєктом правових текстів.'},
 it:{tagline:'Analisi dei trend video basata su evidenze, con indicazioni creative responsabili.',product:'Prodotto',overview:'Panoramica',dashboard:'Dashboard',pricing:'Prezzi',company:'Azienda',about:'Chi siamo',contact:'Contatti',trust:'Fiducia e trasparenza',methodology:'Fonti dei dati e metodologia',ai:'Informativa su IA e analisi automatizzata',security:'Sicurezza',responsible:'Segnalazione responsabile',accessibility:'Dichiarazione di accessibilità',legal:'Note legali',terms:'Termini e condizioni',privacy:'Informativa sulla privacy',cookies:'Politica sui cookie e archiviazione locale',acceptable:'Politica di utilizzo accettabile',copyright:'Politica sul copyright e rimozione',billing:'Prezzi, fatturazione e cancellazione',follow:'Segui SignalScope',comingSoon:'Prossimamente',independent:'Prodotto indipendente — non affiliato a TikTok o ByteDance.',coverage:'La copertura riflette un campione monitorato configurato e non è esaustiva.',dataMode:'Modalità dati: demo · dati simulati',draft:'Bozze delle politiche valide dal',legalOverview:'Centro legale',noTracking:'Nessun tracciamento non essenziale rilevato; nessun controllo del consenso mostrato.',language:'Lingua',available:'Disponibile',beta:'Beta',planned:'Pianificato',betaNotice:'Lingua beta: la navigazione condivisa è tradotta; i contenuti possono restare in inglese.',englishReference:'L’inglese resta la bozza di riferimento per i contenuti legali.'},
 'pt-PT':{tagline:'Inteligência de tendências de vídeo baseada em evidências, com orientação criativa responsável.',product:'Produto',overview:'Visão geral',dashboard:'Painel',pricing:'Preços',company:'Empresa',about:'Sobre',contact:'Contacto',trust:'Confiança e transparência',methodology:'Fontes de dados e metodologia',ai:'Informação sobre IA e análise automatizada',security:'Segurança',responsible:'Divulgação responsável',accessibility:'Declaração de acessibilidade',legal:'Legal',terms:'Termos e condições',privacy:'Política de privacidade',cookies:'Política de cookies e armazenamento local',acceptable:'Política de utilização aceitável',copyright:'Política de direitos de autor e remoção',billing:'Preços, faturação e cancelamento',follow:'Siga a SignalScope',comingSoon:'Brevemente',independent:'Produto independente — não afiliado à TikTok ou ByteDance.',coverage:'A cobertura reflete uma amostra monitorizada configurada e não é exaustiva.',dataMode:'Modo de dados: demonstração · dados simulados',draft:'Projetos de políticas em vigor desde',legalOverview:'Centro legal',noTracking:'Não foi detetado rastreio não essencial; não é apresentado controlo de consentimento.',language:'Idioma',available:'Disponível',beta:'Beta',planned:'Planeado',betaNotice:'Idioma beta: a navegação partilhada está traduzida; o conteúdo pode permanecer em inglês.',englishReference:'O inglês continua a ser o projeto de referência para conteúdo jurídico.'},
};

export const selectableLocales=locales.filter(locale=>locale.status==='complete'||locale.status==='beta');
export const messagesFor=(locale:string)=>dictionaries[locale]||en;

const landingNav:Record<string,{problem:string;method:string;trust:string;pricing:string;demo:string}>={
 en:{problem:'The problem',method:'How it works',trust:'Why trust it',pricing:'Pricing',demo:'Explore demo dashboard'},
 es:{problem:'El problema',method:'Cómo funciona',trust:'Por qué confiar',pricing:'Precios',demo:'Explorar el panel de demostración'},
 de:{problem:'Das Problem',method:'So funktioniert es',trust:'Warum vertrauen',pricing:'Preise',demo:'Demo-Dashboard ansehen'},
 pl:{problem:'Problem',method:'Jak to działa',trust:'Dlaczego warto zaufać',pricing:'Cennik',demo:'Otwórz panel demonstracyjny'},
 fr:{problem:'Le problème',method:'Fonctionnement',trust:'Pourquoi nous faire confiance',pricing:'Tarifs',demo:'Explorer le tableau de bord démo'},
 uk:{problem:'Проблема',method:'Як це працює',trust:'Чому довіряти',pricing:'Ціни',demo:'Відкрити демонстраційну панель'},
 it:{problem:'Il problema',method:'Come funziona',trust:'Perché fidarsi',pricing:'Prezzi',demo:'Esplora la dashboard demo'},
 'pt-PT':{problem:'O problema',method:'Como funciona',trust:'Porquê confiar',pricing:'Preços',demo:'Explorar o painel de demonstração'},
};
export const landingNavFor=(locale:string)=>landingNav[locale]||landingNav.en;

const dashboardNav:Record<string,Record<string,string>>={
 en:{daily:'Daily',today:'Today',discover:'Discover',research:'Research',creators:'Creators',sounds:'Sounds · Add-on',hashtags:'Hashtags · Add-on',decide:'Decide',ideas:'Ideas',watchlists:'Watchlists',reports:'Reports',review:'Review',reviewQueue:'Review queue',dataHealth:'Data health',settings:'Settings',plans:'Plans & pricing',demo:'Demo workspace',source:'Check Data health for source status',site:'Product site'},
 pl:{daily:'Codziennie',today:'Dzisiaj',discover:'Odkrywaj',research:'Analiza',creators:'Twórcy',sounds:'Dźwięki · Dodatek',hashtags:'Hashtagi · Dodatek',decide:'Działania',ideas:'Pomysły',watchlists:'Listy obserwacji',reports:'Raporty',review:'Weryfikacja',reviewQueue:'Kolejka oceny',dataHealth:'Stan danych',settings:'Ustawienia',plans:'Plany i ceny',demo:'Przestrzeń demo',source:'Sprawdź stan źródła w sekcji Stan danych',site:'Strona produktu'},
 es:{daily:'Diario',today:'Hoy',discover:'Descubrir',research:'Análisis',creators:'Creadores',sounds:'Sonidos · Extra',hashtags:'Hashtags · Extra',decide:'Decidir',ideas:'Ideas',watchlists:'Listas',reports:'Informes',review:'Revisión',reviewQueue:'Cola de revisión',dataHealth:'Estado de datos',settings:'Configuración',plans:'Planes y precios',demo:'Espacio demo',source:'Consulta el estado de la fuente en Estado de datos',site:'Sitio del producto'},
 fr:{daily:'Quotidien',today:'Aujourd’hui',discover:'Découvrir',research:'Analyse',creators:'Créateurs',sounds:'Sons · Option',hashtags:'Hashtags · Option',decide:'Décider',ideas:'Idées',watchlists:'Listes de suivi',reports:'Rapports',review:'Vérification',reviewQueue:'File de vérification',dataHealth:'État des données',settings:'Paramètres',plans:'Offres et tarifs',demo:'Espace démo',source:'Consultez la source dans État des données',site:'Site produit'},
};
export const dashboardNavFor=(locale:string)=>dashboardNav[locale]||dashboardNav.en;

const globalBar:Record<string,Record<string,string>>={
 en:{workspace:'Workspace',search:'Search',market:'market demo',markets:'market demo',language:'language demo',languages:'language demo',history:'day entitlement',snapshot:'Simulated snapshot',custom:'Custom'},
 pl:{workspace:'Przestrzeń',search:'Szukaj',market:'rynek demo',markets:'rynki demo',language:'język demo',languages:'języki demo',history:'dni historii',snapshot:'Symulowana migawka',custom:'Niestandardowe'},
 es:{workspace:'Espacio',search:'Buscar',market:'mercado demo',markets:'mercados demo',language:'idioma demo',languages:'idiomas demo',history:'días de historial',snapshot:'Instantánea simulada',custom:'Personalizado'},
 fr:{workspace:'Espace',search:'Rechercher',market:'marché démo',markets:'marchés démo',language:'langue démo',languages:'langues démo',history:'jours d’historique',snapshot:'Instantané simulé',custom:'Personnalisé'},
};
export const globalBarFor=(locale:string)=>globalBar[locale]||globalBar.en;
