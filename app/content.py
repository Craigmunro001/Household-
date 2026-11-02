"""All client-facing wording (English / Afrikaans / isiZulu) and answer options.

DRAFT: legal wording must be signed off by David Schoonraad, and the Afrikaans and
isiZulu text should be read by a native speaker before going live.
"""

LANGS = ("en", "af", "zu")
LANG_NAMES = {"en": "English", "af": "Afrikaans", "zu": "isiZulu"}

TERMS = (25, 30, 36)  # plan lengths in months; nothing shorter or longer


def money(x):
    return f"R{x:,.2f}"


def term_label(n, lang):
    return {"en": f"{n} months", "af": f"{n} maande", "zu": f"izinyanga ezingu-{n}"}[lang]


# ---------------------------------------------------------------- answer options
# value, {lang: label}, keywords (all languages, matched on whole words / phrases)
OPTIONS = {
    "lang": [
        ("en", {"en": "English", "af": "English", "zu": "English"}, ["english", "eng", "engels"]),
        ("af", {"en": "Afrikaans", "af": "Afrikaans", "zu": "Afrikaans"}, ["afrikaans", "afr"]),
        ("zu", {"en": "isiZulu", "af": "isiZulu", "zu": "isiZulu"}, ["zulu", "isizulu", "isi zulu"]),
    ],
    "review": [
        ("yes", {"en": "Yes", "af": "Ja", "zu": "Yebo"}, ["yes", "ja", "yebo", "i am", "ek is"]),
        ("no", {"en": "No", "af": "Nee", "zu": "Cha"}, ["no", "not", "nee", "cha", "nope"]),
        ("unsure", {"en": "Not sure", "af": "Nie seker nie", "zu": "Angiqiniseki"},
         ["not sure", "unsure", "dont know", "don't know", "nie seker", "weet nie", "angiqiniseki", "angazi"]),
    ],
    "marital": [
        ("not_married", {"en": "No (single, divorced or widowed)", "af": "Nee (ongetroud, geskei of weduwee/wewenaar)",
                         "zu": "Cha (angishadile, ngehlukanisiwe noma ngiyisikhumba/umfelokazi)"},
         ["not married", "single", "unmarried", "divorced", "widowed", "widow", "widower", "nie getroud", "ongetroud",
          "enkel", "geskei", "angishadile", "angishadanga", "ngingashadile"]),
        ("in_community", {"en": "Married in community of property", "af": "Getroud binne gemeenskap van goedere",
                          "zu": "Ngishadile, ngokuhlanganyela kwempahla (in community of property)"},
         ["in community", "binne gemeenskap", "ngokuhlanganyela"]),
        ("out_of_community", {"en": "Married out of community of property", "af": "Getroud buite gemeenskap van goedere",
                              "zu": "Ngishadile, ngaphandle kokuhlanganyela kwempahla (out of community of property)"},
         ["out of community", "buite gemeenskap", "ngaphandle", "anc", "antenuptial", "ante nuptial"]),
        ("unsure", {"en": "Married, not sure which", "af": "Getroud, nie seker watter een nie",
                    "zu": "Ngishadile, angiqiniseki ukuthi yimuphi"},
         ["not sure", "unsure", "dont know", "don't know", "nie seker", "weet nie", "angiqiniseki", "angazi"]),
    ],
    "province": [
        ("EC", {"en": "Eastern Cape", "af": "Oos-Kaap", "zu": "Eastern Cape"}, ["eastern cape", "oos kaap", "east london", "gqeberha", "port elizabeth"]),
        ("FS", {"en": "Free State", "af": "Vrystaat", "zu": "Free State"}, ["free state", "vrystaat", "bloemfontein"]),
        ("GP", {"en": "Gauteng", "af": "Gauteng", "zu": "Gauteng"}, ["gauteng", "johannesburg", "joburg", "pretoria", "tshwane", "centurion", "sandton"]),
        ("KZN", {"en": "KwaZulu-Natal", "af": "KwaZulu-Natal", "zu": "KwaZulu-Natal"}, ["kwazulu natal", "kwazulu", "kzn", "natal", "durban", "ballito", "pietermaritzburg"]),
        ("LP", {"en": "Limpopo", "af": "Limpopo", "zu": "Limpopo"}, ["limpopo", "polokwane"]),
        ("MP", {"en": "Mpumalanga", "af": "Mpumalanga", "zu": "Mpumalanga"}, ["mpumalanga", "nelspruit", "mbombela"]),
        ("NW", {"en": "North West", "af": "Noordwes", "zu": "North West"}, ["north west", "noordwes", "rustenburg", "mahikeng"]),
        ("NC", {"en": "Northern Cape", "af": "Noord-Kaap", "zu": "Northern Cape"}, ["northern cape", "noord kaap", "kimberley", "upington"]),
        ("WC", {"en": "Western Cape", "af": "Wes-Kaap", "zu": "Western Cape"}, ["western cape", "wes kaap", "cape town", "kaapstad", "stellenbosch"]),
    ],
}

