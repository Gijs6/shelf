import argparse
import random
from datetime import timedelta

from app import app
from models import Note, StickyNote, Todo, db, now

NOTE_SEEDS = [
    ("Ruimte tussen geest en lichaam", "Ruimte scheidt de lichamen, niet de geesten."),
    ("Kiesraad Den Haag", "Er is een Kiesraad, gevestigd te 's-Gravenhage."),
    (
        "Secretariaat locatie Den Helder",
        "Het secretariaat van het centrum is gevestigd Polderweg 60, den Helder.",
    ),
    (
        "Essentie van schilderkunst",
        "En de waarheid der Kunst, de waarheid der schilderkunst dat is de eigenschap van den Vorm en der kleur. Niets anders.",
    ),
    (
        "Scheepsramp Hongkong bericht",
        "Een Reuter-telegram uit Hongkong meldt, dat een inlandsch vaartuig op de Westrivier is omgeslagen en 200 personen daarbij zijn omgekomen.",
    ),
    (
        "Correctie toneelverslag Elsloo/Hasloo",
        "In ons verslag van de tooneeluitvoering van Zondag jl. was een fout geslopen. Niet de tooneelclub „Elsloo” doch „Hasloo” bracht een avond voor den Bond van Groote Gezinnen.",
    ),
    (
        "Zitting Tweede Kamer – landbouwmissive",
        "In de zitting van de Tweede Kamer der Staten-Generaal van heden is ingekomen eene missive der commissie van landbouw in Limburg, ten geleide van een afschrift van een aan Z. M. toegezonden adres. Dit stuk niet gezegeld zijnde, wordt ter zijde gelegd.",
    ),
    (
        "Parlementair wetsvoorstel vestingwerken",
        "In de zitting van de Tweede Kamer der Staten-Generaal van heden zijn de beraadslagingen voortgezet over het wets-ontwerp, houdende bepalingen betrekkelijk het bouwen, planten en het maken van andere werken binnen zekeren afstand van vestingwerken van den Staat.",
    ),
    (
        "Socrates en de aanklacht",
        "De formule der aanklacht wordt in de Verdediging zelf aangeduid, en ook bij Xenophon bijna geheel vermeld. Volledig vindt men ze bij Diogenes Laërtius in het leven van Socrates.",
    ),
    (
        "Ptolemaeus en het Almagest",
        "Ptolomaeus, Claudius: astronoom en wiskundige te Alexandrië in de eerste helft der 2e eeuw voor Chr. Zijn werk: „Syntaxis mathematica”, omtrent 827 in het Arabisch vertaald als: Almagest (het grote werk), ontvouwt het Ptolomaeische wereldsysteem met de aarde als middelpunt voor ons planetenstelsel.",
    ),
    (
        "Seizoenen van arbeid en tijd",
        "Nu het huis klaar was, konden de mannen, die het gebouwd hadden, voortaan hun makkers helpen in het vervoeren van goederen en levensmiddelen. En dat was gelukkig, want och, wat waren het al korte daagjes geworden!",
    ),
    (
        "Prijsvraag beeldhouwkunst Gent 1857",
        "Het Koninkl. genootschap voor fraaije kunsten en Letterkunde te Gent heeft eene prijsvraag uitgeschreven, verlangende eene geschiedenis der beeldhouwkunst in Belgie, sedert de invoering des Christendoms tot op het einde der 18de eeuw. De uitgeloofde prijs is 500 fr. en de antwoorden moeten voor 1o Oct. 1857 ingezonden worden.",
    ),
    (
        "Muzikale avond Brussel",
        "In het conservatorium te Brussel hebben de Nederlandsche violiste Annie Mesritz en de Zwitsersche pianiste Carola Pajonk een interessanten sonatenavond gegeven, welken talrijke leden van de Nederlandsche kolonie, onder wie de gezant en mevrouw Patijn, hebben bijgewoond.",
    ),
    (
        "Historische parallellen Frankrijk",
        "In Frankrijk vermeerderen met den dag de teekenen van overeenkomst tusschen het heden en de gebeurtenissen van vóór 100 jaar; en telkenmale, waar het pas geeft, doen de bladen dit uitkomen.",
    ),
    (
        None,
        "De militaire hospitaalschepen, waaronder te verstaan de schepen door de Staten gebouwd of ingericht in 't bijzonder en uitsluitend met het doel om hulp te verleenen aan de gewonden, zieken en schipbreukelingen, en waarvan de namen aan de oorlogvoerende Mogendheden moeten zijn medegedeeld bij den aanvang of in den loop der vijandelijkheden, in ieder geval vóór eenige ingebruikstelling, worden geëerbiedigd en kunnen gedurende de vijandelijkheden niet worden prijs gemaakt.",
    ),
    (
        None,
        "„Het Huis, oud en nieuw”, de uitgave van den architect Ed. Cuypers, die in de laatst verschenen afl. o. a. een door hem verbouwd buitenhuis te Princenhage afbeeldt en bespreekt, is deze maand grootendeels gewijd aan den stoel. Dr. Vogelsang vervolgt zijn opstel over „Zetels en Stoelen”, waarbij weer een aantal leuningstoelen zijn gereproduceerd. En hij belooft ons een hoofdstuk over den modernen armstoel, een zeer netelig onderwerp, waarnaar wij belangstellend uitzien.",
    ),
    (
        None,
        "Het moderne socialisme is volgens zijn inhoud in de eerste plaats het product van de aanschouwing, eenerzijds van de in de huidige maatschappij heerschende klassentegenstellingen van bezittenden en bezitloozen, kapitalisten en loonarbeiders, anderzijds van de in de productie heerschende anarchie. Maar volgens zijn theoretischen vorm doet het zich aanvankelijk voor als een verder opgevoerde, zoogenaamd consequenter doorvoering van de door de groote fransche wijsgeeren der 18de eeuw geformuleerde beginselen. Als elke nieuwe theorie, moest het beginnen met aan te sluiten aan het aanwezig gedachtenmateriaal, hoezeer ook zijn wortel in de stoffelijke, economische feiten lag.",
    ),
    (
        None,
        "eder weet, dat vele dieren op bepaalde of onbepaalde tijden in groote scharen van de eene plaats naar de andere trekken. Zulk eene neiging tot verhuizing is ook aan sommige insekten eigen, en genoeg bekend is het, hoe in de warmere streken, somwijlen sprinkhanen (vooral Gryllus migratorius) in zulk een verbazend aantal zich te zamen op reis begeven, dat zij als eene wolk de zon verduisteren, en een ware plaag worden voor de bewoners wier velden zij bezoeken, om hunnen oogst binnen weinig tijds geheel te vernielen. Zeldzamer is het volgende geval, dat voor korten tijd in het naburige Belgie plaats greep, en door den hoogleeraar morren aan de Belgische Akademie in hare zitting van den 2den July 1853 werd medegedeeld.",
    ),
    (
        None,
        "Der dierbre Vrouw,\nwier liefde en trouw\nsints driemaal dertien jaren,\nin elken strijd,\nten allen tijd,\nin zielsbezwaren en gevaren,\nmy stond ter zij;\nen nu met my\nby d' aanblik weêr van deze bladen\ngeeft lof en eer\naan haren Heer,\nvan al Zijn wegen en Zijn daden.",
    ),
    (
        None,
        "De lente — ik sta midden in haar —\no daar komt ze daar daar\nwaar vliegt ze op mij aan, ze zoent me,\nze zoent me, ze zoent me en ze noemt me\nhaar zoete ademen, woord voor woord ;\no en daar vliegt ze voort\nde honnege fladderende lente,\ndaar naar de verte, daar naar de horizonnerige tenten,\nde zilveren, zilvervoetige, zilverhandige lente,\nde zomerige lente.",
    ),
    (
        None,
        "Kijk nu, ze strooit den zomer rond\ndie vliegt om haar rond\nuit haar mond,\nrond haar boezem, haar gladde rug, haar beenen\nzoo donslicht omschenen,\nze gaat langs de horizonnen\nmaar aldoor omme,\nze heeft toch zoo veel, ze kan geven\nwel, zie het lichte sneven\nvan al dat kwijnende levende stervende opflikkerend licht\nen daar midde' in haar gezicht,\nzie je het wel, zie je het wel —\nhow licht hoe wit hoe goud hoe schel,\nhoe kunnen we het toch verdragen\nvan ochtend tot avonddage,\nkom weer, kom bij me weer\ngij mijn lieve, mijn lieve, lieve, lieve oogenbegeer.",
    ),
    (
        None,
        "O ze valt op mijn borst,\nhaar mond midde' in de dorst\nvan mijn mond, haar roode zachte weeke punttong —\n't is of ze heelemaal in me drong.",
    ),
    (
        None,
        "De straalpralende dag,\nde aardwijde hemeldag,\nlente in nooit geziene\nlicht — het blauw moesseliene\nwittig schitt'rend omhoog,\nalleen ' t zongouden éénoog.\n\nBinnen is kalm gepraal\npaarllicht, niet één zonnestraal.",
    ),
    (
        None,
        "k zal terugkomen En dan zal ik de waarheid zeggen. Ik zal zeggen dat gij op de schilderijen van Van Gogh en den dommen Millet arme boeren en vervallen levens kunt zien; maar ik zèg wanneer ge iemand in de stad ziet wandelen in fraaigesneden kleeding, iemand met ’n opgeruimden tred en ’n lachend gelaat, zóó iemand arm is en ik zal er bijvoegen dat die boeren rijk zijn. Kijk eens naar de brabantsche dier-boeren welken Vincent schildert het is alles bij elkaâr ’n komedie van Armoede.\n\nNeen van Gogh, neen Millet! Gij liegt. De boer is ’n ongemest beest, dat zich zelf èn zijn vrouw en zijne kinderen laar verarmen en verhongeren. Hij wil er uitzien als ’n schooier en zijne familie is ’n familie van schooiers wonende in stinkende beestenhokken, levende op steenen vloeren. Wanneer ’n schilder dus bij mij, die nu de waarheid weet van den Boer aankomt met vervallen hutjes en arme gehavende boeren, dan zal ik in het openbaar waar mijn mond door iedereen gezien wordt, in het licht op dat werk spuwen.\n\nWeg met uwe Schijnvertooning van leugens. Wij willen de waarheid der Kunst.",
    ),
    (
        None,
        "Leidt ons niet in Verzoeking!\nTracht niet op ons sentimenteel gevoel te werken, door voor ons armoedige gezichten uit te stallen. Het is de bedoeling der Kunst niet dat wij na het zien van vorm en kleur de hand in den zak steken om ’n bedelaar of boer ’n aalmoes te geven. Het is de bedoeling der schilderkunst dat wij na het zien der eigenschappen van Vorm, kleur, rythme het Leven lief hebben de waarheid kennen, de gedachte begrijpen de hartstochten beminnen.",
    ),
    (
        None,
        "s Gravenhage den 27 July. Eergiſteren zyn dertig van des Konings Lyfguardes na Loo vertrokken. De Karoſſen van ſijn Majeſteit zyn na Honslardyk, en word Hoog gemelde ſijne Majt. in ’t kort te gemoet geſien. De Heeren Staten van Holland en Weſt-Vriesland, die tot giſteren middag by een zyn geweeſt, ſullen aenſtaende Dingsdag weder vergaderen. De Heer van Dykvelt word in 1 a 2 dagen van Bruſsel verwagt. De Tranſportſchepen met des Konings paerden zyn uyt Engeland aengekomen, en gaen de tachtig Lyfguardes morgen of overmorgen vanhier, om in de tranſportſchepen na Engeland ſcheep te gaen. Deſe voormiddag is de Envoyé van Portugael de Heer Pachieco van Utrecht weder alhier aengekomen. Wegens den Raed van State zyn tot de verpachtinge genomineerd de Heeren de Vicq en van Renſwou na ’s Hertogenboſch en andere plaetsen op de Maes, en de Heeren de Lange en Eeck na die van Vlaenderen, werwaerts zy in d’aenſtaende maend ſullen vertrekken. De Heer vander Clouſen is vertrokken, om de beſtedinge van de aerde Fortificatiewerken tot Zutphen en Swol, nevens andere Heeren Gecommitteerden van den Raed van State by te woonen. De Generael Zales, Gouverneur van Breda, is alhier aengekomen, en worden in ’t kort noch meer Generaels en andere Heeren verwagt, onder anderen de Hertog van Holſtein Pleun. De Brigadier en Opper Jagermeeſter van den Koning is uyt Engeland aengekomen.",
    ),
    (
        None,
        "Morgen, 16 Mei, zal de bouwmeester Dr. Cuypers den eerbiedwaardigen leeftijd van tachtig jaren hebben bereikt. Wij wenschen bij deze gelegenheid enkele feiten uit zijn werkzaam leven bijeen te brengen.\n\nPetrus Josephus Hubertus Cuypers, geboren 16 Mei 1827 te Roermond, ontving een gymnasiale opleiding in zijn geboortestad. Hij studeerde van 1846 af aan de Academie te Antwerpen en behaalde er in 1849 den »prix d’excellence« en de gouden medaille voor bouwkunst. Zijn verdere studie volbracht hij in Frankrijk en Duitschland. Op last van den bisschop van Roermond ontwierp hij in 1859 het restauratieplan van de Onze-Lieve-Vrouwen-Munsterkerk. Door een conflict met de kerkeraden kwam hij in aanraking met Viollet-le-Duc, die als scheidsrechter naar Roermond ontboden was, en van dien tijd dagteekent een groote vriendschap met den meest bekenden en kundigsten van alle Fransche archaeologen.",
    ),
]

