from flask import Flask, jsonify, request, abort
from flask_pymongo import PyMongo

# Flask-Instanz erstellen
app = Flask(__name__)

# Verbindung zur MongoDB-Datenbank "employees" herstellen
app.config["MONGO_URI"] = "mongodb://employees_db:27017/employees"
# Variable definieren als Schnittstelle zur verbundenen MongoDB für Datenbankoperationen
mongo = PyMongo(app)

# Hilfsfunktion zum Generieren einer einzigartigen employee_id, welche bei jedem neuen Mitarbeiter inkrementell um 1 erhöht wird
def generate_employee_id():
    # Zugriff auf die MongoDB Sammlung "counters" und sucht nach folgendem Dokument
    counter = mongo.db.counters.find_one_and_update(
        # Sucht das Dokument mit dem Feld "_id" mit dem Wert "employee_id_counter"
        {'_id': 'employee_id_counter'}, 
        # Erhöht den counter um 1
        {'$inc': {'seq': 1}}, 
        # Das aktualisierte Dokument wird zurückgegeben
        return_document=True, 
        # Sollte die Sammlung oder das Dokument in der MongoDB noch nicht existieren wird es erstellt
        upsert=True  
    )

    # Rückgabe der neuen employee_id, außer wenn das Dokument neu erstellt wurde, dann wird seq auf 1 initialisiert
    return counter['seq'] if counter['seq'] is not None else 1

# Funktion zum Finden eines Mitarbeiters in der "employees" Sammlung der MongoDB über die "employee_id"
def find_employee_by_id(employee_id):
    # Sucht den Mitarbeiter mit der angegebenen "employee_id" in der "employees" Sammlung
    employee = mongo.db.employees.find_one({'_id': int(employee_id)})
    # Wenn der Mitarbeiter nicht gefunden wird, wird ein Fehler zurückgegeben
    if not employee:
        abort(404, description="Employee not found")
    # Gibt das gefundene Mitarbeiter-Dokument zurück
    return employee


# GET-Route ohne ID: Alle vorhandenen Mitarbeiter ausgeben
@app.route('/employees', methods=['GET'])
def get_employees():
    # Alle Abfrageparameter, die über die URL gesendet werden, werden in einem Dictionary gespeichert
    query_params = request.args.to_dict()
    # Das "query" Dictionary wird erstellt
    query = {}

    # For-Schleife, welche über die einzelnen Abfrageparameter iteriert
    for key, value in query_params.items():
        try:
            # Falls ein Abfrageparameter numerisch ist, wird dieser in integer konvertiert
            value = int(value)
        # Falls der Abfrageparameter nicht konvertiert werden kann, wird der Fehler abgefangen
        except ValueError:
            pass
        # Der Abfrageparameter wird dem "query" Dictionary hinzugefügt (key = Parametername; value = Wert)
        query[key] = value

    # Sucht die "employees" Sammlung in der MongoDB und speichert alle Dokumente mit übereinstimmenden Attributen aus der Abfrage als Liste
    # Sind keine Abfrageparameter angegeben, werden alle Dokumente der "employees" Sammlung als Liste gespeichert
    employees = list(mongo.db.employees.find(query))
    
    # Wenn kein Mitarbeiter gefunden wird, wird ein Fehler zurückgegeben
    if not employees:
        abort(404, description="No employees found")

    # Rückgabe der in JSON umgewandelten Liste der gefundenen Mitarbeiter
    return jsonify(list(employees)), 200


# GET-Route mit ID: Einzelnen Mitarbeiter durch Angabe der employee_id ausgeben
@app.route('/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    # Aufruf der Funktion zum Suchen des Mitarbeiters über die angegebene "employee_id"
    return jsonify(find_employee_by_id(employee_id)), 200


# POST-Route: Neuen Mitarbeiter hinzufügen
@app.route('/employees', methods=['POST'])
def add_employee():
    # Liste der erforderlichen Felder beim Anlegen eines neuen Mitarbeiters
    required_fields = ["name", "position", "salary", "hire_date", "address"]
    
    # Es wird überprüft, ob die Anfrage im JSON-Format vorliegt und ob alle erforderlichen Felder enthalten sind
    # Wenn eines der beiden Kriterien nicht erfüllt ist, wird ein Fehler zurückgegeben
    if not request.json or not all(k in request.json for k in required_fields):
        abort(400, description="Missing data")
    
    # Aufruf der Funktion zum Generieren einer eindeutigen "employee_id"
    employee_id = generate_employee_id()
    # Die employee_id wird der JSON-Anfrage hinzugefügt
    request.json['_id'] = employee_id

    # Der neue Mitarbeiter wird in die "employees" Sammlung der MongoDB eingefügt
    mongo.db.employees.insert_one(request.json)

    # Der angelegte Mitarbeiter wird im JSON-Format zurückgegeben
    return jsonify(request.json), 201


# PUT-Route: Mitarbeiter aktualisieren
@app.route('/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    # Aufruf der Funktion zum Suchen des Mitarbeiters über die angegebene "employee_id"
    find_employee_by_id(employee_id)
    
    # Aktualisiert das Dokument mit der angegebenen "employee_id" in der "employees" Sammlung
    mongo.db.employees.update_one({'_id': int(employee_id)}, {'$set': request.json})

    # Sucht den aktualisierten Mitarbeiter, um ihn als Antwort zurückzugeben
    updated_employee = mongo.db.employees.find_one({'_id': int(employee_id)})

    # Der aktualisierte Mitarbeiter wird im JSON-Format zurückgegeben
    return jsonify(updated_employee), 200


# DELETE-Route: Mitarbeiter löschen
@app.route('/employees/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    # Aufruf der Funktion zum Suchen des Mitarbeiters über die angegebene "employee_id"
    employee = find_employee_by_id(employee_id)

    # Löscht das Dokument mit der angegebenen "employee_id" aus der "employees" Sammlung
    mongo.db.employees.delete_one({'_id': int(employee_id)})

    # Der gelöschte Mitarbeiter wird im JSON-Format zurückgegeben
    return jsonify(employee), 200


# Flask App starten, die über alle IP-Adressen von außen erreichbar ist und sich im Debug-Modus befindet
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)