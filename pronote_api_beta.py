from flask import Flask, jsonify
import pronotepy
from pronotepy.ent import ile_de_france
import json
import datetime

app = Flask(__name__)

@app.route('/get_pronote_data', methods=['GET'])
def get_pronote_data():
    # Définition de la fonction pour calculer la moyenne pondérée
    def calculer_moyenne_ponderee(notes_avec_coef):
        somme_produits = 0
        somme_coef = 0
        coef_1_found = False  # Indique si au moins une note avec coef 1 a été trouvée

        for note_str, out_of_str, coef_str in notes_avec_coef:
            try:
                note = float(note_str)
                out_of = float(out_of_str)
                coef = float(coef_str)

                # Si le coefficient est inférieur à 1, ramener à 1
                if coef < 1:
                    coef = 1
                    coef_1_found = True

                somme_produits += (note / out_of) * coef
                somme_coef += coef
            except ValueError:
                print(f"Erreur de conversion pour les valeurs : {note_str}, {out_of_str}, {coef_str}")

        if somme_coef == 0:
            return 0
        else:
            # Si tous les coefficients étaient inférieurs à 1, la moyenne est sur 20
            if coef_1_found and somme_coef == len(notes_avec_coef):
                return (somme_produits / somme_coef) * 20
            else:
                return (somme_produits / somme_coef)

    # Initialisation du client Pronote
    client = pronotepy.Client('https://[etablissement].index-education.net/pronote/eleve.html',
                            username='',
                            password='',
                            ent=ile_de_france)

    if client.logged_in:
        nom_utilisateur = client.info.name
        print(f'Logged in as {nom_utilisateur}')

        notes_avec_coef = []  # Liste pour stocker les notes avec coef

        periods = client.periods
        for period in periods:
            for grade in period.grades:
                note = grade.grade
                out_of = grade.out_of
                coef = grade.coefficient
                matiere = grade.subject.name

                # Ajout des informations sur la note dans la liste
                notes_avec_coef.append([note, out_of, coef])

                print(f'{note}/{out_of} (coef {coef})')

        today = datetime.date.today()  # Utilisez le module datetime renommé ici
        homework = client.homework(today)

        for hw in homework:
            # Utiliser datetime.datetime pour obtenir le timestamp Unix
            date_timestamp = int(datetime.datetime(hw.date.year, hw.date.month, hw.date.day).timestamp())
            matiere = hw.subject.name
            hw_content = hw.description  # Intitulé du devoir

            print(f"({matiere}): {hw_content} (date timestamp: {date_timestamp})")

        # Création de la structure de données
        data = {
            "pronote": {
                "username": nom_utilisateur,
                "notes": {},
                "devoirs": {},
                "moyennes": {
                    "générale": {
                        "moy_gen": f"{calculer_moyenne_ponderee(notes_avec_coef)}/20"
                    }
                }
            }
        }

        # Remplissage des données des notes
        for period in periods:
            for grade in period.grades:
                note = grade.grade
                out_of = grade.out_of
                coef = grade.coefficient
                matiere = grade.subject.name

                # Création de la structure si elle n'existe pas encore
                if matiere not in data["pronote"]["notes"]:
                    data["pronote"]["notes"][matiere] = []

                # Ajout des données dans la structure
                data["pronote"]["notes"][matiere].append({"note": f"{note}/{out_of}", "coefficient": coef})

        # Remplissage des données des devoirs
        for hw in homework:
            date_timestamp = int(datetime.datetime(hw.date.year, hw.date.month, hw.date.day).timestamp())
            matiere = hw.subject.name
            hw_content = hw.description  # Intitulé du devoir

            # Création de la structure si elle n'existe pas encore
            if date_timestamp not in data["pronote"]["devoirs"]:
                data["pronote"]["devoirs"][date_timestamp] = []

            # Ajout des données dans la structure
            data["pronote"]["devoirs"][date_timestamp].append({"matiere": matiere, "hw_content": hw_content})

        # Écriture des données dans un fichier JSON
        with open("pronote_data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    else:
        print("Failed to log in")
        exit()
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
