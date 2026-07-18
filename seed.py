import argparse
import random
from datetime import timedelta

from app import app
from models import Note, StickyNote, Todo, db, now

NOTE_SEEDS = [
    ("Artikel A 2 Kieswet", "Er is een Kiesraad, gevestigd te 's-Gravenhage."),
    (
        "Artikel 1 Grondwet",
        "Allen die zich in Nederland bevinden, worden in gelijke gevallen gelijk behandeld. Discriminatie wegens godsdienst, levensovertuiging, politieke gezindheid, ras, geslacht, handicap, seksuele gerichtheid of op welke grond dan ook, is niet toegestaan.",
    ),
    (
        "Artikel 5:1 BW",
        "## Artikel 1\n\n1. Eigendom is het meest omvattende recht dat een persoon op een zaak kan hebben.\n2. Het staat de eigenaar met uitsluiting van een ieder vrij van de zaak gebruik te maken, mits dit gebruik niet strijdt met rechten van anderen en de op wettelijke voorschriften en regels van ongeschreven recht gegronde beperkingen daarbij in acht worden genomen.\n3. De eigenaar van de zaak wordt, behoudens rechten van anderen, eigenaar van de afgescheiden vruchten.",
    ),
    (
        "Artikel 6:162 BW",
        "## Artikel 162\n\n1. Hij die jegens een ander een onrechtmatige daad pleegt, welke hem kan worden toegerekend, is verplicht de schade die de ander dientengevolge lijdt, te vergoeden.\n2. Als onrechtmatige daad worden aangemerkt een inbreuk op een recht en een doen of nalaten in strijd met een wettelijke plicht of met hetgeen volgens ongeschreven recht in het maatschappelijk verkeer betaamt, een en ander behoudens de aanwezigheid van een rechtvaardigingsgrond.\n3. Een onrechtmatige daad kan aan de dader worden toegerekend, indien zij te wijten is aan zijn schuld of aan een oorzaak welke krachtens de wet of de in het verkeer geldende opvattingen voor zijn rekening komt.",
    ),
    (
        "Artikel 310 Sr",
        "Hij die enig goed dat geheel of ten dele aan een ander toebehoort wegneemt, met het oogmerk om het zich wederrechtelijk toe te eigenen, wordt, als schuldig aan *diefstal*, gestraft met gevangenisstraf van ten hoogste vier jaren of geldboete van de vierde categorie.",
    ),
    (
        None,
        "Het is een ieder verboden zich zodanig te gedragen dat gevaar op de weg wordt veroorzaakt of kan worden veroorzaakt of dat het verkeer op de weg wordt gehinderd of kan worden gehinderd.",
    ),
    ("Artikel 114 Grondwet", "De doodstraf kan niet worden opgelegd."),
    (
        "Artikel 7 Grondwet",
        "## Artikel 7\n\n1. Niemand heeft voorafgaand verlof nodig om door de drukpers gedachten of gevoelens te openbaren, behoudens ieders verantwoordelijkheid volgens de wet.\n2. De wet stelt regels omtrent radio en televisie. Er is geen voorafgaand toezicht op de inhoud van een radio- of televisieuitzending.\n3. Voor het openbaren van gedachten of gevoelens door andere dan in de voorgaande leden genoemde middelen heeft niemand voorafgaand verlof nodig wegens de inhoud daarvan, behoudens ieders verantwoordelijkheid volgens de wet. De wet kan het geven van vertoningen toegankelijk voor personen jonger dan zestien jaar regelen ter bescherming van de goede zeden.\n4. De voorgaande leden zijn niet van toepassing op het maken van handelsreclame.",
    ),
    (
        "Artikel 7:1 BW",
        "Koop is de overeenkomst waarbij de een zich verbindt een zaak te geven en de ander om daarvoor een prijs in geld te betalen.",
    ),
    (
        None,
        "## Artikel 3:1 BW\n\nGoederen zijn alle zaken en alle vermogensrechten.\n\n## Artikel 3:2 BW\n\nZaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.",
    ),
    (
        "Artikel 1:3 Awb",
        "1. Onder besluit wordt verstaan: een schriftelijke beslissing van een bestuursorgaan, inhoudende een publiekrechtelijke rechtshandeling.\n2. Onder beschikking wordt verstaan: een besluit dat niet van algemene strekking is, met inbegrip van de afwijzing van een aanvraag daarvan.\n3. Onder aanvraag wordt verstaan: een verzoek van een belanghebbende, een besluit te nemen.\n4. Onder beleidsregel wordt verstaan: een bij besluit vastgestelde algemene regel, niet zijnde een algemeen verbindend voorschrift, omtrent de afweging van belangen, de vaststelling van feiten of de uitleg van wettelijke voorschriften bij het gebruik van een bevoegdheid van een bestuursorgaan.",
    ),
    (
        "Artikel 1:30 BW",
        "Een huwelijk kan worden aangegaan door twee personen van verschillend of van gelijk geslacht.\n\nDe wet beschouwt het huwelijk alleen in zijn burgerlijke betrekkingen.",
    ),
    (
        None,
        "Hij die, zonder daartoe gerechtigd te zijn, zich op eens anders grond waarvan de toegang op een voor hem blijkbare wijze door de rechthebbende is verboden, bevindt of daar vee laat lopen, wordt gestraft met geldboete van de eerste categorie.",
    ),
    (
        None,
        "De militaire hospitaalschepen, waaronder te verstaan de schepen door de Staten gebouwd of ingericht in 't bijzonder en uitsluitend met het doel om hulp te verleenen aan de gewonden, zieken en schipbreukelingen, en waarvan de namen aan de oorlogvoerende Mogendheden moeten zijn medegedeeld bij den aanvang of in den loop der vijandelijkheden, in ieder geval vóór eenige ingebruikstelling, worden geëerbiedigd en kunnen gedurende de vijandelijkheden niet worden prijs gemaakt.",
    ),
    (
        "Artikel 23 Grondwet",
        "## Artikel 23\n\n1. Het onderwijs is een voorwerp van de aanhoudende zorg der regering.\n2. Het geven van onderwijs is vrij, behoudens het toezicht van de overheid en, voor wat bij de wet aangewezen vormen van onderwijs betreft, het onderzoek naar de bekwaamheid en de zedelijkheid van hen die onderwijs geven, een en ander bij de wet te regelen.\n3. Het openbaar onderwijs wordt, met eerbiediging van ieders godsdienst of levensovertuiging, bij de wet geregeld.\n4. In elke gemeente en in elk van de openbare lichamen, bedoeld in artikel 132a, wordt van overheidswege voldoend openbaar algemeen vormend lager onderwijs gegeven in een genoegzaam aantal openbare scholen. Volgens bij de wet te stellen regels kan afwijking van deze bepaling worden toegelaten, mits tot het ontvangen van zodanig onderwijs gelegenheid wordt gegeven, al dan niet in een openbare school.\n5. De eisen van deugdelijkheid, aan het geheel of ten dele uit de openbare kas te bekostigen onderwijs te stellen, worden bij de wet geregeld, met inachtneming, voor zover het bijzonder onderwijs betreft, van de vrijheid van richting.\n6. Deze eisen worden voor het algemeen vormend lager onderwijs zodanig geregeld, dat de deugdelijkheid van het geheel uit de openbare kas bekostigd bijzonder onderwijs en van het openbaar onderwijs even afdoende wordt gewaarborgd. Bij die regeling wordt met name de vrijheid van het bijzonder onderwijs betreffende de keuze der leermiddelen en de aanstelling der onderwijzers geëerbiedigd.\n7. Het bijzonder algemeen vormend lager onderwijs, dat aan de bij de wet te stellen voorwaarden voldoet, wordt naar dezelfde maatstaf als het openbaar onderwijs uit de openbare kas bekostigd. De wet stelt de voorwaarden vast, waarop voor het bijzonder algemeen vormend middelbaar en voorbereidend hoger onderwijs bijdragen uit de openbare kas worden verleend.\n8. De regering doet jaarlijks van de staat van het onderwijs verslag aan de Staten-Generaal.",
    ),
    (
        "Artikel 21 Grondwet",
        "De zorg van de overheid is gericht op de bewoonbaarheid van het land en de bescherming en verbetering van het leefmilieu.",
    ),
    (
        None,
        "In elke gemeente is een raad, een college en een burgemeester.\n\nDe raad vertegenwoordigt de gehele bevolking van de gemeente.",
    ),
    (
        "Artikel 300 Sr",
        "1. Mishandeling wordt gestraft met gevangenisstraf van ten hoogste drie jaren of geldboete van de vierde categorie.\n2. Indien het feit zwaar lichamelijk letsel ten gevolge heeft, wordt de schuldige gestraft met gevangenisstraf van ten hoogste vier jaren of geldboete van de vierde categorie.\n3. Indien het feit de dood ten gevolge heeft, wordt hij gestraft met gevangenisstraf van ten hoogste zes jaren of geldboete van de vierde categorie.\n4. Met mishandeling wordt gelijkgesteld opzettelijke benadeling van de gezondheid.\n5. Poging tot dit misdrijf is niet strafbaar.",
    ),
    (
        "Artikel 2 Grondwet",
        "1. De wet regelt wie Nederlander is.\n2. De wet regelt de toelating en de uitzetting van vreemdelingen.\n3. Uitlevering kan slechts geschieden krachtens verdrag. Verdere voorschriften omtrent uitlevering worden bij de wet gegeven.\n4. Ieder heeft het recht het land te verlaten, behoudens in de gevallen, bij de wet bepaald.",
    ),
    (
        None,
        "1. Geen feit is strafbaar dan uit kracht van een daaraan voorafgegane wettelijke strafbepaling.\n2. Bij verandering in de wetgeving na het tijdstip waarop het feit begaan is, worden de voor de verdachte gunstigste bepalingen toegepast.",
    ),
    (
        "Artikel 6:179 BW",
        "De bezitter van een dier is aansprakelijk voor de door het dier aangerichte schade, tenzij aansprakelijkheid op grond van de vorige afdeling zou hebben ontbroken indien hij de gedraging van het dier waardoor de schade werd toegebracht, in zijn macht zou hebben gehad.",
    ),
    (
        "Artikel 32 Grondwet",
        "Nadat de Koning de uitoefening van het koninklijk gezag heeft aangevangen, wordt hij zodra mogelijk beëdigd en ingehuldigd in de hoofdstad Amsterdam in een openbare verenigde vergadering van de Staten-Generaal. Hij zweert of belooft trouw aan de Grondwet en een getrouwe vervulling van zijn ambt. De wet stelt nadere regels vast.",
    ),
    (
        "Artikel 5:13 BW",
        "## Artikel 13\n\n1. Een schat komt voor gelijke delen toe aan degene die hem ontdekt, en aan de eigenaar van de onroerende of roerende zaak, waarin de schat wordt aangetroffen.\n2. Een schat is een zaak van waarde, die zolang verborgen is geweest dat daardoor de eigenaar niet meer kan worden opgespoord.\n3. De ontdekker is verplicht van zijn vondst aangifte te doen overeenkomstig artikel 5 lid 1 onder a. Indien geen aangifte is gedaan of onzeker is aan wie de zaak toekomt, kan de gemeente overeenkomstig artikel 5 lid 1 onder c vorderen dat deze aan haar in bewaring wordt gegeven, totdat vaststaat wie rechthebbende is.",
    ),
    (
        None,
        "Allen die zich in Nederland bevinden, zijn vrij en bevoegd tot het genot van de burgerlijke rechten.\n\nPersoonlijke dienstbaarheden, van welke aard of onder welke benaming ook, worden niet geduld.",
    ),
]