YES_WORDS = {"yes", "y", "yep", "yeah", "ok", "okay", "sure", "continue", "ja", "goed", "yebo", "yes please", "ja asseblief"}
NO_WORDS = {"no", "n", "nope", "nee", "cha", "no thanks", "nee dankie"}
START_WORDS = {"start", "subscribe"}  # only an explicit START re-engages someone who sent STOP

COST_PHRASES = [
    "cost", "costs", "price", "fee", "fees", "charge", "charges", "how much will it", "how much will i pay",
    "how much do you charge", "what will i pay", "what do i pay", "will i pay",
    "koste", "kos", "prys", "tarief", "hoeveel gaan dit", "hoeveel kos",
    "ixabiza", "malini", "imali engizoyikhokha",
    "going to pay", "have to pay", "need to pay", "must pay", "gaan betaal", "moet betaal",
]

REQUEST_STARTS = [
    "tell me", "please tell", "please explain", "explain", "i want to know", "i need to know", "i would like to know",
    "i wanna know", "let me know", "please advise", "please clarify", "sê vir my", "verduidelik", "ek wil weet",
    "ngicela ungitshele", "ngifuna ukwazi",
]

WHEN = {  # when the team is next available, by language
    "today": {"en": "08:00 this morning", "af": "08:00 vanoggend", "zu": "ngo-08:00 ekuseni"},
    "tomorrow": {"en": "tomorrow", "af": "môre", "zu": "kusasa"},
    "monday": {"en": "Monday", "af": "Maandag", "zu": "ngoMsombuluko"},
}

STOP_PHRASES = ["stop", "unsubscribe", "opt out", "optout", "hou op", "yeka", "yima"]

AGENT_PHRASES = [
    "agent", "human", "real person", "speak to a person", "speak to someone", "talk to a person",
    "talk to someone", "speak to a human", "praat met iemand", "regte mens", "praat met 'n mens",
    "ngifuna ukukhuluma nomuntu", "khuluma nomuntu", "umuntu langempela",
    "want a person", "need a person", "want a human", "need a human", "real human", "someone real",
    "want to speak to someone", "want to talk to someone", "need to speak to someone", "need to talk to someone",
    "speak with someone", "talk with someone", "speak to a consultant", "talk to a consultant", "speak to an agent",
    "met iemand praat", "met 'n mens praat", "wil met iemand", "ngifuna umuntu", "ngifuna ukukhuluma nomeluleki",
]

DISTRESS_PHRASES = [
    "kill myself", "end my life", "suicide", "suicidal", "want to die", "take my own life", "end it all",
    "dont want to live", "don't want to live", "do not want to live", "better off dead", "hurt myself", "harm myself",
    "selfmoord", "myself doodmaak", "wil nie meer leef", "wil doodgaan", "myself seermaak", "my lewe beeindig",
    "ukuzibulala", "ngifuna ukufa", "angifuni ukuphila", "ukuzilimaza", "ukuphelisa impilo yami",
]

