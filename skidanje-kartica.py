import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance
# import urllib
import os, sys, io, datetime, multiprocessing, time, random, db_handler
from multiprocessing import Process, Lock, cpu_count, Semaphore, Queue

'''
**Monster** // ubaciti OCG/TCG oznaku za svaku kartu u bazu

- CARD TYPE <a title = "Card type">.find_parent(th).find_parent(tr).find_next_siblings()
	- Monster / Spell / Trap
	
- ATTRIBUTE <a title="Attribute">.find_parent(th).find_next_sibling(td).a.text.strip()
	!!! ima vise a, prvo je to, ali za svaki slucaj traziti po has_att(title)

- (secondary) TYPES <a title="Type">.find_parent(th).find_next_sibling(td).find_all(a).text.strip()

# PENDULUM LINK SYNCHRO XYZ TUNER # izbeci, naci sve posebne mehanike

	- FUSION
	# postoje Synchro Fusion karte, isfiltrirati prema Synchro u Materials

	- RITUAL

	- TOKEN
	# https://yugioh.fandom.com/wiki/Monster_Token

	- EFFECT
	# vrlo je bitno da li je cudoviste Effect ili ne zbog Fusion i ostalog


+ RANK ! # broj 0- <a title="Rank">.find_parent(th).find_next_sibling(td).a.text.strip()


- LEVEL / LINK ARROWS !
	- value <a title="Level"> ima 2 a, prvo je pravo / <a title="Link Arrow">.find_parent(th).find_next_sibling(td).find_all(a)
	!!! ima a tagova za neke slike, a.text.strip() == ''

+ PENDULUM SCALE !

- ATK (moze biti ?) / DEF (moze biti ?) / LINK ! <td><a title=...>
	- value <a title = "Link Rating">.find_parent(th).find_next_sibling(td).find_all(a)

+ LIMITATION TEXT (za tokene) <a title="Limitation text">.find_parent(th).find_next_sibling(td).text.strip()

+ SUMMONED... <a title="Summon">.find_parent(th).text.strip() (izvuci frazu iz th?) find_next_sibling(td).find_all(a)
	- U DB OSTAVITI NEKI PLACE HOLDER ZA ID KARTE

- PASSCODE <a title=Passcode>
# indeksirati karte u DB po ovome?

+ RITUAL SPELL CARD ! <a title="Ritual Spell Card">.find_parent(th).find_next_sibling(td).a.text.strip()

+ FUSION MATERIAL ! <a title="Fusion Material">.find_parent(th).find_next_sibling(td).find_all(a).text.strip()
	- u DB polje Fusion=true, requirement=[(1, psychic, ime cudovista).(...)]

+ MATERIALS ! <th>.text.strip() == Materials     find_next_sibling(td)
# isfiltrirati ovde Synchro, Tuner(s)
	value <td>.text.strip()

- CARD EFFECT TYPES ! <th>.text.strip()  // POPISATI SVE VRSTE EFEKATA, grupisati ih: Continuous, Ignition, Trigger (including Flip effects)[procuiti], Quick
# PENDULUM moze da ima dve potkategorije, find_all() pa dl[0] == ul[0]

	- Pendulum effect <dl><dt>.text.strip()
		value <ul><li><a>.text.strip()

	- Monster Effect <dl>
		value <ul><li><a>.text.strip()

- STATUSES <a title="Status">.find_parent(th).find_next_sibling(td).find_all(a)

- DESCRIPTION ENGLISH <table id="collapsibleTable0">.tbody.find_all(tr)[-1].td.text.strip()
	!!! svaki apostrof dobija \ pre sebe, vidljivo u stampanom tekstu
	!!! voditi racuna o formatiranju, neke imaju bulletpoints

Effects that depend on a monster's Level, such as "Gravity Bind",
"Burden of the Mighty", and "Roulette Barrel", have no effect 
on Xyz Monsters.

- NAPRAVITI VISE DB, JEDNU ZA FUSION, JEDNU ZA SYNCHRO ITD.
- EXTRA DECK SIDE DECK proveriti sta je to
- IZBECI SPELL/TRAP KOJE SE ODNOSE NA TURNER ITD.
- UNION MONSTER nije eksplicitno naznaceno, cudovista koja se kace na druga cudovista, u opisu pise Equip Card/equip
- Activation requirement, Cost, Effect - proci sve ove Card effect types i sortirati radi lakseg programiranja
 npr. cost = self.LP.deduce(1500) '''


