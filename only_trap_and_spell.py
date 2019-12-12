import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance
# import urllib
import os, sys, io, datetime, multiprocessing, time, random, db_handler
from multiprocessing import Process, Lock, cpu_count, Semaphore, Queue


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

            # Variables for DB
            name = ""  # all
            card_type = ""  # all
            ritual_card = ""  # monster, contains link to card
            card_effect_types = ""  # all
            passcode = 0  # all, but not Tokens
            description = ""  # all


            TCG = 0  # all
            OCG = 0  # all
            TOKEN = 0
            IS_MONSTER = 0
            IS_SPELL = 0
            IS_RITUAL = 0


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
                        continue
                    elif card_type == "Spell":
                        IS_SPELL = 1
                        # Property
                        try:
                            property_ = soup.find("a", {"title": "Property"}).find_parent("th").find_next_sibling(
                                "td").a.text.strip()  # Normal, Continuous, Equip, Quick-Play, Field, Ritual
                            if property_ == "Ritual":
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

                        # Description
                        description = soup.find("td",
                                                {"class": "navbox-list"}).text.strip()  # ima \n i \', regulisati nekako
                    # Trap
                    else:


                        try:
                            # Passcode
                            passcode = int(
                                soup.find("a", {"title": "Passcode"}).find_parent("th").find_next_sibling(
                                    "td").a.text.strip())
                        except:
                            passcode = 0

                        # Description
                        description = soup.find("td",
                                                {"class": "navbox-list"}).text.strip()  # ima \n i \', regulisati nekako
                    try:
                        if IS_MONSTER:
                            continue
                        elif IS_SPELL:
                            if IS_RITUAL:
                                db_handler.edit_spell_trap(db_conn, db_cursor, "spell_ritual", name, passcode, description)
                            else:
                                db_handler.edit_spell_trap(db_conn, db_cursor, "spell_card", name, passcode, description)
                        else:
                            db_handler.edit_spell_trap(db_conn, db_cursor, "trap_card", name, passcode, description)

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

    semaphore = Semaphore(value=2)
    lock = Lock()
    queue = []
    nr_of_processes = multiprocessing.cpu_count() * 2
    off_set_sleep = 0.5

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


    for stack in queue_stacks:
        p = multiprocessing.Process(target=parse_card,
                                    args=(os.path.normpath(pathname + logginglog_directory),
                                          pathname, lock, stack, off_set_sleep))
        p.start()
        off_set_sleep = off_set_sleep + 0.3