# ---------------------------------------------------------------- messages
M = {
    "welcome": {
        "en": "Welcome to Pinnacle Debt Solutions 👋\nThanks for getting in touch. Please choose your language:\n\n{options}",
        "af": "Welkom by Pinnacle Debt Solutions 👋\nDankie dat jy kontak gemaak het. Kies asseblief jou taal:\n\n{options}",
        "zu": "Siyakwamukela ku-Pinnacle Debt Solutions 👋\nSiyabonga ngokuxhumana nathi. Sicela ukhethe ulimi lwakho:\n\n{options}",
    },
    "welcome_all": (
        "Welcome to Pinnacle Debt Solutions 👋 / Welkom 👋 / Siyakwamukela 👋\n\n"
        "Please choose your language / Kies jou taal / Khetha ulimi:\n\n{options}\n\n"
        "(Reply with a number / Antwoord met 'n nommer / Phendula ngenombolo)"
    ),
    "consent": {
        "en": "Hi! I'm Pinnacle's virtual assistant (an AI, not a person). I'll ask a few quick questions so one of our consultants can call you at a time that suits you.\n\nYour information is confidential, used only to assess how we can help you, and handled in line with POPIA. You can type STOP at any time.\n\nReply YES to continue.",
        "af": "Hallo! Ek is Pinnacle se virtuele assistent (KI, nie 'n mens nie). Ek sal jou 'n paar vinnige vrae vra sodat een van ons konsultante jou kan bel op 'n tyd wat jou pas.\n\nJou inligting is vertroulik, word net gebruik om te bepaal hoe ons jou kan help, en word volgens POPIA hanteer. Jy kan enige tyd STOP tik.\n\nAntwoord JA om voort te gaan.",
        "zu": "Sawubona! NginguMsizi we-Pinnacle osebenza ngobuchwepheshe be-AI, hhayi umuntu. Ngizokubuza imibuzo embalwa ukuze omunye wabeluleki bethu akushayele ucingo ngesikhathi esikulungele.\n\nUlwazi lwakho luyimfihlo, lusetshenziselwa kuphela ukuhlola ukuthi singakusiza kanjani, futhi luphethwe ngokomthetho we-POPIA. Ungabhala u-STOP noma inini.\n\nPhendula ngo-YEBO ukuze siqhubeke.",
    },
    "declined": {
        "en": "No problem at all. If you change your mind, just send us a message any time. Take care.",
        "af": "Geen probleem nie. As jy van plan verander, stuur net enige tyd 'n boodskap. Sterkte.",
        "zu": "Ayikho inkinga. Uma ushintsha umqondo, sithumelele umlayezo noma nini. Uzinakekele.",
    },
    "ask_name": {
        "en": "Great, thank you. What's your first name?",
        "af": "Mooi so, dankie. Wat is jou voornaam?",
        "zu": "Kuhle, ngiyabonga. Ubani igama lakho?",
    },
    "ask_review": {
        "en": "Are you currently under debt review or debt counselling?\n\n{options}",
        "af": "Is jy tans onder skuldhersiening (debt review) of skuldberading?\n\n{options}",
        "zu": "Ingabe okwamanje usohlelweni lwe-debt review noma lwe-debt counselling?\n\n{options}",
    },
    "not_fit": {
        "en": "Thank you for being so open, {name}. Unfortunately our process only starts at around R100\u00a0000 of debt. Below that, the fees would end up costing you more than simply paying the debt off yourself, so it wouldn't be in your interest.\n\nIf your total debt (all loans, cards and accounts together) is actually more than R100\u00a0000, just send me the amount and we'll carry on. Otherwise, I wish you well.",
        "af": "Dankie dat jy so openhartig was, {name}. Ongelukkig begin ons proses eers by ongeveer R100\u00a0000 skuld. Daaronder sou die fooie jou uiteindelik meer kos as om die skuld bloot self af te betaal, so dit sou nie in jou belang wees nie.\n\nAs jou totale skuld (alle lenings, kaarte en rekeninge saam) eintlik meer as R100\u00a0000 is, stuur net die bedrag en ons gaan voort. Andersins wens ek jou alles van die beste toe.",
        "zu": "Ngiyabonga ngokuvuleka, {name}. Ngeshwa inqubo yethu iqala cishe ku-R100\u00a0000 wesikweletu. Ngaphansi kwalokho, izindleko zingaphela zikubiza ngaphezu kokukhokha isikweletu ngokwakho, ngakho ngeke kube yinzuzo kuwe.\n\nUma isamba sezikweletu zakho zonke (zonke izimali ezibolekiwe, amakhadi nama-akhawunti) siwumkhulu kuno-R100\u00a0000, ngithumelele inani futhi siqhubeke. Uma kungenjalo, ngikufisela konke okuhle.",
    },
    "not_fit_followup": {
        "en": "Thanks, {name}. If your total debt turns out to be more than R100\u00a0000, just send me the amount and we'll carry on. I wish you well.",
        "af": "Dankie, {name}. As jou totale skuld meer as R100\u00a0000 blyk te wees, stuur net die bedrag en ons gaan voort. Ek wens jou alles van die beste toe.",
        "zu": "Ngiyabonga, {name}. Uma isamba sezikweletu zakho siba ngaphezu kuka-R100\u00a0000, ngithumelele inani futhi siqhubeke. Ngikufisela konke okuhle.",
    },
    "ask_province": {
        "en": "Nice to meet you, {name}. Which province are you in?\n\n{options}",
        "af": "Lekker om jou te ontmoet, {name}. In watter provinsie is jy?\n\n{options}",
        "zu": "Ngiyajabula ukukwazi, {name}. Uhlala kuliphi isifundazwe?\n\n{options}",
    },
    "ask_debt": {
        "en": "Thanks. Roughly how much do you owe in total, with all your debts added together (loans, credit cards, accounts, etc.)? Just type an amount, e.g. R250 000.",
        "af": "Dankie. Ongeveer hoeveel skuld het jy altesaam, met al jou skulde bymekaar (lenings, kredietkaarte, rekeninge, ens.)? Tik net 'n bedrag, bv. R250 000.",
        "zu": "Ngiyabonga. Ukweleta malini ngokulinganiselwa, uma zonke izikweletu zakho zihlanganiswe (izimali ezibolekiwe, amakhadi, ama-akhawunti, njll.)? Bhala nje inani, isib. R250 000.",
    },
    "ask_term": {
        "en": "Over how long would you like to pay? Our plans run 25 to 36 months.\n\n{options}",
        "af": "Oor hoe lank wil jy betaal? Ons planne loop 25 tot 36 maande.\n\n{options}",
        "zu": "Ungathanda ukukhokha isikhathi esingakanani? Amaplani ethu aqhubeka izinyanga ezingu-25 kuya kwezingu-36.\n\n{options}",
    },
    "estimate": {
        "en": "Thanks. A client in a similar position typically pays about {amount} per month over {months} months.\n\nThis is what a client in a similar debt range to yours would typically be paying. It is an estimate based on our standard calculation - your own figure depends on exactly what you owe and where you live, and comes from a formal quote.",
        "af": "Dankie. 'n Kliënt in 'n soortgelyke posisie betaal gewoonlik ongeveer {amount} per maand oor {months} maande.\n\nDit is wat 'n kliënt met 'n soortgelyke skuldreeks as joune gewoonlik sou betaal. Dit is 'n skatting gebaseer op ons standaardberekening - jou eie bedrag hang af van presies wat jy skuld en waar jy woon, en kom uit 'n formele kwotasie.",
        "zu": "Ngiyabonga. Ikhasimende esimeni efanayo ngokuvamile likhokha cishe {amount} ngenyanga ezinyangeni ezingu-{months}.\n\nLokhu yilokho ikhasimende elinohlobo lwezikweletu olufanayo nolwakho elivame ukukukhokha. Kuyisilinganiso esisekelwe ekubaleni kwethu okujwayelekile - inani lakho liya ngokuthi ungakanani isikweletu sakho ngempela nokuthi uhlala kuphi, futhi livela kukhotheshini esemthethweni.",
    },
    "no_figure": {
        "en": "Thanks. Your debt is outside the range I can give an estimate for, so a consultant will work out a figure with you on the call.",
        "af": "Dankie. Jou skuld is buite die reeks waarvoor ek 'n skatting kan gee, so 'n konsultant sal 'n bedrag saam met jou uitwerk tydens die oproep.",
        "zu": "Ngiyabonga. Isikweletu sakho siphandle kobubanzi engingakwazi ukunikeza isilinganiso ngabo, ngakho umeluleki uzobala inani nawe ngesikhathi socingo.",
    },
    "term_range": {
        "en": "Our plans run 25 to 36 months, nothing shorter or longer. Which would you like: 25, 30 or 36 months?",
        "af": "Ons planne loop 25 tot 36 maande, nie korter of langer nie. Watter een wil jy hê: 25, 30 of 36 maande?",
        "zu": "Amaplani ethu aqhubeka izinyanga ezingu-25 kuya kwezingu-36, akukho okufushane noma okude. Ufuna isiphi: izinyanga ezingu-25, 30 noma 36?",
    },
    "one_figure": {
        "en": "Could you give me one total figure, with all your debts added together? A rough amount is fine.",
        "af": "Kan jy my een totale bedrag gee, met al jou skulde bymekaar getel? 'n Ruwe bedrag is reg.",
        "zu": "Ungangipha inani elilodwa eliphelele, uma zonke izikweletu zakho zihlanganiswe? Isilinganiso siyafaneleka.",
    },
    "cost_need_info": {
        "en": "I can give you a rough monthly estimate once I know where you are, roughly what you owe in total, and over how long you'd like to pay. Just a few quick questions.",
        "af": "Ek kan jou 'n ruwe maandelikse skatting gee sodra ek weet waar jy is, ongeveer wat jy altesaam skuld, en oor hoe lank jy wil betaal. Net 'n paar vinnige vrae.",
        "zu": "Ngingakunikeza isilinganiso senyanga uma ngazi ukuthi uhlala kuphi, ukuthi ukweleta malini ngokuphelele, nokuthi ufuna ukukhokha isikhathi esingakanani. Imibuzo embalwa nje.",
    },
    "agent_after_hours": {
        "en": "I've noted that you'd like to speak to a person. Our team is resting until {when} so that they can give you the best possible service. Please carry on with me in the meantime: I can answer your questions and help you through the rest. As soon as a consultant is available {when}, they'll call you back.",
        "af": "Ek het genoteer dat jy met 'n persoon wil praat. Ons span rus tot {when} sodat hulle jou die allerbeste diens kan gee. Gaan asseblief intussen voort met my: ek kan jou vrae beantwoord en jou deur die res help. Sodra 'n konsultant {when} beskikbaar is, sal hulle jou terugbel.",
        "zu": "Ngiyabona ukuthi ufuna ukukhuluma nomuntu. Iqembu lethu liphumule kuze kube {when} ukuze likunike insizakalo engcono kakhulu. Sicela uqhubeke nami okwamanje: ngingaphendula imibuzo yakho futhi ngikusize ngokusele. Lapho nje umeluleki etholakala {when}, uzokubuyisela ucingo.",
    },
    "agent_after_hours_time": {
        "en": "What time would suit you?",
        "af": "Watter tyd sal jou pas?",
        "zu": "Yisiphi isikhathi esikulungele?",
    },
    "handover_after_hours": {
        "en": "No problem. I've passed this on, and a consultant will contact you {when}.",
        "af": "Geen probleem nie. Ek het dit deurgegee, en 'n konsultant sal jou {when} kontak.",
        "zu": "Ayikho inkinga. Ngikudlulisile lokhu, futhi umeluleki uzokuthinta {when}.",
    },
    "callback_updated": {
        "en": "Done, {name}. A consultant will call you: {callback}.",
        "af": "Reg so, {name}. 'n Konsultant sal jou bel: {callback}.",
        "zu": "Kulungile, {name}. Umeluleki uzokushayela ucingo: {callback}.",
    },
    "ask_marital": {
        "en": "Thanks. Are you married? If so, is it in community of property or out of community of property?\n\n{options}",
        "af": "Dankie. Is jy getroud? Indien wel, is dit binne gemeenskap van goedere of buite gemeenskap van goedere?\n\n{options}",
        "zu": "Ngiyabonga. Ingabe usushadile? Uma kunjalo, ngabe ukuhlanganyela kwempahla (in community of property) noma ngaphandle kokuhlanganyela (out of community of property)?\n\n{options}",
    },
    "ask_callback": {
        "en": "Last one. What time are you available for a call from a consultant? For example \"tomorrow after 2pm\". We call Monday to Friday, 08:00–17:00.",
        "af": "Laaste een. Op watter tyd is jy beskikbaar vir 'n oproep van 'n konsultant? Byvoorbeeld \"môre na 2nm\". Ons bel Maandag tot Vrydag, 08:00–17:00.",
        "zu": "Owokugcina. Ukhululeke ngasiphi isikhathi ukuthi umeluleki akushayele ucingo? Isibonelo \"kusasa ntambama\". Sishaya ngoMsombuluko kuya eLwesihlanu, 08:00–17:00.",
    },
    "done": {
        "en": "Thank you, {name}! That's everything I need. A consultant will call you: {callback}.{after}\n\nThey'll go through your situation properly and explain your options. If you have a question in the meantime, ask me here.",
        "af": "Dankie, {name}! Dis alles wat ek nodig het. 'n Konsultant sal jou bel: {callback}.{after}\n\nHulle sal jou situasie behoorlik deurgaan en jou opsies verduidelik. As jy intussen 'n vraag het, vra my gerus hier.",
        "zu": "Ngiyabonga, {name}! Yilokho kuphela engikudingayo. Umeluleki uzokushayela ucingo: {callback}.{after}\n\nUzohlaziya isimo sakho kahle futhi akuchazele izinketho zakho. Uma unemibuzo okwamanje, ngibuze lapha.",
    },
    "after_hours": {
        "en": " Our consultants work Mon–Fri 08:00–17:00, so you'll hear from us at the first suitable time.",
        "af": " Ons konsultante werk Maandag–Vrydag 08:00–17:00, so jy sal by die eerste geleentheid van ons hoor.",
        "zu": " Abeluleki bethu basebenza ngoMsombuluko–NgoLwesihlanu 08:00–17:00, ngakho uzozwa kithi ngesikhathi sokuqala esifanele.",
    },
    "reask": {
        "en": "Sorry, I didn't quite catch that. ",
        "af": "Jammer, ek het dit nie mooi verstaan nie. ",
        "zu": "Ngiyaxolisa, angikuzwanga kahle lokho. ",
    },
    "faq_fallback": {
        "en": "Good question; your consultant will be able to answer that properly on the call. ",
        "af": "Goeie vraag; jou konsultant sal dit behoorlik tydens die oproep kan beantwoord. ",
        "zu": "Umbuzo omuhle; umeluleki wakho uzokwazi ukuwuphendula kahle ngesikhathi socingo. ",
    },
    "handover": {
        "en": "No problem. I've asked one of our consultants to take over and contact you personally. They'll be in touch as soon as they can.",
        "af": "Geen probleem nie. Ek het een van ons konsultante gevra om oor te neem en jou persoonlik te kontak. Hulle sal so gou moontlik in verbinding tree.",
        "zu": "Ayikho inkinga. Ngicele omunye wabeluleki bethu ukuthi athathe indawo futhi akuthinte ngokwakhe. Uzokuthinta ngokushesha okukhulu.",
    },
    "distress": {
        "en": "I'm really sorry you're going through this. You're not alone, and your life matters more than any debt. If you're thinking of harming yourself, please call the SADAG Suicide Crisis Helpline on 0800 567 567 (free, 24 hours) or Lifeline on 0861 322 322 right now.\n\nI've also asked one of our consultants to contact you personally as soon as possible.",
        "af": "Dit spyt my opreg dat jy hierdeur gaan. Jy is nie alleen nie, en jou lewe is meer werd as enige skuld. As jy daaraan dink om jouself seer te maak, bel asseblief nou die SADAG Selfmoord-krisislyn by 0800 567 567 (gratis, 24 uur) of Lifeline by 0861 322 322.\n\nEk het ook een van ons konsultante gevra om jou so gou moontlik persoonlik te kontak.",
        "zu": "Ngiyadabuka ngempela ngokuthi udlula kulokhu. Awuwedwa, futhi impilo yakho ibaluleke kakhulu kuneso sikweletu. Uma ucabanga ukuzilimaza, sicela ushayele manje i-SADAG Suicide Crisis Helpline ku-0800 567 567 (mahhala, amahora angu-24) noma i-Lifeline ku-0861 322 322.\n\nNgicele futhi omunye wabeluleki bethu ukuthi akuthinte ngokushesha okukhulu.",
    },
    "stopped": {
        "en": "You've been unsubscribed and we won't message you again. If you ever want to talk, just send us a message.",
        "af": "Jy is uitgeskryf en ons sal jou nie weer boodskappe stuur nie. As jy ooit wil gesels, stuur net 'n boodskap.",
        "zu": "Ususiphumile futhi ngeke sisathumela imilayezo. Uma ufuna ukukhuluma, sithumelele umlayezo.",
    },
    "already_done": {
        "en": "Thanks {name}, your details are with our team and a consultant will call you. If you'd like to change the time, or have a question, just tell me. Type AGENT to speak to a person.",
        "af": "Dankie {name}, jou besonderhede is by ons span en 'n konsultant sal jou bel. As jy die tyd wil verander, of 'n vraag het, sê net. Tik AGENT om met 'n mens te praat.",
        "zu": "Ngiyabonga {name}, imininingwane yakho iseqenjini lethu futhi umeluleki uzokushayela. Uma ufuna ukushintsha isikhathi, noma unombuzo, ngitshele. Bhala u-AGENT ukukhuluma nomuntu.",
    },
    "voice_note": {
        "en": "I can't listen to voice notes yet. Could you type your answer instead?",
        "af": "Ek kan nog nie na stemboodskappe luister nie. Kan jy asseblief jou antwoord tik?",
        "zu": "Angikwazi ukulalela imilayezo yezwi okwamanje. Ungabhala impendulo yakho?",
    },
}

# Plain single-language helpers used in notification emails etc.
QUALIFICATION_LABEL = {"likely": "LIKELY", "unsure": "UNSURE", "": ""}


def tr(key, lang, **kw):
    entry = M[key]
    text = entry[lang] if isinstance(entry, dict) else entry
    return text.format(**kw) if kw else text


def options_text(step, lang):
    if step == "term":
        labels = [term_label(n, lang) for n in TERMS]
    else:
        labels = [labels_by_lang[lang] for _, labels_by_lang, _ in OPTIONS[step]]
    return "\n".join(f"{i}. {lbl}" for i, lbl in enumerate(labels, 1))