def parse_pages(starting_url):
    lst = []
    lst.append(starting_url)
    req = requests.get(starting_url)
    soup = BeautifulSoup(req.content, "html.parser")
    next_page = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})["href"]
    lst.append(next_page)
    while True:
        print("List of pages: {}".format(lst))
        time.sleep(random.uniform(1, 4))
        try:
            req = requests.get(next_page)
            soup = BeautifulSoup(req.content, "html.parser")
            next_page = soup.find("a", {"class": "category-page__pagination-next wds-button wds-is-secondary"})["href"]
            lst.append(next_page)
        except Exception as e:
            print(e)
            print("No more pages with cards.")
            break
    return lst


def parse_card(directory, pathname, lock, queue, off_set_sleep):
    _current_process = multiprocessing.current_process()
    print("Starting : ", _current_process)

    log_directory = directory
    _pathname = pathname
    _sleep = off_set_sleep

    lock.acquire()
    try:
        db_conn, db_cursor = db_handler.open_connection(_pathname)
    except Exception as error:
        print("{}  |  Error while creating connection to DB : {}".format(_current_process, error))
        with open(f"{log_directory}/db_error.txt", "a") as log:
            log.write(
                "{}\n{}  |  Database error while opening : {}\n{}\n".format(_current_process,
                                                                            datetime.datetime.now().strftime(
                                                                                "%d/%m/%Y, %H:%M:%S"),
                                                                            queue, error))
            log.write("---------------------------------------------------------\n")
            log.flush()
    finally:
        lock.release()

    statuses = ["Legal", "Forbidden", "Limited", "Semi-Limited", "Unlimited", "Not legal",
                "Illegal", "Not yet legal", "Not yet released"]

    skip_monster_types = ["Synchro", "Turner", "Xyz", "Pendulum", "Link"]
    special_types = ["Fusion", "Ritual", "Token", "Efect"]

    base_link = "https://yugioh.fandom.com"
    illegal_characters = ['<', '>', '"', '*', '/', '\\', '?', '|', ':']

    for page in queue:
        time.sleep(random.uniform(1 + _sleep, 4))
        req = requests.get(page)
        print("{} got status code : {} for {}".format(_current_process, req.status_code, page))
        if req.status_code != 200:
            lock.acquire()
            with open(f"{log_directory}/request_denied_log.text", "a") as log:
                log.write("{}   |  {} got status code : {} for {}\n".format(datetime.datetime.now().strftime(
                    "%d/%m/%Y, %H:%M:%S"), _current_process, req.status_code, page))
                log.write("---------------------------------------------------------\n")
            lock.release()

        soup = BeautifulSoup(req.content, "html.parser")
        card_urls = soup.find_all("a", {"class": "category-page__member-link"})
        time.sleep(random.uniform(1 + _sleep, 2.7))

        for card_url in card_urls:
            card_url = card_url["href"]

            dct_statuses = {k: [] for k in statuses}

            # Variables for DB
            name = ""  # all
            card_type = ""  # all
            attribute = ""  # monster
            secondary_type = ""  # monster
            fusion_material = ""  # fusion
            materlias = ""  # fusion
            ritual_card = ""  # monster, contains link to card
            card_effect_types = ""  # all
            passcode = 0  # all, but not Tokens
            summoned_by = ""  # token
            level = ""  # monster, token, can be ?
            attack = ""  # monster, token, can be ?
            defense = ""  # monster, token, can be ?
            game_statuses = ""  # all
            description = ""  # all
            property_ = ""  # spell/trap
            card_image_relative_path = ""  # all

            TCG = 0  # all
            OCG = 0  # all
            TOKEN = 0
            EXTRA_DECK = 0  # token
            SIDE_DECK = 0  # token
            MAIN_DECK = 1  # all
            HAS_EFFECT = 0  # monster
            HAS_FLIP = 0  # monster
            IS_UNION = 0  # monster
            IS_TOON = 0  # monster
            IS_GEMINI = 0  # monster
            IS_SPIRIT = 0  # monster
            IS_FUSION = 0  # monster
            IS_RITUAL = 0  # monster + spell
            IS_TOKEN = 0  # token
            IS_MONSTER = 0
            IS_SPELL = 0
            SKIPABLE_CARD = 0  # monster

            time.sleep(random.uniform(2 + _sleep, 7))
            req1 = requests.get(base_link + card_url)
            soup = BeautifulSoup(req1.content, "html.parser")

            tcg_or_ocg = soup.find("div", {"class": "page-header__categories-links"}).text.strip()
            if "TCG" in tcg_or_ocg:
                TCG = 1
            if "OCG" in tcg_or_ocg:
                OCG = 1
            if "Tokne" in tcg_or_ocg:
                TOKEN = 1

            if TCG or OCG or TOKEN:
                # Name
                try:
                    name = soup.find("td",
                                     {"class": "cardtablerowdata"}).text.strip()  # mnoge stvari imaju \n na pocetku!
                    print("Name: ", name)

                    try:
                        # Card type: Monster, Spell, Trap
                        card_type = soup.find("a", {"title": "Card type"}).find_parent("th").find_next_sibling(
                            "td").a.text.strip()
                    except:
                        lock.acquire()
                        with open(f"{log_directory}/card_error_log.text", "a") as log:
                            log.write("{}   |  {} faild to obtain card type for : {}\n".format(
                                datetime.datetime.now().strftime(
                                    "%d/%m/%Y, %H:%M:%S"), _current_process, card_url))
                            log.write("-----------------------------------------------------------------\n")
                        lock.release()

                    if card_type == "Monster":
                        IS_MONSTER = 1
                        try:
                            # Attribute
                            attribute = soup.find("a", {"title": "Attribute"}).find_parent("th").find_next_sibling(
                                "td").a.text.strip()
                        except:
                            attribute = "?"

                        try:
                            # Secondery type
                            secondary_types = soup.find("a", {"title": "Type"}).find_parent("th").find_next_sibling(
                                "td").find_all(
                                "a")
                        except:
                            secondary_types = ["?"]

                        if len(secondary_types) < 2:
                            secondary_type = secondary_types[0].text.strip()
                        else:
                            secondary_type = [a.text.strip() for a in secondary_types]
                        # print(f"Secondery type(s): {secondary_type}")
                        for skip_type in skip_monster_types:
                            if skip_type in secondary_type:
                                SKIPABLE_CARD = 1
                                print("Skipable card found : {}".format(card_url))
                                lock.acquire()
                                with open(f"{log_directory}/skipped_card_log.txt", "a") as log:
                                    log.write(
                                        "{}\n{}  |  Skipped card : {}\n\t\t\tCard type(s) : {}\n".format(
                                            _current_process,
                                            datetime.datetime.now().strftime(
                                                "%d/%m/%Y, %H:%M:%S"),
                                            card_url,
                                            secondary_type))
                                    log.write("---------------------------------------------------------\n")
                                    log.flush()
                                lock.release()
                                break  # preskacemo Synchro itd.
                            else:
                                continue
                        else:  # not in skip_monster_types

                            if "Fusion" in secondary_type:  # posebna DB kako bih razvrstao sta sve moze, https://yugioh.fandom.com/wiki/List_of_Fusion_Monsters
                                # za neke fuzije je neophodno samo 5 cudovista istog podtipa, a to se ne vidi u karti, mora iz descriptiona
                                # ovde mozda ipak izvuci href i pribaviti passcode
                                IS_FUSION = 1
                                lock.acquire()
                                try:
                                    # Fusion Materials
                                    fusion_material = [a.text.strip() for a in
                                                       soup.find("a", {"title": "Fusion Material"}).find_parent(
                                                           "th").find_next_sibling("td").find_all("a")]
                                    # Materials
                                    materlias = soup.find("a", {"title": "Fusion Material"}).find_parent(
                                        "th").find_parent(
                                        "tr").find_next_sibling("tr").td.text.strip()


                                except Exception as e:  # nema fusion materials
                                    # Fusion Materials
                                    fusion_material = ""
                                    # Materials
                                    materlias = soup.find("a", {"title": "Passcode"}).find_parent("th").find_parent(
                                        "tr").find_next_sibling("tr").td.text.strip()

                                finally:
                                    lock.release()

                                try:
                                    card_effect_types = [a.text.strip() for a in
                                                         soup.find("a", {"title": "Passcode"}).find_parent(
                                                             "th").find_parent(
                                                             "tr").find_next_sibling("tr")]
                                    try:
                                        if card_effect_types.th.a.text == "Status":
                                            card_effect_types = ["?"]
                                        else:
                                            card_effect_types = [card_effect_types.td.find_all("a")]
                                    except:
                                        card_effect_types = [a.text.strip() for a in
                                                             soup.find("a", {"title": "Passcode"}).find_parent(
                                                                 "th").find_parent(
                                                                 "tr").find_next_sibling("tr").td.find_all("a")]
                                except:  # no passcode
                                    card_effect_types = ["?"]

                            elif "Ritual" in secondary_type:
                                # izvuci href i passcode?
                                IS_RITUAL = 1
                                lock.acquire()
                                try:
                                    # Ritual Spell Card
                                    ritual_card = soup.find("a", {"title": "Ritual Spell Card"}).find_parent(
                                        "th").find_next_sibling("td").a.text.strip()

                                except Exception as e:  # No ritual spell card, empty string

                                    with open(f"{log_directory}/ritual_log.txt", "a") as log:
                                        log.write("{}\n{}  |  Missing ritual card : {}\n".format(
                                            _current_process, datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                                            card_url))
                                        log.write("---------------------------------------------------------\n")
                                        log.flush()
                                finally:
                                    lock.release()

                                try:
                                    card_effect_types = [a.text.strip() for a in
                                                         soup.find("a", {"title": "Passcode"}).find_parent(
                                                             "th").find_parent(
                                                             "tr").find_next_sibling("tr")]
                                    try:
                                        if card_effect_types.th.a.text == "Status":
                                            card_effect_types = ["?"]
                                        else:
                                            card_effect_types = [card_effect_types.td.find_all("a")]
                                    except:
                                        card_effect_types = [a.text.strip() for a in
                                                             soup.find("a", {"title": "Passcode"}).find_parent(
                                                                 "th").find_parent(
                                                                 "tr").find_next_sibling("tr").td.find_all("a")]
                                except:  # no passcode
                                    card_effect_types = ["?"]

                            elif "Token" in secondary_type:
                                IS_TOKEN = 1
                                # Limitation text
                                limitation_text = ""

                                MAIN_DECK = 0
                                EXTRA_DECK = 1
                                SIDE_DECK = 1

                                try:
                                    # Attribute
                                    attribute = soup.find("a", {"title": "Attribute"}).find_parent(
                                        "th").find_next_sibling(
                                        "td").a.text.strip()
                                except:
                                    attribute = "?"

                                try:
                                    # Secondery type
                                    secondary_types = [
                                        soup.find("a", {"title": "Type"}).find_parent("th").find_next_sibling(
                                            "td").find_all("a")]

                                    if len(secondary_types) < 2:
                                        secondary_type = secondary_types[0].text.strip()
                                    else:
                                        secondary_type = [a.text.strip() for a in secondary_types]
                                except:
                                    secondary_types = ["?"]
                                # Summoned by
                                try:
                                    summoned_by = [a["href"] for a in
                                                   soup.find("a", {"title": "Summon"}).find_parent(
                                                       "th").find_next_sibling(
                                                       "td").find_all("a")]
                                except:
                                    summoned_by = "Any monster."

                                try:
                                    # Level
                                    level = soup.find("a", {"title": "Level"}).find_parent("th").find_next_sibling(
                                        "td").find(
                                        "a", {
                                            "title": True}).text.strip()
                                except:
                                    level = "?"

                                try:
                                    # ATK / DEF can be ?
                                    attack, defense = [a.text.strip() for a in
                                                       soup.find("a", {"title": "ATK"}).find_parent(
                                                           "th").find_next_sibling(
                                                           "td").find_all(
                                                           "a")]
                                except:
                                    attack, defense = ["?", "?"]

                                # po imenu sacuvati po naknadno spajati u bazi?
                                # for link in summoned_by:
                                # extra_req = requests.get("".join(base_link, link))
                                # extra_soup = BeautifulSoup(extra_req.text.strip(), "html.parser")
                                # parent_name = extra_soup.find("td", {"class":"cardtablerowdata"}).text.strip()
                                # parent_passcode = int(soup.find("a", {"title":"Passcode"}).find_parent("th").find_next_sibling("td").a.text.strip())

                                try:
                                    card_effect_types = [a.text.strip() for a in
                                                         soup.find("a", {"title": "Passcode"}).find_parent(
                                                             "th").find_parent(
                                                             "tr").find_next_sibling("tr")]
                                    try:
                                        if card_effect_types.th.a.text == "Status":
                                            card_effect_types = ["?"]
                                        else:
                                            card_effect_types = [card_effect_types.td.find_all("a")]
                                    except:
                                        card_effect_types = [a.text.strip() for a in
                                                             soup.find("a", {"title": "Passcode"}).find_parent(
                                                                 "th").find_parent(
                                                                 "tr").find_next_sibling("tr").td.find_all("a")]
                                except:  # no passcode
                                    card_effect_types = ["?"]
                            else:
                                try:
                                    # Passcode
                                    passcode = int(
                                        soup.find("a", {"title": "Passcode"}).find_parent("th").find_next_sibling(
                                            "td").a.text.strip())
                                except Exception as e:
                                    passcode = 0

                                # Card effect type, can be Null
                                try:
                                    card_effect_types = [a.text.strip() for a in
                                                         soup.find("a", {"title": "Passcode"}).find_parent(
                                                             "th").find_parent(
                                                             "tr").find_next_sibling("tr")]
                                    try:
                                        if card_effect_types.th.a.text == "Status":
                                            card_effect_types = ["?"]
                                        else:
                                            card_effect_types = [card_effect_types.td.find_all("a")]
                                    except:
                                        card_effect_types = [a.text.strip() for a in
                                                             soup.find("a", {"title": "Passcode"}).find_parent(
                                                                 "th").find_parent(
                                                                 "tr").find_next_sibling("tr").td.find_all("a")]
                                except:  # no passcode
                                    card_effect_types = ["?"]

                            if "Effect" in secondary_type:
                                HAS_EFFECT = 1

                            if "Union" in secondary_type:
                                IS_UNION = 1

                            if "Toon" in secondary_type:
                                IS_TOON = 1

                            if "Gemini" in secondary_type:
                                IS_GEMINI = 1

                            if "Flip" in card_effect_types:
                                HAS_FLIP = 1

                            if "Spirit" in secondary_type:
                                IS_SPIRIT = 1

                            try:
                                # Level
                                level = soup.find("a", {"title": "Level"}).find_parent("th").find_next_sibling(
                                    "td").find(
                                    "a", {
                                        "title": True}).text.strip()
                            except Exception as e:
                                level = "?"

                            try:
                                # ATK / DEF can be ?
                                attack, defense = [a.text.strip() for a in
                                                   soup.find("a", {"title": "ATK"}).find_parent("th").find_next_sibling(
                                                       "td").find_all(
                                                       "a")]
                            except Exception as e:
                                attack, defense = "?", "?"

                            # Status (mora ovako jer je svaki status zaseban tr)
                            for s in statuses:
                                res = soup.find_all("a", {"title": s})
                                if len(res):
                                    for r in res:
                                        q = r.find_parent("td", {"class": "cardtablerowdata"})
                                        if q:
                                            a = q.find_all("a")
                                            # print(a)
                                            if len(a):
                                                dct_statuses[a[0].text.strip()].append(
                                                    " ".join([b.text.strip() for b in a[1:]]))
                            # print(dct_statuses)

                            # Description
                            description = soup.find("td",
                                                    {
                                                        "class": "navbox-list"}).text.strip()  # ima \n i \', regulisati nekako

                    elif card_type == "Spell":
                        IS_SPELL = 1
                        # Property
                        try:
                            property_ = soup.find("a", {"title": "Property"}).find_parent("th").find_next_sibling(
                                "td").a.text.strip()  # Normal, Continuous, Equip, Quick-Play, Field, Ritual
                            if property_ == "Ritual":
                                IS_RITUAL = 1
                                IS_RITUAL = 1
                        except:
                            property_ = "Unknown"

                        try:
                            # Passcode
                            passcode = int(
                                soup.find("a", {"title": "Passcode"}).find_parent("th").find_next_sibling(
                                    "td").a.text.strip())
                        except:
                            passcode = 0

                        # Card effect type
                        try:
                            card_effect_types = [a.text.strip() for a in
                                                 soup.find("a", {"title": "Passcode"}).find_parent("th").find_parent(
                                                     "tr").find_next_sibling("tr").td.find_all("a")]
                        except:  # no passcode
                            card_effect_types = [a.text.strip() for a in
                                                 soup.find("a", {"title": "Property"}).find_parent("th").find_parent(
                                                     "tr").find_next_sibling("tr").td.find_all("a")]

                        # Status (mora ovako jer je svaki status zaseban tr)
                        for s in statuses:
                            res = soup.find_all("a", {"title": s})
                            if len(res):
                                for r in res:
                                    q = r.find_parent("td", {"class": "cardtablerowdata"})
                                    if q:
                                        a = q.find_all("a")
                                        # print(a)
                                        if len(a):
                                            dct_statuses[a[0].text.strip()].append(
                                                " ".join([b.text.strip() for b in a[1:]]))
                        # print(dct_statuses)
                        # Description
                        description = soup.find("td",{"class": "navbox-list"}).text.strip()  # ima \n i \', regulisati nekako
                    # Trap
                    else:
                        # Property
                        try:
                            property_ = soup.find("a", {"title": "Property"}).find_parent("th").find_next_sibling(
                                "td").a.text.strip()  # Normal, Continuous, Equip, Quick-Play, Field, Ritual
                        except:
                            property_ = "Unknown"

                        try:
                            # Passcode
                            passcode = int(
                                soup.find("a", {"title": "Passcode"}).find_parent("th").find_next_sibling(
                                    "td").a.text.strip())
                        except:
                            passcode = 0

                        # Card effect type
                        try:
                            card_effect_types = [a.text.strip() for a in
                                                 soup.find("a", {"title": "Passcode"}).find_parent("th").find_parent(
                                                     "tr").find_next_sibling("tr").td.find_all("a")]
                        except:  # if there is no passcode
                            card_effect_types = [a.text.strip() for a in
                                                 soup.find("a", {"title": "Property"}).find_parent("th").find_parent(
                                                     "tr").find_next_sibling("tr").td.find_all("a")]
                        # Status (mora ovako jer je svaki status zaseban tr)
                        for s in statuses:
                            res = soup.find_all("a", {"title": s})
                            if len(res):
                                for r in res:
                                    q = r.find_parent("td", {"class": "cardtablerowdata"})
                                    if q:
                                        a = q.find_all("a")
                                        # print(a)
                                        if len(a):
                                            dct_statuses[a[0].text.strip()].append(
                                                " ".join([b.text.strip() for b in a[1:]]))
                        # print(dct_statuses)
                        description = soup.find("td",
                                                {"class": "navbox-list"}).text.strip()  # ima \n i \', regulisati nekako
                    # Image
                    if SKIPABLE_CARD:
                        continue
                    else:
                        lock.acquire()
                        try:
                            try:
                                card_image_link = soup.find("a", {"class": "image image-thumbnail"}).img[
                                    "src"]  # radi konzistentnosti, sve su 300pix
                            except AttributeError:
                                card_image_link = soup.find("a", {"class": "image image-thumbnail"})["href"]
                            image = requests.get(card_image_link, stream=True)
                            im = Image.open(io.BytesIO(image.content))
                            im = im.convert('RGB')
                            # print('Input file size       : ', im.size )
                            # print('Input file name       : ', name )
                            # print('Input Image Size      : ', sys.getsizeof(image.content))
                            # print('')

                            enhancer = ImageEnhance.Sharpness(im)
                            factor = 1.8
                            en_im = enhancer.enhance(factor)

                            image_filename = name
                            for char in illegal_characters:
                                image_filename = image_filename.replace(char, "")
                            image_filename = image_filename.replace(' ', '_')

                            if card_type == "Monster":
                                if IS_FUSION:
                                    im_save_name = os.path.normpath(
                                        f"{_pathname}/Images/{card_type}/Fusion/{image_filename}.jpg")
                                elif IS_RITUAL:
                                    im_save_name = os.path.normpath(
                                        f"{_pathname}/Images/{card_type}/Ritual/{image_filename}.jpg")
                                else:
                                    im_save_name = os.path.normpath(
                                        f"{_pathname}/Images/{card_type}/{image_filename}.jpg")
                            else:  # Spell, Trap
                                im_save_name = os.path.normpath(
                                    f"{_pathname}/Images/{card_type}/{property_}/{image_filename}.jpg")
                            en_im.save(im_save_name)
                            # Image path for DB
                            card_image_relative_path = im_save_name.replace(_pathname, "")
                            print(_current_process, card_image_relative_path)

                            # print('Output file size       : ', en_im.size )
                            # print('Output file name       : ', im_save_name)
                            # print('Sharepned Image Size   : ', os.path.getsize (im_save_name))
                            # print('Sharpness level set to : ', factor)
                            # print('---------------------------------------------------\n')
                            with open(f"{log_directory}/card_image_size_log.txt", "a") as log:
                                log.write(
                                    "{}\n{}  |  Sharpening of card : {}\n".format(_current_process,
                                                                                  datetime.datetime.now().strftime(
                                                                                      "%d/%m/%Y, %H:%M:%S"),
                                                                                  card_url))
                                log.write("Original size : {}\n".format(sys.getsizeof((image.content))))
                                log.write("New size      : {}\n".format(os.path.getsize((im_save_name))))
                                log.write("---------------------------------------------------------\n")
                                log.flush()

                        # urllib.request.urlretrieve(card_image_link, "{}.jpg.".format(name.replace(" ", "_")) # manje function calls prema profiler-u
                        # with open("{}.jpg.".format(name.replace(" ", "_")),"wb") as pic:
                        #   pic.write(card_image.content)
                        except Exception as e:
                            print("Nema slike : ", e)
                            with open(f"{log_directory}/card_image_log.txt", "a") as log:
                                log.write(
                                    "{}\n{}  |  Missing card image : {}\n".format(_current_process,
                                                                                  datetime.datetime.now().strftime(
                                                                                      "%d/%m/%Y, %H:%M:%S"),
                                                                                  card_url))
                                log.write("---------------------------------------------------------\n")
                                log.flush()
                            card_image_relative_path = ""  # file path
                        finally:
                            lock.release()

                        print("{}  |  Inserting data into DB.".format(_current_process))

                        status = []
                        for k, v in dct_statuses.items():
                            if v:
                                status.append([k, v])
                        lock.acquire()
                        try:
                            status = ", ".join(k[0] + "(" + " ".join(k[1]) + ")" for k in status)
                        except:
                            with open(f"{log_directory}/card_status_log.txt", "a") as log:
                                log.write(
                                    "{}\n{}  |  Card status out of range : {}\n".format(_current_process,
                                                                                        datetime.datetime.now().strftime(
                                                                                            "%d/%m/%Y, %H:%M:%S"),
                                                                                        status))
                                log.write("---------------------------------------------------------\n")
                                log.flush()
                        finally:
                            lock.release()
                        # print("before",dct_statuses)
                        # print("list to del",status)
                        # print("after",dct_statuses)
                        lock.acquire()
                        try:
                            if IS_MONSTER:
                                if IS_FUSION:
                                    db_handler.insert_fusion_monster(db_conn, db_cursor, TCG, OCG, name, attribute,
                                                                     secondary_type,
                                                                     fusion_material, materlias, card_effect_types,
                                                                     passcode, level, attack, defense, status,
                                                                     description,
                                                                     card_image_relative_path)
                                elif IS_RITUAL:
                                    db_handler.insert_ritual_monster(db_conn, db_cursor, TCG, OCG, name, attribute,
                                                                     secondary_type,
                                                                     ritual_card, card_effect_types, passcode, level,
                                                                     attack, defense, status, description,
                                                                     card_image_relative_path)
                                elif IS_TOKEN:
                                    db_handler.insert_token(db_conn, db_cursor, TCG, OCG, name, attribute,
                                                            secondary_type,
                                                            card_effect_types, summoned_by, level, attack, defense,
                                                            description, card_image_relative_path)
                                else:
                                    db_handler.insert_monster(db_conn, db_cursor, TCG, OCG, name, attribute,
                                                              secondary_type,
                                                              card_effect_types, passcode, level, attack, defense,
                                                              status,
                                                              description, card_image_relative_path)
                            elif IS_SPELL:
                                if IS_RITUAL:
                                    db_handler.insert_spell_ritual(db_conn, db_cursor, TCG, OCG, name,
                                                                   card_effect_types, passcode, status, description,
                                                                   card_image_relative_path)
                                else:
                                    db_handler.insert_spell(db_conn, db_cursor, TCG, OCG, name,
                                                            card_effect_types, passcode, status, description, property_,
                                                            card_image_relative_path)
                            else:
                                db_handler.insert_trap(db_conn, db_cursor, TCG, OCG, name, card_effect_types,
                                                       passcode, status, description, property_,
                                                       card_image_relative_path)

                            # db_handler.insert(db_conn, db_cursor, card_type, TCG, OCG, name, attribute, secondary_type,
                            #                   IS_FUSION,
                            #                   fusion_material, materlias, IS_RITUAL,
                            #                   ritual_card, card_effect_types, passcode, summoned_by, HAS_EFFECT, IS_TOON,
                            #                   IS_GEMINI, IS_UNION, HAS_FLIP,
                            #                   IS_SPIRIT, level, attack, defense, status, description, property_,
                            #                   card_image_relative_path,
                            #                   IS_TOKEN)  # koristiti .filter() da izbacim prazna/None polja
                        except Exception as error:
                            with open(f"{log_directory}/db_error.txt", "a") as log:
                                log.write(
                                    "{}\n{}  |  Database error while inserting : {}\n{}\n".format(_current_process,
                                                                                                  datetime.datetime.now().strftime(
                                                                                                      "%d/%m/%Y, %H:%M:%S"),
                                                                                                  card_url, error))
                                log.write("---------------------------------------------------------\n")
                                log.flush()
                        finally:
                            lock.release()
                        print("Process finished : {}".format(_current_process))
                except:
                    lock.acquire()
                    with open(f"{log_directory}/card_error_log.text", "a") as log:
                        log.write(
                            "{}   |  {} Card could not be parsed for some reason : {}\n".format(
                                datetime.datetime.now().strftime(
                                    "%d/%m/%Y, %H:%M:%S"), _current_process, card_url))
                        log.write("-----------------------------------------------------------------\n")
                    lock.release()
            else:
                print(
                    "Process aborted : {}\nCard neither TCG nor OCG.".format(
                        _current_process))  # ukoliko karta nije OCG/TCG
    lock.acquire()
    try:
        db_handler.close_connection(db_conn, db_cursor)
    except Exception as error:
        with open(f"{log_directory}/db_error.txt", "a") as log:
            log.write(
                "{}\n{}  |  Database error while closing : {}\n{}\n".format(_current_process,
                                                                            datetime.datetime.now().strftime(
                                                                                "%d/%m/%Y, %H:%M:%S"),
                                                                            card_url, error))
            log.write("---------------------------------------------------------\n")
            log.flush()
    finally:
        lock.release()