NOTE_GROUPS = ["Research", "Poetry", "History"]

STICKY_SEEDS = [
    {"content": "Buy milk", "colour": "yellow"},
    {"content": "Call dentist", "colour": "pink", "pinned": True},
    {"content": "Pick up parcel", "colour": "orange"},
    {"content": "Water plants", "colour": "green"},
    {
        "title": "Pay rent",
        "content": "Transfer by the 1st, landlord's account details are in the notes app.",
        "colour": "blue",
        "pinned": True,
    },
    {"content": "Laundry", "colour": "yellow"},
    {
        "title": "Groceries",
        "content": "- [x] bread\n- [ ] cheese\n- [ ] coffee\n- [ ] something for the weekend",
        "colour": "green",
    },
    {"content": "Renew library books", "colour": "pink", "expires_days": -3},
    {"content": "Bring plants inside", "colour": "orange", "expires_days": 2},
    {"content": "Take out trash", "colour": "green"},
    {"content": "Check tyre pressure", "colour": "blue"},
    {
        "title": "Concert tickets",
        "colour": "purple",
        "expires_days": 5,
    },
    {
        "title": "Old warranty reminder",
        "colour": "purple",
        "pinned": True,
        "expires_days": -10,
    },
    {"content": "Cancel old subscription", "colour": "orange", "deleted": True},
]


