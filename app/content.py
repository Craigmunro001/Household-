"""All client-facing wording (English / Afrikaans / isiZulu) and answer options.

DRAFT: legal wording must be signed off by David Schoonraad, and the Afrikaans and
isiZulu text should be read by a native speaker before going live.
"""

LANGS = ("en", "af", "zu")
LANG_NAMES = {"en": "English", "af": "Afrikaans", "zu": "isiZulu"}

# Debt bands in rand: (from, to). to=None means open-ended. Placeholders; extend as needed.
BANDS = [
    (0, 100_000),
    (100_000, 120_000),
    (120_000, 150_000),
    (150_000, 200_000),
    (200_000, 300_000),
    (300_000, 500_000),
    (500_000, None),
]


def band_key(band):
    lo, hi = band
    return f"{lo}-{hi}" if hi else f"{lo}+"


def rand(n):
    return "R" + f"{n:,}".replace(",", " ")


def band_label(band, lang):
    lo, hi = band
    if lo == 0:
        return {"en": f"Under {rand(hi)}", "af": f"Minder as {rand(hi)}", "zu": f"Ngaphansi kuka-{rand(hi)}"}[lang]
    if hi is None:
        return {"en": f"{rand(lo)} or more", "af": f"{rand(lo)} of meer", "zu": f"{rand(lo)} noma ngaphezulu"}[lang]
    return f"{rand(lo)} – {rand(hi)}"


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

STOP_PHRASES = ["stop", "unsubscribe", "opt out", "optout", "hou op", "yeka", "yima"]

AGENT_PHRASES = [
    "agent", "human", "real person", "speak to a person", "speak to someone", "talk to a person",
    "talk to someone", "speak to a human", "praat met iemand", "regte mens", "praat met 'n mens",
    "ngifuna ukukhuluma nomuntu", "khuluma nomuntu", "umuntu langempela",
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
    "ask_debt": {
        "en": "Nice to meet you, {name}. How much debt do you have in rand value, roughly (loans, credit cards, accounts, etc.)? Reply with the number:\n\n{options}\n\nYou can also just type an amount, e.g. R250 000.",
        "af": "Lekker om jou te ontmoet, {name}. Ongeveer hoeveel skuld het jy altesaam (lenings, kredietkaarte, rekeninge, ens.)? Antwoord met die nommer:\n\n{options}\n\nJy kan ook net 'n bedrag tik, bv. R250 000.",
        "zu": "Ngiyajabula ukukwazi, {name}. Ngokulinganiselwa, inkokhelo ingakanani yezikweletu zakho zonke (izimali ezibolekiwe, amakhadi, ama-akhawunti, njll.)? Phendula ngenombolo:\n\n{options}\n\nUngabhala nje inani, isib. R250 000.",
    },
    "ask_review": {
        "en": "Are you currently under debt review or debt counselling?\n\n{options}",
        "af": "Is jy tans onder skuldhersiening (debt review) of skuldberading?\n\n{options}",
        "zu": "Ingabe okwamanje usohlelweni lwe-debt review noma lwe-debt counselling?\n\n{options}",
    },
    "ask_marital": {
        "en": "Thanks. Are you married? If so, is it in community of property or out of community of property?\n\n{options}",
        "af": "Dankie. Is jy getroud? Indien wel, is dit binne gemeenskap van goedere of buite gemeenskap van goedere?\n\n{options}",
        "zu": "Ngiyabonga. Ingabe usushadile? Uma kunjalo, ngabe ukuhlanganyela kwempahla (in community of property) noma ngaphandle kokuhlanganyela (out of community of property)?\n\n{options}",
    },
    "ask_province": {
        "en": "Which province are you in?\n\n{options}",
        "af": "In watter provinsie is jy?\n\n{options}",
        "zu": "Uhlala kuliphi isifundazwe?\n\n{options}",
    },
    "ask_callback": {
        "en": "Last one. What time are you available for a call from a consultant? For example \"tomorrow after 2pm\". We call Monday to Friday, 08:00–17:00.",
        "af": "Laaste een. Op watter tyd is jy beskikbaar vir 'n oproep van 'n konsultant? Byvoorbeeld \"môre na 2nm\". Ons bel Maandag tot Vrydag, 08:00–17:00.",
        "zu": "Owokugcina. Ukhululeke ngasiphi isikhathi ukuthi umeluleki akushayele ucingo? Isibonelo \"kusasa ntambama\". Sishaya ngoMsombuluko kuya eLwesihlanu, 08:00–17:00.",
    },
    "done": {
        "en": "Thank you, {name}! That's everything I need. A consultant will call you: {callback}.{fee}{after}\n\nThey'll go through your situation properly and explain your options. If you have a question in the meantime, ask me here.",
        "af": "Dankie, {name}! Dis alles wat ek nodig het. 'n Konsultant sal jou bel: {callback}.{fee}{after}\n\nHulle sal jou situasie behoorlik deurgaan en jou opsies verduidelik. As jy intussen 'n vraag het, vra my gerus hier.",
        "zu": "Ngiyabonga, {name}! Yilokho kuphela engikudingayo. Umeluleki uzokushayela ucingo: {callback}.{fee}{after}\n\nUzohlaziya isimo sakho kahle futhi akuchazele izinketho zakho. Uma unemibuzo okwamanje, ngibuze lapha.",
    },
    "fee_line": {
        "en": " Based on what you've told me, our fees for matters like yours are typically {range}. This is only an estimate; your consultant will confirm it after a proper assessment.",
        "af": " Gebaseer op wat jy my vertel het, is ons fooie vir sake soos joune gewoonlik {range}. Dit is net 'n skatting; jou konsultant sal dit bevestig ná 'n behoorlike assessering.",
        "zu": " Ngokusekelwe kulokho ongitshele khona, izindleko zethu zezindaba ezifana nezakho ngokuvamile ziyi-{range}. Lokhu kuyisilinganiso nje; umeluleki wakho uzokuqinisekisa ngemva kokuhlola ngokufanele.",
    },
    "range": {
        "en": "between {min} and {max}",
        "af": "tussen {min} en {max}",
        "zu": "phakathi kuka-{min} no-{max}",
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


def options_text(step, lang, bands=BANDS):
    if step == "debt":
        labels = [band_label(b, lang) for b in bands]
    else:
        labels = [labels_by_lang[lang] for _, labels_by_lang, _ in OPTIONS[step]]
    return "\n".join(f"{i}. {lbl}" for i, lbl in enumerate(labels, 1))
