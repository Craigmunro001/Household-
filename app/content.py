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
    "home": [
        ("yes", {"en": "Yes, I own a home", "af": "Ja, ek besit 'n huis", "zu": "Yebo, nginendlu"},
         ["yes", "ja", "yebo", "own", "i own", "my house", "bonded", "bond", "fully paid", "paid off", "flat", "townhouse", "huis", "indlu"]),
        ("no", {"en": "No (I rent or live with family)", "af": "Nee (ek huur of woon by familie)", "zu": "Cha (ngiqasha noma ngihlala nomndeni)"},
         ["no", "nee", "cha", "rent", "renting", "huur", "don't own", "do not own", "dont own", "nie eienaar", "with family", "with my parents", "ngiqasha"]),
    ],
    "vehicle": [
        ("yes", {"en": "Yes, a vehicle under finance", "af": "Ja, 'n voertuig onder finansiering", "zu": "Yebo, isithuthi esisakhokhelwa"},
         ["yes", "ja", "yebo", "financed", "under finance", "finance", "instalments", "installments", "still paying", "still owe", "afbetaling", "finansiering"]),
        ("no", {"en": "No vehicle", "af": "Nee, geen voertuig", "zu": "Cha, asikho isithuthi"},
         ["no", "nee", "cha", "no vehicle", "no car", "don't have", "dont have", "geen voertuig", "geen kar", "asikho"]),
        ("paid_off", {"en": "I have a vehicle, but it's fully paid off", "af": "Ek het 'n voertuig, maar dit is heeltemal afbetaal",
                      "zu": "Nginesithuthi, kodwa sikhokhiwe sonke"},
         ["paid off", "fully paid", "paid up", "settled", "freehold", "own outright", "outright", "no finance", "not financed",
          "afbetaal", "geen finansiering", "sikhokhiwe"]),
    ],
    "asset_ack": [
        ("yes", {"en": "Yes, I understand and want to continue", "af": "Ja, ek verstaan en wil voortgaan", "zu": "Yebo, ngiyaqonda futhi ngifuna ukuqhubeka"},
         ["yes", "y", "ja", "yebo", "continue", "go ahead", "carry on", "proceed", "i understand", "understand", "ok", "okay",
          "gaan voort", "ek verstaan", "qhubeka", "ngiyaqonda"]),
        ("no", {"en": "No, I'd rather not", "af": "Nee, liewer nie", "zu": "Cha, angithandi"},
         ["no", "nee", "cha", "rather not", "stop", "dont want", "don't want", "liewer nie", "angithandi"]),
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

OPTIONS["home_ack"] = OPTIONS["vehicle_ack"] = OPTIONS["asset_ack"]

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

CHANGED_MIND_PHRASES = ["continue", "yes", "yes please", "ja", "ja asseblief", "yebo", "go ahead", "carry on", "proceed", "i understand",
                        "gaan voort", "voortgaan", "qhubeka", "ngiyaqonda"]  # deliberately no bare "ok": "ok thanks" is not a yes

CORRECTION_WORDS = ["misunderstood", "mistake", "wrong", "i rent", "renting", "paid off", "fully paid", "settled", "huur", "afbetaal",
                    "ngiqasha", "i misread", "my bad"]

CHANGE_PHRASES = ["change", "wrong", "incorrect", "mistake", "not right", "isnt right", "isn't right", "verander", "fout",
                  "nie reg", "shintsha", "iphutha"]

# Craig's call: no attorney or personal names in the chat; company documents only. Add the CK number here if he decides to share it.
COMPANY_REG_NUMBER = ""

TRUST_PHRASES = [
    "scam", "scammer", "scammers", "scamming", "legit", "legitimate", "fraud", "fraudulent", "fake", "is this real", "can i trust",
    "trust you", "who are you", "who is pinnacle", "who is this", "con artist", "rip off", "ripoff", "are you a con",
    "bedrog", "bedrieg", "bedrieer", "skelm", "skelms", "swendel", "betroubaar", "wie is julle", "inkohliso", "amanga", "uyisela", "ngithembe",
    # "how do I know you're established?" questions: the same answer covers them
    "heard of you", "heard about you", "heard of pinnacle", "seen you", "on the radio", "radio station", "how long have you been",
    "been in business", "been around", "how long are you in business", "van julle gehoor", "op die radio", "hoe lank is julle",
    "ngikuzwile ku-radio", "ku-radio", "nikhona isikhathi esingakanani",
]

AI_QUESTION_PHRASES = [  # asking WHAT it is (not asking to speak to someone)
    "am i speaking to a real person", "am i talking to a real person", "am i speaking to a person", "am i talking to a person",
    "am i speaking to a human", "am i talking to a human", "are you a real person", "are you a person", "are you human",
    "are you a human", "are you a bot", "are you a robot", "are you ai", "are you an ai", "is this a bot", "is this a robot",
    "is this ai", "is this an ai", "is this automated", "is this a real person", "is this a human",
    "is jy 'n mens", "is jy 'n regte mens", "praat ek met 'n mens", "is jy 'n bot", "is dit 'n robot",
    "ungumuntu", "ngikhuluma nomuntu na", "uyirobhothi",
]

PAYMENT_PHRASES = [  # "do I stop paying my creditors while I pay Pinnacle?"
    "stop paying", "keep paying", "carry on paying", "continue paying", "still pay my", "still pay the", "pay both", "pay my creditors",
    "pay the creditors", "pay pinnacle and", "while i'm paying", "while i am paying", "pay you and my", "stop my payments",
    "ophou betaal", "bly betaal", "albei betaal", "betaal my skuldeisers", "betaal die skuldeisers",
    "ukuyeka ukukhokha", "ngiyaqhubeka ngikhokha", "ngikhokhe bobabili",
]

PAYOFF_PHRASES = [  # "can I pay it off quicker / lump sum / over more months?"
    "pay it off quicker", "pay off quicker", "pay it off faster", "pay off faster", "pay quicker", "pay faster", "pay it quicker",
    "pay it off early", "pay off early", "settle early", "settle quicker", "lump sum", "lumpsum", "pay extra", "extra payment", "extra payments",
    "pay more each month", "pay more per month", "pay in one go", "pay it all at once", "pay everything upfront", "pay upfront", "pay up front",
    "more months", "longer to pay", "pay it over longer", "spread it over",
    "vinniger afbetaal", "vinniger betaal", "klompsom", "eenmalige betaling", "ekstra betaling", "meer maande",
    "ngikhokhe ngokushesha", "inani elilodwa", "izinyanga eziningi",
]

SUMMONS_PHRASES = [  # "I already have a summons / judgment - can I still join?"
    "summons", "summonses", "judgment", "judgement", "judgments", "judgements", "court papers", "sheriff",
    "dagvaarding", "dagvaardings", "vonnis", "vonnisse", "isamanisi", "isinqumo senkantolo",
]

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


LEADS = {  # a friendly line before each question; {name} is the lead's first name
    "province": {"en": "Lovely to meet you, {name}! 🎉 Let's get you sorted.", "af": "Lekker om jou te ontmoet, {name}! 🎉 Kom ons kry jou reg.",
                 "zu": "Ngiyajabula ukukwazi, {name}! 🎉 Masikulungise."},
    "debt": {"en": "Thanks, {name}, we're on our way! 🚀", "af": "Dankie, {name}, ons is op pad! 🚀", "zu": "Ngiyabonga, {name}, sesendleleni! 🚀"},
    "home": {"en": "Great, thanks! 👍", "af": "Wonderlik, dankie! 👍", "zu": "Kuhle, ngiyabonga! 👍"},
    "vehicle": {"en": "You're doing brilliantly. 🙌", "af": "Jy doen uitstekend. 🙌", "zu": "Wenza kahle kakhulu. 🙌"},
    "term": {"en": "Almost there! 😊", "af": "Amper daar! 😊", "zu": "Sesiseduze! 😊"},
    "marital": {"en": "Just a few more, I promise. 😄", "af": "Net nog 'n paar, belowe. 😄", "zu": "Okumbalwa nje, ngiyakuthembisa. 😄"},
    "review": {"en": "Nearly done! 🏁", "af": "Amper klaar! 🏁", "zu": "Sesiphelile nje! 🏁"},
    "callback": {"en": "Last one, promise! 🤞", "af": "Die laaste een, belowe! 🤞", "zu": "Owokugcina, ngiyathembisa! 🤞"},
}

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
        "en": "Hi there! 😊 I'm Pinnacle's virtual assistant. While our consultants are busy helping clients get on top of their debt and build a brighter future, I'll take a few quick details so one of them can call you at a time that suits you.\n\nYour information is confidential, used only to assess how we can help you, and handled in line with POPIA. You can type STOP at any time.\n\nReady to get started?\n\n1. Yes, let's go!\n2. No thanks",
        "af": "Hallo daar! 😊 Ek is Pinnacle se virtuele assistent. Terwyl ons konsultante besig is om kliënte te help om hul skuld onder beheer te kry en 'n helderder toekoms te bou, neem ek 'n paar vinnige besonderhede sodat een van hulle jou kan bel op 'n tyd wat jou pas.\n\nJou inligting is vertroulik, word net gebruik om te bepaal hoe ons jou kan help, en word volgens POPIA hanteer. Jy kan enige tyd STOP tik.\n\nReg om te begin?\n\n1. Ja, kom ons gaan!\n2. Nee dankie",
        "zu": "Sawubona! 😊 Ngingumsizi we-Pinnacle we-virtual. Ngenkathi abeluleki bethu bematasa ekusizeni amakhasimende ukulawula izikweletu zawo nokwakha ikusasa eliqhakazile, mina ngizothatha imininingwane embalwa ukuze omunye wabo akushayele ucingo ngesikhathi esikulungele.\n\nUlwazi lwakho luyimfihlo, lusetshenziselwa kuphela ukuhlola ukuthi singakusiza kanjani, futhi luphethwe ngokomthetho we-POPIA. Ungabhala u-STOP noma inini.\n\nSulungele ukuqala?\n\n1. Yebo, masiqale!\n2. Cha ngiyabonga",
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
        "en": "Which province are you in?\n\n{options}",
        "af": "In watter provinsie is jy?\n\n{options}",
        "zu": "Uhlala kuliphi isifundazwe?\n\n{options}",
    },
    "ask_debt": {
        "en": "Roughly how much do you owe in total, with all your debts added together (loans, credit cards, accounts, the lot)? A rough number is perfect, just type it, e.g. R250 000.",
        "af": "Ongeveer hoeveel skuld het jy altesaam, met al jou skulde bymekaar (lenings, kredietkaarte, rekeninge, die hele spul)? 'n Ruwe bedrag is perfek, tik dit net, bv. R250 000.",
        "zu": "Ukweleta malini ngokulinganiselwa, uma zonke izikweletu zakho zihlanganiswe (izimali ezibolekiwe, amakhadi, ama-akhawunti, konke)? Isilinganiso siyafaneleka, bhala nje inani, isib. R250 000.",
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
    "term_range_long": {
        "en": "Our plans run 25 to 36 months, and 36 is the maximum. We can't go longer, because dragging the process out wouldn't be fair to your creditors, who carry their own legal costs while it continues. Which would you like: 25, 30 or 36 months?",
        "af": "Ons planne loop 25 tot 36 maande, en 36 is die maksimum. Ons kan nie langer gaan nie, want om die proses uit te rek sou nie billik wees teenoor jou skuldeisers nie, wat hul eie regskoste dra solank dit duur. Watter een wil jy hê: 25, 30 of 36 maande?",
        "zu": "Amaplani ethu aqhubeka izinyanga ezingu-25 kuya kwezingu-36, futhi engu-36 iyona ephezulu. Asikwazi ukudlulela ngale, ngoba ukudonsa inqubo ngeke kube nobulungisa kubakweletwa bakho, abathwala izindleko zabo zomthetho kuyilapho iqhubeka. Ufuna esiphi: izinyanga ezingu-25, 30 noma 36?",
    },
    "term_range_short": {
        "en": "Our plans run 25 to 36 months. If you'd like to be finished sooner, you can pay extra or a lump sum, and your consultant will explain how. Which would you like to start with: 25, 30 or 36 months?",
        "af": "Ons planne loop 25 tot 36 maande. As jy vinniger klaar wil wees, kan jy ekstra of 'n klompsom betaal, en jou konsultant sal verduidelik hoe. Met watter een wil jy begin: 25, 30 of 36 maande?",
        "zu": "Amaplani ethu aqhubeka izinyanga ezingu-25 kuya kwezingu-36. Uma ufuna ukuqeda ngokushesha, ungakhokha okwengeziwe noma inani elilodwa, futhi umeluleki wakho uzochaza ukuthi kuyenziwa kanjani. Ufuna ukuqala ngesiphi: izinyanga ezingu-25, 30 noma 36?",
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
    "ask_home": {
        "en": "Do you own a home (a house, flat or townhouse), whether it's bonded or fully paid off?\n\n{options}",
        "af": "Besit jy 'n huis (huis, woonstel of dorpshuis), of dit nou 'n verband het of heeltemal afbetaal is?\n\n{options}",
        "zu": "Ingabe unendlu (indlu, ifulethi noma i-townhouse), noma inebhondi noma ikhokhiwe yonke?\n\n{options}",
    },
    "ask_vehicle": {
        "en": "Do you have a vehicle that is still under finance (a car loan or instalment agreement)?\n\n{options}",
        "af": "Het jy 'n voertuig wat nog onder finansiering is ('n motorlening of afbetalingskontrak)?\n\n{options}",
        "zu": "Ingabe unesithuthi esisakhokhelwa ngemali-mboleko (isikweletu semoto noma isivumelwano sezinkokhelo)?\n\n{options}",
    },
    "ask_home_ack": {
        "en": "Thanks for letting me know, {name}. Before we go any further, I want to make sure you're aware of something important. With a voluntary surrender of estate, a trustee is appointed to look after your estate on behalf of your creditors, and that means your home would be sold, usually by auction, to pay off part of your debts. Your consultant will explain exactly how this works for you, so there are no surprises.\n\nWould you like to continue?\n\n{options}",
        "af": "Dankie dat jy my laat weet, {name}. Voordat ons verder gaan, wil ek seker maak jy weet van iets belangriks. By 'n vrywillige oorhandiging van boedel word 'n kurator aangestel om jou boedel namens jou skuldeisers te hanteer, en dit beteken jou huis sou verkoop word, gewoonlik op 'n veiling, om 'n deel van jou skuld te delg. Jou konsultant sal presies verduidelik hoe dit vir jou werk, sodat daar geen verrassings is nie.\n\nWil jy voortgaan?\n\n{options}",
        "zu": "Ngiyabonga ngokungazisa, {name}. Ngaphambi kokuba siqhubeke, ngifuna ukuqinisekisa ukuthi uyazi ngento ebalulekile. Ku-voluntary surrender of estate, kuqokwa umphathi (trustee) ukuze aphathe impahla yakho egameni labakweletwa, futhi lokho kusho ukuthi indlu yakho izothengiswa, ngokuvamile ngomthengisi esidlangalaleni (auction), ukuze kukhokhelwe ingxenye yezikweletu zakho. Umeluleki wakho uzochaza ngokuqondile ukuthi lokhu kusebenza kanjani kuwe, ukuze kungabikho okukumangazayo.\n\nUfuna ukuqhubeka?\n\n{options}",
    },
    "ask_vehicle_ack": {
        "en": "Thanks, {name}. Because your vehicle is still under finance, please know that the bank will take it back during the process. Your consultant will explain exactly what this means for you, so there are no surprises.\n\nWould you like to continue?\n\n{options}",
        "af": "Dankie, {name}. Omdat jou voertuig nog onder finansiering is, weet asseblief dat die bank dit gedurende die proses sal terugneem. Jou konsultant sal presies verduidelik wat dit vir jou beteken, sodat daar geen verrassings is nie.\n\nWil jy voortgaan?\n\n{options}",
        "zu": "Ngiyabonga, {name}. Ngoba isithuthi sakho sisakhokhelwa, sicela wazi ukuthi ibhange lizosithatha kabusha phakathi nenqubo. Umeluleki wakho uzochaza ngokuqondile ukuthi lokhu kusho ini kuwe, ukuze kungabikho okukumangazayo.\n\nUfuna ukuqhubeka?\n\n{options}",
    },
    "vehicle_paid_off": {
        "en": "Good to know. A vehicle that's fully paid off is a different situation, and your consultant will talk you through the options for it.",
        "af": "Goed om te weet. 'n Voertuig wat heeltemal afbetaal is, is 'n ander situasie, en jou konsultant sal die opsies daarvoor met jou deurgaan.",
        "zu": "Kuhle ukwazi. Isithuthi esikhokhiwe sonke sisimo esihlukile, futhi umeluleki wakho uzokuchazela ngezinketho zaso.",
    },
    "not_fit_home": {
        "en": "Understood, {name}, and thank you for being open with me. If you change your mind, just reply CONTINUE and we'll carry on. And if I've misunderstood (for example you rent your home), just tell me. Otherwise, I wish you well.",
        "af": "Verstaan, {name}, en dankie dat jy so openhartig was. As jy van plan verander, antwoord net CONTINUE (voortgaan) en ons gaan voort. En as ek jou verkeerd verstaan het (byvoorbeeld jy huur jou huis), sê net. Andersins wens ek jou alles van die beste toe.",
        "zu": "Ngiyaqonda, {name}, futhi ngiyabonga ngokuvuleka kimi. Uma ushintsha umqondo, phendula nje ngo-CONTINUE (qhubeka) futhi siqhubeke. Futhi uma ngingakuqondanga kahle (isibonelo uqasha indlu yakho), ngitshele nje. Uma kungenjalo, ngikufisela konke okuhle.",
    },
    "not_fit_vehicle": {
        "en": "Understood, {name}, and thank you for being open with me. If you change your mind, just reply CONTINUE and we'll carry on. And if I've misunderstood (for example your vehicle is fully paid off), just tell me. Otherwise, I wish you well.",
        "af": "Verstaan, {name}, en dankie dat jy so openhartig was. As jy van plan verander, antwoord net CONTINUE (voortgaan) en ons gaan voort. En as ek jou verkeerd verstaan het (byvoorbeeld jou voertuig is heeltemal afbetaal), sê net. Andersins wens ek jou alles van die beste toe.",
        "zu": "Ngiyaqonda, {name}, futhi ngiyabonga ngokuvuleka kimi. Uma ushintsha umqondo, phendula nje ngo-CONTINUE (qhubeka) futhi siqhubeke. Futhi uma ngingakuqondanga kahle (isibonelo isithuthi sakho sikhokhiwe sonke), ngitshele nje. Uma kungenjalo, ngikufisela konke okuhle.",
    },
    "not_fit_home_followup": {
        "en": "Thanks, {name}. Reply CONTINUE if you'd like to carry on, or tell me if I've misunderstood (for example you rent your home). I wish you well.",
        "af": "Dankie, {name}. Antwoord CONTINUE (voortgaan) as jy wil voortgaan, of sê my as ek jou verkeerd verstaan het (byvoorbeeld jy huur jou huis). Ek wens jou alles van die beste toe.",
        "zu": "Ngiyabonga, {name}. Phendula ngo-CONTINUE (qhubeka) uma ufuna ukuqhubeka, noma ungitshele uma ngingakuqondanga kahle (isibonelo uqasha indlu yakho). Ngikufisela konke okuhle.",
    },
    "not_fit_vehicle_followup": {
        "en": "Thanks, {name}. Reply CONTINUE if you'd like to carry on, or tell me if I've misunderstood (for example your vehicle is fully paid off). I wish you well.",
        "af": "Dankie, {name}. Antwoord CONTINUE (voortgaan) as jy wil voortgaan, of sê my as ek jou verkeerd verstaan het (byvoorbeeld jou voertuig is heeltemal afbetaal). Ek wens jou alles van die beste toe.",
        "zu": "Ngiyabonga, {name}. Phendula ngo-CONTINUE (qhubeka) uma ufuna ukuqhubeka, noma ungitshele uma ngingakuqondanga kahle (isibonelo isithuthi sakho sikhokhiwe sonke). Ngikufisela konke okuhle.",
    },
    "done_flagged": {
        "en": "Thank you, {name}! That's everything I need. I've noted {callback} as your preferred time. That's outside our standard calling hours (Mon–Fri, 08:00–17:00), so I've flagged it for your consultant, who will confirm it or suggest the nearest time that works.\n\nThey'll go through your situation properly and explain your options. If you have a question in the meantime, ask me here.",
        "af": "Dankie, {name}! Dis alles wat ek nodig het. Ek het {callback} as jou voorkeurtyd genoteer. Dit is buite ons gewone belure (Maandag–Vrydag, 08:00–17:00), so ek het dit vir jou konsultant gemerk, wat dit sal bevestig of die naaste tyd sal voorstel wat werk.\n\nHulle sal jou situasie behoorlik deurgaan en jou opsies verduidelik. As jy intussen 'n vraag het, vra my gerus hier.",
        "zu": "Ngiyabonga, {name}! Yilokho kuphela engikudingayo. Ngiqophe {callback} njengesikhathi osithandayo. Lokho kungaphandle kwamahora ethu avamile okushaya ucingo (uMsombuluko–uLwesihlanu, 08:00–17:00), ngakho ngikumake kumeluleki wakho, ozoqinisekisa noma aphakamise isikhathi esiseduze esisebenzayo.\n\nUzohlaziya isimo sakho kahle futhi akuchazele izinketho zakho. Uma unemibuzo okwamanje, ngibuze lapha.",
    },
    "am_i_ai": {
        "en": "I'm Pinnacle's virtual assistant, an AI, so not a person. I take your details so that one of our consultants can phone you. If you'd rather speak to a person straight away, just type AGENT.",
        "af": "Ek is Pinnacle se virtuele assistent, 'n KI, so nie 'n mens nie. Ek neem jou besonderhede sodat een van ons konsultante jou kan bel. As jy liewer dadelik met 'n mens wil praat, tik net AGENT.",
        "zu": "Ngingumsizi we-Pinnacle we-virtual, i-AI, ngakho angiyena umuntu. Ngithatha imininingwane yakho ukuze omunye wabeluleki bethu akushayele ucingo. Uma ungathanda ukukhuluma nomuntu manje, bhala nje u-AGENT.",
    },
    "summons": {
        "en": "Yes, it does work with us. Having a summons or a judgment doesn't stop you from applying. With debt review, an account that has already received a court summons can't be included in the plan. Your consultant will go through your accounts with you, including any summonses or judgments, so please have the details ready for the call.",
        "af": "Ja, dit werk wel by ons. 'n Dagvaarding of 'n vonnis keer jou nie om aansoek te doen nie. By skuldhersiening kan 'n rekening wat reeds 'n hofdagvaarding ontvang het, nie by die plan ingesluit word nie. Jou konsultant sal jou rekeninge saam met jou deurgaan, insluitend enige dagvaardings of vonnisse, so hou asseblief die besonderhede gereed vir die oproep.",
        "zu": "Yebo, kuyasebenza nathi. Ukuba ne-summons noma i-judgment akukuvimbeli ukufaka isicelo. Ku-debt review, i-akhawunti esivele yathola i-summons yenkantolo ayikwazi ukufakwa ohlelweni. Umeluleki wakho uzobheka ama-akhawunti akho nawe, kuhlanganise nanoma yimaphi ama-summons noma ama-judgment, ngakho sicela ulungise imininingwane yocingo.",
    },
    "payoff": {
        "en": "Yes, you can. You can pay it off quicker, for example with extra payments or a lump sum. Because no interest builds up, paying more each month simply finishes the plan sooner (paying double means roughly half the time) rather than changing the total. You can also spread it over more months, up to our maximum of 36. Your consultant will discuss this with you, explain how it would work and how it affects the timeline of your process.",
        "af": "Ja, jy kan. Jy kan dit vinniger afbetaal, byvoorbeeld met ekstra betalings of 'n klompsom. Omdat daar geen rente oploop nie, beteken meer betaal elke maand eenvoudig dat die plan vinniger klaar is (dubbel betaal beteken ongeveer die helfte van die tyd) eerder as dat die totaal verander. Jy kan dit ook oor meer maande versprei, tot ons maksimum van 36. Jou konsultant sal dit met jou bespreek, verduidelik hoe dit sal werk en hoe dit die tydlyn van jou proses raak.",
        "zu": "Yebo, ungakwazi. Ungakhokha ngokushesha, isibonelo ngezinkokhelo ezengeziwe noma ngenani elilodwa. Ngoba akukho nzalo eqoqekayo, ukukhokha okwengeziwe qanyanga kufinyeza uhlelo kunokushintsha isamba (ukukhokha kabili kusho cishe ingxenye yesikhathi). Ungaphinda uyisakaze phezu kwezinyanga eziningi, kuze kube yisiphetho sethu esingu-36. Umeluleki wakho uzokuxoxa nawe ngalokhu, achaze ukuthi kuzosebenza kanjani nokuthi kuthinta kanjani uhlelo lwesikhathi senqubo yakho.",
    },
    "payments": {
        "en": "Good question, and an important one. No, you won't be paying both. Here's how it works: you complete your application (this can be done the same day). We then get your credit report, verify your debts and decide whether your application can be accepted. Until we confirm that it has been accepted, please keep paying your creditors as normal and don't stop anything yourself. Once it's accepted, we ask you to start your monthly payment to us, normally from the end of that month on payday. From the moment it's accepted you stop paying your creditors, and we notify them that you've applied. Your consultant will confirm the exact dates for you.",
        "af": "Goeie vraag, en 'n belangrike een. Nee, jy sal nie albei betaal nie. So werk dit: jy voltooi jou aansoek (dit kan dieselfde dag gedoen word). Ons kry dan jou kredietverslag, verifieer jou skulde en besluit of jou aansoek aanvaar kan word. Totdat ons bevestig dat dit aanvaar is, hou asseblief aan om jou skuldeisers soos gewoonlik te betaal en moenie self enigiets stop nie. Sodra dit aanvaar is, vra ons jou om jou maandelikse betaling aan ons te begin, gewoonlik vanaf die einde van daardie maand op betaaldag. Vanaf die oomblik dat dit aanvaar is, hou jy op om jou skuldeisers te betaal, en ons stel hulle in kennis dat jy aansoek gedoen het. Jou konsultant sal die presiese datums vir jou bevestig.",
        "zu": "Umbuzo omuhle, futhi obalulekile. Cha, ngeke ukhokhe kokubili. Nakhu kusebenza kanjani: uqedela isicelo sakho (lokhu kungenziwa ngosuku olufanayo). Ngemva kwalokho sithola umbiko wakho wezikweletu, siqinisekisa izikweletu zakho bese sinquma ukuthi isicelo sakho singamukelwa yini. Kuze kube sesiqinisekisa ukuthi samukelwe, sicela uqhubeke nokukhokha abakweletwa njengenjwayelo futhi ungayeki lutho ngokwakho. Uma samukelwe, sikucela ukuthi uqale inkokhelo yakho yanyanga zonke kithi, ngokuvamile kusukela ekupheleni kwaleyo nyanga ngosuku lokukhokhelwa. Kusukela ngesikhathi samukelwe, uyeka ukukhokha abakweletwa, futhi sibazisa ukuthi usufake isicelo. Umeluleki wakho uzoqinisekisa izinsuku ngqo.",
    },
    "trust": {
        "en": "Fair question, and I'm glad you asked. Pinnacle Debt Solutions has been helping South Africans with their debt since 2016. We've advertised on East Coast Radio in KwaZulu-Natal for 3 years, on Vuma FM in KwaZulu-Natal for over a year, and on Hot FM in Gauteng for 2 years. Nothing is paid or signed in this chat, and I will never ask for your banking details. Your consultant can share our company documents with you on the call, and you can ask them anything before you decide anything.{reg} If you'd like a person now, just type AGENT.",
        "af": "Goeie vraag, en ek is bly jy het gevra. Pinnacle Debt Solutions help sedert 2016 Suid-Afrikaners met hul skuld. Ons het 3 jaar lank op East Coast Radio in KwaZulu-Natal geadverteer, meer as 'n jaar op Vuma FM in KwaZulu-Natal en 2 jaar op Hot FM in Gauteng. Niks word in hierdie gesprek betaal of onderteken nie, en ek sal nooit vir jou bankbesonderhede vra nie. Jou konsultant kan ons maatskappydokumente tydens die oproep met jou deel, en jy kan hulle enigiets vra voordat jy enigiets besluit.{reg} As jy nou met 'n mens wil praat, tik net AGENT.",
        "zu": "Umbuzo omuhle, futhi ngiyajabula ngokuthi ubuzile. I-Pinnacle Debt Solutions isiza abantu baseNingizimu Afrika ngezikweletu zabo kusukela ngo-2016. Sike sakhangisa ku-East Coast Radio eKwaZulu-Natal iminyaka emi-3, ku-Vuma FM eKwaZulu-Natal isikhathi esingaphezu konyaka owodwa, nase-Hot FM eGauteng iminyaka emi-2. Akukho okukhokhwayo noma okusayinwayo kule ngxoxo, futhi angiyikukucela imininingwane yakho yasebhange. Umeluleki wakho angabelana nawe ngamadokhumenti enkampani ngesikhathi socingo, futhi ungambuza noma yini ngaphambi kokuba unqume noma yini.{reg} Uma ufuna umuntu manje, bhala nje u-AGENT.",
    },
    "trust_reg": {
        "en": " Our registration number is {reg}.",
        "af": " Ons registrasienommer is {reg}.",
        "zu": " Inombolo yethu yokubhalisa ithi {reg}.",
    },
    "recap": {
        "en": "Here's what I've noted, {name}:\n• Province: {province}\n• Debt: about {debt}\n• Home: {home}\n• Vehicle: {vehicle}\n• Married: {marital}\n• Debt review: {review}\n• Call: {callback}\n\nIf anything isn't right, reply CHANGE and I'll flag it for your consultant to fix before they call.",
        "af": "Hier is wat ek genoteer het, {name}:\n• Provinsie: {province}\n• Skuld: ongeveer {debt}\n• Huis: {home}\n• Voertuig: {vehicle}\n• Getroud: {marital}\n• Skuldhersiening: {review}\n• Oproep: {callback}\n\nAs iets nie reg is nie, antwoord CHANGE (verander) en ek sal dit vir jou konsultant merk om reg te maak voor hulle bel.",
        "zu": "Nanku engikuqophile, {name}:\n• Isifundazwe: {province}\n• Isikweletu: cishe {debt}\n• Indlu: {home}\n• Isithuthi: {vehicle}\n• Umshado: {marital}\n• Debt review: {review}\n• Ucingo: {callback}\n\nUma kukhona okungalungile, phendula ngo-CHANGE (shintsha) futhi ngizokumaka kumeluleki wakho ukuze akulungise ngaphambi kokushaya.",
    },
    "recap_home": {
        "yes": {"en": "Yes, I own a home", "af": "Ja, ek besit 'n huis", "zu": "Yebo, nginendlu"},
        "no": {"en": "No", "af": "Nee", "zu": "Cha"},
    },
    "recap_vehicle": {
        "yes": {"en": "Under finance", "af": "Onder finansiering", "zu": "Sisakhokhelwa"},
        "no": {"en": "None", "af": "Geen", "zu": "Asikho"},
        "paid_off": {"en": "Fully paid off", "af": "Heeltemal afbetaal", "zu": "Sikhokhiwe sonke"},
    },
    "recap_marital": {
        "not_married": {"en": "No", "af": "Nee", "zu": "Cha"},
        "in_community": {"en": "Yes, in community of property", "af": "Ja, binne gemeenskap van goedere", "zu": "Yebo, in community of property"},
        "out_of_community": {"en": "Yes, out of community of property", "af": "Ja, buite gemeenskap van goedere", "zu": "Yebo, out of community of property"},
        "unsure": {"en": "Yes (regime to be confirmed)", "af": "Ja (stelsel moet bevestig word)", "zu": "Yebo (uhlelo luzoqinisekiswa)"},
    },
    "recap_review": {
        "yes": {"en": "Yes", "af": "Ja", "zu": "Yebo"},
        "no": {"en": "No", "af": "Nee", "zu": "Cha"},
        "unsure": {"en": "Not sure", "af": "Nie seker nie", "zu": "Angiqiniseki"},
    },
    "ask_correction": {
        "en": "Of course! What would you like to change? Just type it, and I'll pass it straight to your consultant so it's fixed before they call you.",
        "af": "Natuurlik! Wat wil jy verander? Tik dit net, en ek gee dit direk aan jou konsultant sodat dit reggemaak word voor hulle jou bel.",
        "zu": "Impela! Ufuna ukushintsha ini? Bhala nje, futhi ngizokudlulisela ngqo kumeluleki wakho ukuze kulungiswe ngaphambi kokuba akushayele.",
    },
    "correction_thanks": {
        "en": "Thank you, I've passed that to your consultant so it's fixed before they call you.",
        "af": "Dankie, ek het dit aan jou konsultant deurgegee sodat dit reggemaak word voor hulle jou bel.",
        "zu": "Ngiyabonga, ngikudlulisele kumeluleki wakho ukuze kulungiswe ngaphambi kokuba akushayele.",
    },
    "cb_confirm": {
        "en": "Just to confirm: {label}. Is that right?\n\n1. Yes, that's right\n2. No, change it{note}",
        "af": "Net om te bevestig: {label}. Is dit reg?\n\n1. Ja, dis reg\n2. Nee, verander dit{note}",
        "zu": "Ukuqinisekisa nje: {label}. Kulungile?\n\n1. Yebo, kulungile\n2. Cha, shintsha{note}",
    },
    "cb_confirm_note": {
        "en": "\n\n(That's outside our standard hours, so your consultant will confirm it.)",
        "af": "\n\n(Dit is buite ons gewone ure, so jou konsultant sal dit bevestig.)",
        "zu": "\n\n(Lokhu kungaphandle kwamahora ethu avamile, ngakho umeluleki wakho uzokuqinisekisa.)",
    },
    "cb_intro_guided": {
        "en": "I want to get this exactly right for you, so let's do it in two quick steps. ",
        "af": "Ek wil dit presies reg kry vir jou, so kom ons doen dit in twee vinnige stappe. ",
        "zu": "Ngifuna ukuyithola ngqo kuwe, ngakho masiyenze ngezinyathelo ezimbili ezisheshayo. ",
    },
    "cb_intro_time": {
        "en": "{time}, got it. ",
        "af": "{time}, reg so. ",
        "zu": "{time}, kulungile. ",
    },
    "cb_intro_past": {
        "en": "That time has already passed, so let's pick another. ",
        "af": "Daardie tyd het reeds verby gegaan, so kom ons kies 'n ander een. ",
        "zu": "Lesosikhathi sesidlulile, ngakho masikhethe esinye. ",
    },
    "cb_ask_day": {
        "en": "{intro}Which day suits you?\n\n{options}",
        "af": "{intro}Watter dag pas jou?\n\n{options}",
        "zu": "{intro}Yisiphi usuku olukulungele?\n\n{options}",
    },
    "cb_ask_time": {
        "en": "{day}, got it. What time suits you?\n\n{options}\n\nOr just type a time, like \"10:30\".{note}",
        "af": "{day}, reg so. Watter tyd pas jou?\n\n{options}\n\nOf tik net 'n tyd, soos \"10:30\".{note}",
        "zu": "{day}, kulungile. Yisiphi isikhathi esikulungele?\n\n{options}\n\nNoma bhala nje isikhathi, njengo \"10:30\".{note}",
    },
    "cb_day_other": {
        "en": "No problem! Type the day, like \"Friday\" or \"12 Nov\".",
        "af": "Geen probleem nie! Tik die dag, soos \"Vrydag\" of \"12 Nov\".",
        "zu": "Ayikho inkinga! Bhala usuku, njengo \"Lwesihlanu\" noma \"12 Nov\".",
    },
    "cb_time_other": {
        "en": "No problem! Type the time you'd like, like \"10:30\" or \"after 2pm\".",
        "af": "Geen probleem nie! Tik die tyd wat jy wil hê, soos \"10:30\" of \"na 2nm\".",
        "zu": "Ayikho inkinga! Bhala isikhathi osifunayo, njengo \"10:30\" noma \"ngemva kwe-2 ntambama\".",
    },
    "cb_suggest": {
        "en": "No stress! Would you like me to ask your consultant to suggest a time that works?\n\n1. Yes please\n2. No, let me try again",
        "af": "Geen stres nie! Wil jy hê ek moet jou konsultant vra om 'n tyd voor te stel wat werk?\n\n1. Ja asseblief\n2. Nee, laat ek weer probeer",
        "zu": "Awukho umdlandla! Ungathanda ukuthi ngicele umeluleki wakho aphakamise isikhathi esisebenzayo?\n\n1. Yebo ngicela\n2. Cha, ake ngizame futhi",
    },
    "callback_flexible": {
        "en": "Consultant to suggest a time",
        "af": "Konsultant stel 'n tyd voor",
        "zu": "Umeluleki aphakamise isikhathi",
    },
    "done_flexible": {
        "en": "Thank you, {name}! That's everything I need. A consultant will be in touch to agree a time with you.\n\nThey'll go through your situation properly and explain your options. If you have a question in the meantime, ask me here.",
        "af": "Dankie, {name}! Dis alles wat ek nodig het. 'n Konsultant sal met jou in verbinding tree om 'n tyd te ooreenkom.\n\nHulle sal jou situasie behoorlik deurgaan en jou opsies verduidelik. As jy intussen 'n vraag het, vra my gerus hier.",
        "zu": "Ngiyabonga, {name}! Yilokho kuphela engikudingayo. Umeluleki uzokuthinta ukuvumelana ngesikhathi.\n\nUzohlaziya isimo sakho kahle futhi akuchazele izinketho zakho. Uma unemibuzo okwamanje, ngibuze lapha.",
    },
    "opt_another_day": {"en": "Another day", "af": "'n Ander dag", "zu": "Elinye usuku"},
    "opt_other_time": {"en": "A different time", "af": "'n Ander tyd", "zu": "Esinye isikhathi"},
    "callback_weekend_note": {
        "en": " Our standard hours are Mon–Fri, 08:00–17:00, so I'll flag it for your consultant to confirm.",
        "af": " Ons gewone ure is Maandag–Vrydag, 08:00–17:00, so ek sal dit vir jou konsultant merk om te bevestig.",
        "zu": " Amahora ethu avamile uMsombuluko–uLwesihlanu, 08:00–17:00, ngakho ngizokumaka kumeluleki wakho ukuze aqinisekise.",
    },
    "callback_outside": {
        "en": " That's outside our standard calling hours (Mon–Fri, 08:00–17:00), so I've flagged it for your consultant, who will confirm or suggest the nearest time that works.",
        "af": " Dit is buite ons gewone belure (Maandag–Vrydag, 08:00–17:00), so ek het dit vir jou konsultant gemerk, wat dit sal bevestig of die naaste tyd sal voorstel wat werk.",
        "zu": " Lokho kungaphandle kwamahora ethu avamile okushaya ucingo (uMsombuluko–uLwesihlanu, 08:00–17:00), ngakho ngikumake kumeluleki wakho, ozoqinisekisa noma aphakamise isikhathi esiseduze esisebenzayo.",
    },
    "callback_unclear": {
        "en": "Requested: {raw} (consultant to confirm)",
        "af": "Versoek: {raw} (konsultant om te bevestig)",
        "zu": "Isicelo: {raw} (umeluleki aqinisekise)",
    },
    "progress": {
        "en": "Only {n} questions left.",
        "af": "Net {n} vrae oor.",
        "zu": "Kusele imibuzo engu-{n} kuphela.",
    },
    "ask_marital": {
        "en": "Are you married? If so, is it in community of property or out of community of property?\n\n{options}",
        "af": "Is jy getroud? Indien wel, is dit binne gemeenskap van goedere of buite gemeenskap van goedere?\n\n{options}",
        "zu": "Ingabe usushadile? Uma kunjalo, ngabe ukuhlanganyela kwempahla (in community of property) noma ngaphandle kokuhlanganyela (out of community of property)?\n\n{options}",
    },
    "ask_callback": {
        "en": "When suits you best for a call from a consultant? Our calling hours are Mon–Fri, 08:00–17:00.\n\n1. {d}, 08:00\n2. {d}, 10:00\n3. Another day or time\n4. Let my consultant suggest a time\n\nOr just type a day and time, like \"Friday at 2pm\".",
        "af": "Wanneer pas dit jou die beste vir 'n oproep van 'n konsultant? Ons bel Maandag tot Vrydag, 08:00–17:00.\n\n1. {d}, 08:00\n2. {d}, 10:00\n3. 'n Ander dag of tyd\n4. Laat my konsultant 'n tyd voorstel\n\nOf tik net 'n dag en tyd, soos \"Vrydag om 2nm\".",
        "zu": "Ukhululeka nini ukuthi umeluleki akushayele ucingo? Sishaya ngoMsombuluko kuya eLwesihlanu, 08:00–17:00.\n\n1. {d}, 08:00\n2. {d}, 10:00\n3. Elinye usuku noma isikhathi\n4. Mayibe umeluleki wami aphakamise isikhathi\n\nNoma bhala nje usuku nesikhathi, njengo \"Lwesihlanu ngo-2 ntambama\".",
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