TODO_SEEDS = [
    {
        "title": "Clean apartment",
        "state": "open",
        "content": (
            "Whole place needs a proper clean.\n\n"
            "- [ ] vacuum floors\n"
            "- [ ] wipe kitchen surfaces\n"
            "- [ ] sort clutter on desk\n"
            "- [ ] bathroom cleanup"
        ),
        "group": "Home",
    },
    {
        "title": "Do groceries",
        "state": "active",
        "content": (
            "Basic food supplies running low.\n\n"
            "Need:\n\n"
            "- [x] milk\n"
            "- [x] bread\n"
            "- [ ] eggs\n"
            "- [ ] coffee\n"
            "- [ ] fruit"
        ),
        "group": "Home",
    },
    {
        "title": "Call dentist",
        "state": "open",
        "content": "Book routine check-up.\n\nPrefer morning slot if available.",
        "deadline_days": 3,
        "group": "Health",
    },
    {
        "title": "Sort paperwork",
        "state": "active",
        "content": "Old letters and documents.\n\nMostly things that should probably be thrown away.",
        "archived": True,
    },
    {
        "title": "Laundry",
        "state": "done",
        "content": "Washed and folded.\n\nStill need to put some things back in place.",
    },
    {
        "title": "Return library books",
        "state": "open",
        "content": "Due soon.\n\nCheck if there are any late fees already.",
        "deadline_days": -2,
    },
    {
        "title": "Pay bills",
        "state": "active",
        "content": "Internet and electricity pending.\n\nShould take less than 5 minutes once logged in.",
        "deadline_days": 1,
        "group": "Finance",
    },
    {
        "title": "Plan weekend",
        "state": "open",
        "content": (
            "Keep it simple.\n\nMaybe:\n\n"
            "- [ ] clean a bit\n"
            "- [ ] go outside if weather is ok\n"
            "- [ ] rest"
        ),
    },
    {
        "title": "Buy household items",
        "state": "done",
        "content": (
            "Lightbulbs, cleaning supplies.\n\n"
            "- [x] lightbulbs\n"
            "- [x] cleaning supplies\n"
            "- [x] checked what else is running low"
        ),
        "group": "Home",
    },
    {
        "title": "Call family",
        "state": "active",
        "content": "Check in sometime this week.",
    },
    {"title": "Stamps", "state": "done", "content": ""},
    {"title": "Wash car", "state": "cancelled", "content": "", "deleted": True},
    {
        "title": "Book flights",
        "state": "cancelled",
        "content": "Prices went up too much, waiting for a better deal.\n\nMight revisit next month.",
    },
    {
        "title": "Repot plants",
        "state": "done",
        "content": "Did all three. One had root rot but seemed otherwise fine.",
    },
    {
        "title": "Submit expense report",
        "state": "open",
        "content": "Due today, receipts are already scanned.",
        "deadline_days": 0,
        "group": "Finance",
    },
    {
        "title": "Water succulents",
        "state": "open",
        "content": "Only need this every couple of weeks.",
        "deadline_days": 20,
        "group": "Home",
    },
    {
        "title": "Take out recycling",
        "state": "open",
        "content": "Bins go out every other week.",
        "deadline_days": 2,
        "group": "Home",
    },
    {
        "title": "Review monthly budget",
        "state": "open",
        "content": "Go through spending and update the sheet.",
        "deadline_days": 10,
        "group": "Finance",
    },
    {
        "title": "Reorganize home office",
        "state": "open",
        "content": (
            "Desk setup has been bugging me for a while, finally have a free day to deal with it.\n\n"
            "## Plan\n\n"
            "1. [ ] Take everything off the desk and sort into keep / trash / storage\n"
            "2. [ ] Move monitor arm to the other side, cable runs are cleaner that way\n"
            "3. [ ] Get rid of the second chair, it's just collecting stuff\n"
            "4. [ ] Figure out where the box of old cables actually needs to go\n\n"
            "## Cables\n\n"
            "Should probably just buy a cable tray instead of doing another zip-tie job "
            "that falls apart in three months.\n\n"
            "## Not doing this time\n\n"
            "- painting the wall (separate weekend project)\n"
            "- new desk (current one is fine, just messy)\n\n"
            "If this takes longer than a day I'll just stop and pick it up next weekend "
            "instead of rushing it."
        ),
    },
    {
        "title": "Prepare tax return",
        "state": "active",
        "content": (
            "Deadline is coming up, so actually collecting everything instead of putting "
            "it off again.\n\n"
            "## To collect\n\n"
            "- [x] annual income statement\n"
            "- [ ] freelance receipts (spread across three folders, really need to fix that)\n"
            "- [ ] mortgage overview\n"
            "- [x] savings account statement as of December 31st\n\n"
            "## Questions for the accountant\n\n"
            "1. Does the new laptop still count as a deduction this year or only next year\n"
            "2. What to do with the bit of freelance work from last year, separate or just include it\n\n"
            "Don't want to leave it too long, last year it turned into a last-minute "
            "scramble to get everything in on time."
        ),
        "deadline_days": 6,
        "group": "Finance",
    },
]