NOTE_GROUPS = ["Grondwet", "Strafrecht", "Privaatrecht"]

STICKY_SEEDS = [
    {"content": "De wet regelt wie Nederlander is.", "colour": "yellow"},
    {
        "content": "De doodstraf kan niet worden opgelegd.",
        "colour": "pink",
        "pinned": True,
    },
    {"content": "Goederen zijn alle zaken en alle vermogensrechten.", "colour": "orange"},
    {
        "content": "Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.",
        "colour": "green",
    },
    {
        "title": "Artikel 6 Gemeentewet",
        "content": "In elke gemeente is een raad, een college en een burgemeester.",
        "colour": "blue",
        "pinned": True,
    },
    {
        "content": "De raad vertegenwoordigt de gehele bevolking van de gemeente.",
        "colour": "yellow",
    },
    {
        "title": "Artikel 300 Sr",
        "content": "- [x] Mishandeling wordt gestraft met gevangenisstraf van ten hoogste drie jaren of geldboete van de vierde categorie.\n- [ ] Indien het feit zwaar lichamelijk letsel ten gevolge heeft, wordt de schuldige gestraft met gevangenisstraf van ten hoogste vier jaren of geldboete van de vierde categorie.\n- [ ] Met mishandeling wordt gelijkgesteld opzettelijke benadeling van de gezondheid.",
        "colour": "green",
    },
    {
        "content": "Er is een Kiesraad, gevestigd te 's-Gravenhage.",
        "colour": "pink",
        "expires_days": -3,
    },
    {
        "content": "De overheid treft maatregelen ter bevordering van de volksgezondheid.",
        "colour": "orange",
        "expires_days": 2,
    },
    {"content": "Poging tot dit misdrijf is niet strafbaar.", "colour": "green"},
    {
        "content": "Persoonlijke dienstbaarheden, van welke aard of onder welke benaming ook, worden niet geduld.",
        "colour": "blue",
    },
    {
        "title": "Artikel 7:1 BW",
        "colour": "purple",
        "expires_days": 5,
    },
    {
        "title": "Artikel 453 Sr",
        "colour": "purple",
        "pinned": True,
        "expires_days": -10,
    },
    {
        "content": "Hij die zich in kennelijke staat van dronkenschap op de openbare weg bevindt, wordt gestraft met hechtenis van ten hoogste twaalf dagen of geldboete van de eerste categorie.",
        "colour": "orange",
        "deleted": True,
    },
]


