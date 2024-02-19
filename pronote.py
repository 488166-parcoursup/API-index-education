import datetime
import json

import pronotepy
from pronotepy.ent import ile_de_france


def moyenne(tab: list) -> float:
    """
        Argument :
            tab : liste de valeurs entières ou flottantes.

        Renvoie : moyenne des valeurs de la liste

        Description :
            Calcule la moyenne (non pondérée) d'une liste de valeurs.
    """
    assert isinstance(tab, list) and tab != [], 'Le tableau doit être sous forme de liste !'
    for z in range(len(tab)):
        assert isinstance(z, int) or isinstance(z,
                                                float), 'Le tableau doit contenir des entiers ou flottants (ex. 1 ou 1.5)'
    moy = 0
    for i in range(len(tab)):
        moy += tab[i]

    return moy / len(tab)


def pronote():
    # Initialisation du client Pronote
    client = pronotepy.Client('https://[insérer numéro de l\'établissement].index-education.net/pronote/eleve.html',
                              username='',
                              password='',
                              ent=ile_de_france)

    if client.logged_in:
        nom_utilisateur = client.info.name
        print(f'Logged in as {nom_utilisateur}')

        periods = client.periods

        data = {
            "pronote": {
                "username": nom_utilisateur,
                "notes": {},
                "devoirs": {},
                "moyennes": {
                    "générale": {
                        "moy_gen": ""
                    },
                    "matières": {}
                }
            }
        }

        notes_list = {"note": [], "coef": []}

        dico_matiere = {
            "NUMERIQUE SC.INFORM.": "NSI",
            "NUMERIQUE SC.INFORM. > NUMERIQUE SC.INFORM.": "NSI",
            "ALLEMAND LV2": "Allemand",
            "ANGLAIS LV1": "Anglais",
            "HISTOIRE-GEOGRAPHIE": "Histoire-Géo",
            "ENSEIGN.SCIENTIFIQUE > SVT": "ES",
            "ENSEIGN.SCIENTIFIQUE > PHYS. CHIMIE": "ES",
            "ENSEIGN.SCIENTIFIQUE": "ES",
            'PHYSIQUE - CHIMIE': "Spé Physique",
            'PHYSIQUE-CHIMIE': "Spé Physique",
            "PHILOSOPHIE": "Philosophie",
            "ENS. MORAL & CIVIQUE": "EMC",
            "ED.PHYSIQUE & SPORT.": "EPS"
        }

        averages_list_detail = []
        averages_list = []
        for period in periods:
            for average in period.averages:
                if average is not []:
                    if average.student != 'Inapte' and average.student != "Absent":
                        if "," in average.student:
                            average.student = average.student.replace(",", '.')
                        averages_list.append(float(average.student))
                    averages_list_detail.append([average.student, dico_matiere[average.subject.name]])

                    if dico_matiere[average.subject.name] not in data["pronote"]["moyennes"]["matières"]:
                        data["pronote"]["moyennes"]['matières'][dico_matiere[average.subject.name]] = []

                    data["pronote"]["moyennes"]['matières'][dico_matiere[average.subject.name]].append(
                        {"moyenne": f"{average.student}", "moyenne_classe": f"{average.class_average}",
                         "moyenne_min": f"{average.min}", "moyenne_max": f"{average.max}"})

            for grade in period.grades:
                note = grade.grade
                class_average = grade.average
                out_of = grade.out_of
                if note != "Absent" and note != "Inapte" and note != "N.Note":
                    if out_of != 20:
                        if "," in note:
                            note = note.replace(",", '.')
                        note = (float(note) / int(out_of)) * 20
                        out_of = 20

                    if out_of != 20:
                        if "," in class_average:
                            note = note.replace(",", '.')
                        note = (float(note) / int(out_of)) * 20
                        out_of = 20

                coef = grade.coefficient
                matiere = dico_matiere[grade.subject.name]
                date = grade.date

                if matiere != "EPS":
                    if note != "Absent" and note != "Inapte" and note != "N.Note":
                        notes_list["note"].append(float(note))
                        notes_list["coef"].append(float(coef))
                    if matiere not in data["pronote"]["notes"]:
                        data["pronote"]["notes"][matiere] = []

                    data["pronote"]["notes"][matiere].append(
                        {"Date": f"{date}", "note": f"{note}", "out_of": f"{out_of}", "coefficient": coef,
                         "moyenne_classe": grade.average})

        today = datetime.date.today()
        homework = client.homework(today)

        for hw in homework:
            date_timestamp = str(hw.date.day) + "/" + str(hw.date.month) + '/' + str(
                hw.date.year)
            matiere = hw.subject.name
            hw_content = hw.description
            bg = hw.background_color
            done = hw.done

            if matiere != "ED.PHYSIQUE & SPORT.":
                if date_timestamp not in data["pronote"]["devoirs"]:
                    data["pronote"]["devoirs"][date_timestamp] = []

                # Ajout des données dans la structure
                data["pronote"]["devoirs"][date_timestamp].append(
                    {"matiere": dico_matiere[matiere], "hw_content": hw_content, "bg": bg, "done": done})

        moy_gen = str(round(moyenne(averages_list), 2))
        data['pronote']["moyennes"]["générale"]["moy_gen"] = moy_gen

        with open("pronote_data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    else:
        print("Failed to log in")
        exit()

pronote()