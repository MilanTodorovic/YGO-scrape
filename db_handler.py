import sqlite3, sys, os


def create_tables(pathname):
    try:
        print(pathname)
        with sqlite3.connect(pathname + "/card_list.sqlite") as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS monsters
                         (passcode INT, tcg INT, ocg INT, name TEXT, attribute TEXT, secondary_type TEXT, 
                         attack TEXT, defense TEXT, card_effect_types TEXT, level TEXT, description TEXT, statuses TEXT, 
                         image_link TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS monsters_fusion
                         (passcode INT, tcg INT, ocg INT, name TEXT, attribute TEXT, secondary_type TEXT, 
                         attack TEXT, defense TEXT, card_effect_types TEXT, level TEXT, description TEXT, statuses TEXT,
                          image_link TEXT, fusion_material TEXT, materials TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS monsters_ritual
                         (passcode INT, tcg INT, ocg INT, name TEXT, attribute TEXT, secondary_type TEXT, 
                         attack TEXT, defense TEXT, card_effect_types TEXT, level TEXT, description TEXT, statuses TEXT,
                          image_link TEXT, ritual_spell_card TEXT)''')

            # c.execute('''CREATE TABLE IF NOT EXISTS monsters_xyz
            #                 (passcode INT PRIMARY KEY)''')
            # c.execute('''CREATE TABLE IF NOT EXISTS monsters_synchro
            #                 (passcode INT PRIMARY KEY)''')
            # c.execute('''CREATE TABLE IF NOT EXISTS monsters_turner
            #                  (passcode INT PRIMARY KEY)''')
            # c.execute('''CREATE TABLE IF NOT EXISTS monsters_link
            #                  (passcode INT PRIMARY KEY)''')
            # c.execute('''CREATE TABLE IF NOT EXISTS monsters_pendulum
            #             (passcode INT PRIMARY KEY)''')

            c.execute('''CREATE TABLE IF NOT EXISTS spell_card
                         (passcode INT, tcg INT, ocg INT, name TEXT, card_effect_types TEXT, description TEXT, 
                         statuses TEXT, property TEXT, image_link TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS spell_ritual
                         (passcode INT, tcg INT, ocg INT, name TEXT, card_effect_types TEXT, description TEXT, 
                         statuses TEXT, image_link TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS trap_card
                         (passcode INT, tcg INT, ocg INT, name TEXT, card_effect_types TEXT, description TEXT, 
                         statuses TEXT, property TEXT, image_link TEXT)''')

            c.execute('''CREATE TABLE IF NOT EXISTS token
                         (tcg INT, ocg INT, name TEXT, attribute TEXT, summoned_by TEXT, secondary_type TEXT, 
                         attack TEXT, defense TEXT, card_effect_types TEXT, level TEXT, description TEXT, image_link TEXT)''')
            conn.commit()
            c.close()
    except Exception as e:
        print(e)


def open_connection(pathname):
    conn = sqlite3.connect(pathname + "/card_list.sqlite")
    c = conn.cursor()
    return [conn, c]


def close_connection(conn, c):
    c.close()
    conn.close()


def insert_monster(conn, cursor, TCG, OCG, name, attribute, secondary_type,
                   card_effect_types, passcode, level, attack, defense, status, description,
                   card_image_relative_path):
    if secondary_type:
        if len(secondary_type) >= 2:
            secondary_type = ", ".join(t for t in secondary_type)
        else:
            secondary_type = secondary_type[0]
    else:
        pass

    if len(card_effect_types) >= 2:
        card_effect_types = ", ".join(t for t in card_effect_types)
    else:
        card_effect_types = card_effect_types[0]

    cursor.execute('''INSERT INTO monsters VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (passcode, TCG, OCG, name, attribute, secondary_type, attack, defense, card_effect_types,
                    level, description, status, card_image_relative_path))
    conn.commit()


def insert_fusion_monster(conn, cursor, TCG, OCG, name, attribute, secondary_type, fusion_material, materlias,
                          card_effect_types, passcode,
                          level, attack, defense, status, description, card_image_relative_path):
    try:
        if fusion_material:
            _fusion_material = ", ".join(m for m in fusion_material)
        else:
            _fusion_material = ""
    except Exception as e:
        _fusion_material = ""
        print("---------------------------------------------\nfusion_kmaterial\n", e,
              "---------------------------------------------------\n")

    try:
        if secondary_type:
            if len(secondary_type) >= 2:
                secondary_type = ", ".join(t for t in secondary_type)
            else:
                secondary_type = secondary_type[0]
        else:
            secondary_type = ""
    except Exception as e:
        secondary_type = ""
        print("---------------------------------------------\nsecondary_type\n", e,
              "---------------------------------------------------\n")

    try: # ovo je problem########################################################
        if len(card_effect_types) >= 2:
            card_effect_types = ", ".join(t for t in card_effect_types)
        else:
            card_effect_types = card_effect_types[0]
    except Exception as e:
        print("---------------------------------------------\ncard_effect_type\n", e,
              "\n---------------------------------------------------\n")
        card_effect_types = ""

    cursor.execute('''INSERT INTO monsters_fusion VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (passcode, TCG, OCG, name, attribute, secondary_type, attack, defense, card_effect_types,
                    level, description, status, card_image_relative_path, _fusion_material, materlias))
    conn.commit()


def insert_ritual_monster(conn, cursor, TCG, OCG, name, attribute, secondary_type,
                          ritual_card, card_effect_types, passcode, level, attack, defense, status, description,
                          card_image_relative_path):
    if secondary_type:
        if len(secondary_type) >= 2:
            secondary_type = ", ".join(t for t in secondary_type)
        else:
            secondary_type = secondary_type[0]
    else:
        pass

    if len(card_effect_types) >= 2:
        card_effect_types = ", ".join(t for t in card_effect_types)
    else:
        card_effect_types = card_effect_types[0]

    cursor.execute('''INSERT INTO monsters_ritual VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (passcode, TCG, OCG, name, attribute, secondary_type, attack, defense, card_effect_types,
                    level, description, status, card_image_relative_path, ritual_card))
    conn.commit()


def insert_token(conn, cursor, TCG, OCG, name, attribute, secondary_type, card_effect_types, summoned_by, level, attack,
                 defense, description, card_image_relative_path):
    if secondary_type:
        if len(secondary_type) >= 2:
            secondary_type = ", ".join(t for t in secondary_type)
        else:
            secondary_type = secondary_type[0]
    else:
        pass

    if len(summoned_by) > 1:
        _summoned_by = ", ".join(s for s in summoned_by)
    else:
        _summoned_by = summoned_by[0]

    cursor.execute('''INSERT INTO token VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                   (TCG, OCG, name, attribute, _summoned_by, secondary_type, attack, defense, card_effect_types,
                    level, description, card_image_relative_path))
    conn.commit()


def insert_spell(conn, cursor, TCG, OCG, name, card_effect_types, passcode, status, description, property_,
                 card_image_relative_path
                 ):
    if len(card_effect_types) >= 2:
        card_effect_types = ", ".join(t for t in card_effect_types)
    else:
        card_effect_types = card_effect_types[0]

    cursor.execute('''INSERT INTO spell_card VALUES(?,?,?,?,?,?,?,?,?)''',
                   (passcode, TCG, OCG, name, card_effect_types, description, status, property_,
                    card_image_relative_path))
    conn.commit()


def insert_spell_ritual(conn, cursor, TCG, OCG, name, card_effect_types, passcode, status, description,
                        card_image_relative_path):
    if len(card_effect_types) >= 2:
        card_effect_types = ", ".join(t for t in card_effect_types)
    else:
        card_effect_types = card_effect_types[0]

    cursor.execute('''INSERT INTO spell_ritual VALUES(?,?,?,?,?,?,?,?)''',
                   (passcode, TCG, OCG, name, card_effect_types, description, status,
                    card_image_relative_path))
    conn.commit()


def insert_trap(conn, cursor, TCG, OCG, name, card_effect_types, passcode, status, description, property_,
                card_image_relative_path):
    if len(card_effect_types) >= 2:
        card_effect_types = ", ".join(t for t in card_effect_types)
    else:
        card_effect_types = card_effect_types[0]

    cursor.execute('''INSERT INTO trap_card VALUES(?,?,?,?,?,?,?,?,?)''',
                   (passcode, TCG, OCG, name, card_effect_types, description, status, property_,
                    card_image_relative_path))
    conn.commit()

def edit_spell_trap(conn, cursor, table, passcode, name, descritpion):
    cursor. execute("UPDATE ? SET description = ? WHERE passcode=? AND name=?", (table, descritpion, passcode, name))
    conn.commit()


if __name__ == "__main__":
    pathname = os.path.dirname(sys.argv[0])
    create_tables(pathname)