if __name__ == "__main__":

    pathname = os.path.dirname(sys.argv[0])

    directories = ["/Images/Monster/Fusion", "/Images/Monster/Ritual", "/Images/Spell/Ritual",
                   "/Images/Spell/Field", "/Images/Spell/Equip", "/Images/Spell/Normal",
                   "/Images/Spell/Continuous", "/Images/Spell/Quick-Play",
                   "/Images/Trap/Normal", "/Images/Trap/Continuous", "/Images/Trap/Counter"]
    logginglog_directory = "/Log"

    for directory in directories:
        if not os.path.exists(pathname + directory):
            os.makedirs(os.path.normpath(pathname + directory))

    if not os.path.exists(pathname + logginglog_directory):
        os.makedirs(os.path.normpath(pathname + logginglog_directory))

    db_handler.create_tables(pathname)

    _starting_url = "https://yugioh.fandom.com/wiki/Category:OCG_cards"
    # tokens = "https://yugioh.fandom.com/wiki/Category:Tokens"  # posebno izuciti, u descriptio traziti tokene

    semaphore = Semaphore(value=2)
    lock = Lock()
    queue = []
    nr_of_processes = multiprocessing.cpu_count() * 2
    off_set_sleep = 0.5
    # queue = parse_pages(_starting_url)
    try:
        with open(pathname + "/links.txt", "r") as file:
            for line in file:
                queue.append(line.strip())
    except:
        pass
    print(queue)
    queue_len = len(queue)
    chunks = int(queue_len / nr_of_processes) + (queue_len % nr_of_processes > 0)  # to round up!
    queue_stacks = [queue[i:i + chunks] for i in range(0, queue_len, chunks)]
    # print(chunks)
    # print(len(queue_stacks))
    # for s in queue_stacks:
    #     print(s)

    for stack in queue_stacks:
        p = multiprocessing.Process(target=parse_card,
                                    args=(os.path.normpath(pathname + logginglog_directory),
                                          pathname, lock, stack, off_set_sleep))  # create txt logs inside directory
        # p.daemon = True
        p.start()
        off_set_sleep = off_set_sleep + 0.3

'''
    for link in spell + monster:
        queue.put(link)

    while not queue.empty():
        # pool = Pool(2)
        # result = pool.apply_async(parse_card, args=(queue.get(), os.path.normpath(pathname+process_directories[0]), pathname))
        # result.get(timeout=5)

        for i in range(2):
            p = multiprocessing.Process(target=parse_card,
                                        args=(os.path.normpath(pathname + logginglog_directory),
                                              pathname, semaphore, lock,
                                              queue))  # ,daemon=True)  # create txt logs inside directory
            p.daemon = True
            p.start()
'''