def days_ago(n):
    return now() - timedelta(days=n)


def days_from_now(n):
    return now() + timedelta(days=n)


def seed_notes(rng):
    for title, content in NOTE_SEEDS:
        created = days_ago(rng.randint(0, 30))
        group_name = rng.choice(NOTE_GROUPS) if rng.random() < 0.35 else None
        archived = rng.random() < 0.1
        deleted = not archived and rng.random() < 0.08

        db.session.add(
            Note(
                title=title,
                content=content,
                created_at=created,
                updated_at=created,
                group_name=group_name,
                archived_at=created if archived else None,
                deleted_at=now() if deleted else None,
            )
        )


def seed_sticky_notes(rng):
    for seed in STICKY_SEEDS:
        expires_days = seed.get("expires_days")

        db.session.add(
            StickyNote(
                title=seed.get("title"),
                content=seed.get("content"),
                colour=seed["colour"],
                pinned=seed.get("pinned", False),
                expires_at=days_from_now(expires_days)
                if expires_days is not None
                else None,
                created_at=days_ago(rng.randint(0, 20)),
                deleted_at=now() if seed.get("deleted") else None,
            )
        )


def seed_todos(rng):
    for seed in TODO_SEEDS:
        created = days_ago(rng.randint(0, 20))
        state = seed["state"]
        deadline_days = seed.get("deadline_days")

        archived_at = created if state == "done" or seed.get("archived") else None

        db.session.add(
            Todo(
                title=seed["title"],
                content=seed["content"],
                state=state,
                group_name=seed.get("group"),
                deadline=days_from_now(deadline_days)
                if deadline_days is not None
                else None,
                created_at=created,
                updated_at=created,
                completed_at=created if state == "done" else None,
                active_at=created if state == "active" else None,
                archived_at=archived_at,
                deleted_at=now() if seed.get("deleted") else None,
            )
        )


def reset_data():
    for model in (Note, StickyNote, Todo):
        model.query.delete()
    db.session.commit()


def seed(reset=False, seed_value=1):
    rng = random.Random(seed_value)

    with app.app_context():
        if reset:
            reset_data()

        seed_notes(rng)
        seed_sticky_notes(rng)
        seed_todos(rng)

        db.session.commit()

        print(
            f"Seeded {Note.query.count()} notes, "
            f"{StickyNote.query.count()} sticky notes, "
            f"{Todo.query.count()} todos."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    seed(reset=args.reset)