TODO_SEEDS = [
    {
        "title": "Hoofdstuk 1 Grondwet",
        "state": "open",
        "content": (
            "- [ ] Allen die zich in Nederland bevinden, worden in gelijke gevallen gelijk behandeld. Discriminatie wegens godsdienst, levensovertuiging, politieke gezindheid, ras, geslacht, handicap, seksuele gerichtheid of op welke grond dan ook, is niet toegestaan.\n"
            "- [ ] De wet regelt wie Nederlander is.\n"
            "- [ ] De zorg van de overheid is gericht op de bewoonbaarheid van het land en de bescherming en verbetering van het leefmilieu.\n"
            "- [ ] De overheid treft maatregelen ter bevordering van de volksgezondheid."
        ),
        "group": "Grondwet",
    },
    {
        "title": "Artikel 2 Grondwet",
        "state": "active",
        "content": (
            "- [x] De wet regelt wie Nederlander is.\n"
            "- [x] De wet regelt de toelating en de uitzetting van vreemdelingen.\n"
            "- [ ] Uitlevering kan slechts geschieden krachtens verdrag. Verdere voorschriften omtrent uitlevering worden bij de wet gegeven.\n"
            "- [ ] Ieder heeft het recht het land te verlaten, behoudens in de gevallen, bij de wet bepaald."
        ),
        "group": "Grondwet",
    },
    {
        "title": "Artikel 310 Sr",
        "state": "open",
        "content": "Hij die enig goed dat geheel of ten dele aan een ander toebehoort wegneemt, met het oogmerk om het zich wederrechtelijk toe te eigenen, wordt, als schuldig aan diefstal, gestraft met gevangenisstraf van ten hoogste vier jaren of geldboete van de vierde categorie.",
        "deadline_days": 3,
        "group": "Strafrecht",
    },
    {
        "title": "Artikel 32 Grondwet",
        "state": "active",
        "content": "Nadat de Koning de uitoefening van het koninklijk gezag heeft aangevangen, wordt hij zodra mogelijk beëdigd en ingehuldigd in de hoofdstad Amsterdam in een openbare verenigde vergadering van de Staten-Generaal. Hij zweert of belooft trouw aan de Grondwet en een getrouwe vervulling van zijn ambt. De wet stelt nadere regels vast.",
        "archived": True,
    },
    {
        "title": "Artikel 114 Grondwet",
        "state": "done",
        "content": "De doodstraf kan niet worden opgelegd.",
    },
    {
        "title": "Artikel 461 Sr",
        "state": "open",
        "content": "Hij die, zonder daartoe gerechtigd te zijn, zich op eens anders grond waarvan de toegang op een voor hem blijkbare wijze door de rechthebbende is verboden, bevindt of daar vee laat lopen, wordt gestraft met geldboete van de eerste categorie.",
        "deadline_days": -2,
    },
    {
        "title": "Artikel 7:1 BW",
        "state": "active",
        "content": "Koop is de overeenkomst waarbij de een zich verbindt een zaak te geven en de ander om daarvoor een prijs in geld te betalen.",
        "deadline_days": 1,
        "group": "Burgerlijk recht",
    },
    {
        "title": "Artikel 6:162 BW",
        "state": "open",
        "content": (
            "- [ ] Hij die jegens een ander een onrechtmatige daad pleegt, welke hem kan worden toegerekend, is verplicht de schade die de ander dientengevolge lijdt, te vergoeden.\n"
            "- [ ] Als onrechtmatige daad worden aangemerkt een inbreuk op een recht en een doen of nalaten in strijd met een wettelijke plicht of met hetgeen volgens ongeschreven recht in het maatschappelijk verkeer betaamt, een en ander behoudens de aanwezigheid van een rechtvaardigingsgrond.\n"
            "- [ ] Een onrechtmatige daad kan aan de dader worden toegerekend, indien zij te wijten is aan zijn schuld of aan een oorzaak welke krachtens de wet of de in het verkeer geldende opvattingen voor zijn rekening komt."
        ),
    },
    {
        "title": "Artikelen 3:1, 3:2 en 5:1 BW",
        "state": "done",
        "content": (
            "- [x] Goederen zijn alle zaken en alle vermogensrechten.\n"
            "- [x] Zaken zijn de voor menselijke beheersing vatbare stoffelijke objecten.\n"
            "- [x] Eigendom is het meest omvattende recht dat een persoon op een zaak kan hebben."
        ),
        "group": "Burgerlijk recht",
    },
    {
        "title": "Artikel 6 Gemeentewet",
        "state": "active",
        "content": "In elke gemeente is een raad, een college en een burgemeester.",
    },
    {"title": "Artikel A 2 Kieswet", "state": "done", "content": ""},
    {
        "title": "Artikel 453 Sr",
        "state": "cancelled",
        "content": "Vervallen per 01-07-2024.",
        "deleted": True,
    },
    {
        "title": "Artikel 430b Sr",
        "state": "cancelled",
        "content": "Hij die zich in kennelijke staat van dronkenschap op de openbare weg bevindt, wordt gestraft met hechtenis van ten hoogste twaalf dagen of geldboete van de eerste categorie.",
    },
    {
        "title": "Artikel 6:179 BW",
        "state": "done",
        "content": "De bezitter van een dier is aansprakelijk voor de door het dier aangerichte schade, tenzij aansprakelijkheid op grond van de vorige afdeling zou hebben ontbroken indien hij de gedraging van het dier waardoor de schade werd toegebracht, in zijn macht zou hebben gehad.",
    },
    {
        "title": "Artikel 1:30 BW",
        "state": "open",
        "content": "Een huwelijk kan worden aangegaan door twee personen van verschillend of van gelijk geslacht.\n\nDe wet beschouwt het huwelijk alleen in zijn burgerlijke betrekkingen.",
        "deadline_days": 0,
        "group": "Burgerlijk recht",
    },
    {
        "title": "Artikel 22 Grondwet",
        "state": "open",
        "content": "De overheid treft maatregelen ter bevordering van de volksgezondheid.\n\nBevordering van voldoende woongelegenheid is voorwerp van zorg der overheid.\n\nZij schept voorwaarden voor maatschappelijke en culturele ontplooiing en voor vrijetijdsbesteding.",
        "deadline_days": 20,
        "group": "Grondwet",
    },
    {
        "title": "Artikel 424 Sr",
        "state": "open",
        "content": "Hij die op of aan de openbare weg of op enige voor het publiek toegankelijke plaats tegen personen of goederen enige baldadigheid pleegt waardoor gevaar of nadeel kan worden teweeggebracht, wordt, als schuldig aan straatschenderij, gestraft met geldboete van de eerste categorie.",
        "deadline_days": 2,
        "group": "Strafrecht",
    },
    {
        "title": "Artikel 5:13 BW",
        "state": "open",
        "content": "Een schat komt voor gelijke delen toe aan degene die hem ontdekt, en aan de eigenaar van de onroerende of roerende zaak, waarin de schat wordt aangetroffen.\n\nEen schat is een zaak van waarde, die zolang verborgen is geweest dat daardoor de eigenaar niet meer kan worden opgespoord.",
        "deadline_days": 10,
        "group": "Burgerlijk recht",
    },
    {
        "title": "Artikelen 5:42 en 5:44 BW",
        "state": "open",
        "content": (
            "## Artikel 42\n\n"
            "1. Het is niet geoorloofd binnen de in lid 2 bepaalde afstand van de grenslijn van eens anders erf bomen, heesters of heggen te hebben, tenzij de eigenaar daartoe toestemming heeft gegeven of dat erf een openbare weg of een openbaar water is.\n"
            "2. De in lid 1 bedoelde afstand bedraagt voor bomen twee meter te rekenen vanaf het midden van de voet van de boom en voor de heesters en heggen een halve meter, tenzij ingevolge een verordening of een plaatselijke gewoonte een kleinere afstand is toegelaten.\n"
            "3. De nabuur kan zich niet verzetten tegen de aanwezigheid van bomen, heesters of heggen die niet hoger reiken dan de scheidsmuur tussen de erven.\n"
            "4. Ter zake van een volgens dit artikel ongeoorloofde toestand is slechts vergoeding verschuldigd van de schade, ontstaan na het tijdstip waartegen tot opheffing van die toestand is aangemaand.\n\n"
            "## Artikel 44\n\n"
            "1. Indien een nabuur wiens beplantingen over eens anders erf heenhangen, ondanks aanmaning van de eigenaar van dit erf, nalaat het overhangende te verwijderen, kan laatstgenoemde eigenaar eigenmachtig het overhangende wegsnijden en zich toeëigenen.\n"
            "2. Degene op wiens erf wortels van een ander erf doorschieten, mag deze voor zover ze doorgeschoten zijn weghakken en zich toeëigenen."
        ),
    },
    {
        "title": "Artikel 23 Grondwet",
        "state": "active",
        "content": (
            "## Artikel 23\n\n"
            "- [x] Het onderwijs is een voorwerp van de aanhoudende zorg der regering.\n"
            "- [x] Het geven van onderwijs is vrij, behoudens het toezicht van de overheid en, voor wat bij de wet aangewezen vormen van onderwijs betreft, het onderzoek naar de bekwaamheid en de zedelijkheid van hen die onderwijs geven, een en ander bij de wet te regelen.\n"
            "- [ ] Het openbaar onderwijs wordt, met eerbiediging van ieders godsdienst of levensovertuiging, bij de wet geregeld.\n"
            "- [ ] De regering doet jaarlijks van de staat van het onderwijs verslag aan de Staten-Generaal."
        ),
        "deadline_days": 6,
        "group": "Grondwet",
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
