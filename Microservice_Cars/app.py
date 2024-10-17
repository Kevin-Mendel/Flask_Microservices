from flask import Flask, jsonify, request, abort
from flask_pymongo import PyMongo

# Flask-Instanz erstellen
app = Flask(__name__)

# Verbindung zur MongoDB-Datenbank "cars" herstellen
app.config["MONGO_URI"] = "mongodb://cars_db:27017/cars"
# Variable definieren als Schnittstelle zur verbundenen MongoDB für Datenbankoperationen
mongo = PyMongo(app)

# Hilfsfunktion zum Generieren einer einzigartigen vehicle_id, welche bei jedem neuen Auto inkrementell um 1 erhöht wird
def generate_vehicle_id():
    # Zugriff auf die MongoDB Sammlung "counters" und sucht nach folgendem Dokument
    counter = mongo.db.counters.find_one_and_update(
        # Sucht das Dokument mit dem Feld "_id" mit dem Wert "vehicle_id_counter"
        {'_id': 'vehicle_id_counter'}, 
        # Erhöht den counter um 1
        {'$inc': {'seq': 1}}, 
        # Das aktualisierte Dokument wird zurückgegeben
        return_document=True, 
        # Sollte die Sammlung oder das Dokument in der MongoDB noch nicht existieren wird es erstellt
        upsert=True  
    )

    # Rückgabe der neuen vehicle_id, außer wenn das Dokument neu erstellt wurde, dann wird seq auf 1 initialisiert
    return counter['seq'] if counter['seq'] is not None else 1

# Funktion zum Finden eines Autos in der "cars" Sammlung der MongoDB über die "vehicle_id"
def find_car_by_id(vehicle_id):
    # Sucht das Auto mit der angegegben "vehicle_id" in der "Cars" Sammlung
    car = mongo.db.cars.find_one({'_id': int(vehicle_id)})
    # Wenn das Auto nicht gefunden wird, wird ein Fehler zurückgegeben
    if not car:
        abort(404, description="Car not found")
    # Gibt das gefunde Auto-Dokument zurück
    return car


# GET-Route ohne ID: Alle vorhanden Autos ausgeben oder Filterung durch Abfrageparameter
@app.route('/cars', methods=['GET'])
def get_cars():
    # Alle Abfrageparameter, die über die URL gesendet werden, werden in einem Dictionary gespeichert
    query_params = request.args.to_dict()
    # Das "query" Dictionary wird erstellt
    query = {}

    # For-Schleife, welche über die einzelen Abfrageparameter iteriert
    for key, value in query_params.items():
        try:
            # Falls ein Abfrageparameter numerisch ist, wird dieser in integer konvertiert
            value = int(value)
        # Falls der Abfrageparameter nicht konvertiert werden kann bzw. muss, wird der Error abgefangen
        except ValueError:
            pass
        # Der Abfrageparameter wird dem "query" Dictionary hinzugefügt (key = Parametername; value = Wert)
        query[key] = value

    # Sucht die "cars" Sammlung in der MongoDB und speichert alle Dokumente mit übereinstimmenden Attributen aus der Abfrage als Liste
    # Sind keine Abfrageparameter angegeben werden alle Dokumente der "cars" Sammlung als Liste gespeichert
    cars = list(mongo.db.cars.find(query))
    
    # Wenn kein Auto gefunden wird, wird ein Fehler zurückgegeben
    if not cars:
        abort(404, description="No cars found")

    # Rückgabe der in JSON umgewandelten Liste der gefundenen Autos
    return jsonify(list(cars)), 200


# GET-Route mit ID: Einzelnes Auto durch Angabe der vehicle_id ausgeben
@app.route('/cars/<vehicle_id>', methods=['GET'])
def get_car(vehicle_id):
    # Aufruf der Funktion zum Suchen des Autos über die angegebene "vehicle_id"
    return jsonify(find_car_by_id(vehicle_id)), 200


# POST-Route: Neues Auto hinzufügen
@app.route('/cars', methods=['POST'])
def add_car():
    # Liste der erforderlichen Felder beim Anlegen eines neuen Autos
    required_fields = ["brand", "model", "year", "price", "mileage", "color", "engine_type", "transmission_type"]
    
    # Es wird überprüft ob die Anfrage im JSON-Format vorliegt und ob alle erforderlichen Felder enthalten sind
    # Wenn eines der beiden Kriterien nicht erfüllt ist, wird ein Fehler zurückgegeben
    if not request.json or not all(k in request.json for k in required_fields):
        abort(400, description="Missing data")
    
    # Aufruf der Funktion zum Generieren einer eindeutigen "vehicle_id"
    vehicle_id = generate_vehicle_id()
    # Die vehicle_id wird der JSON-Anfrage hinzugefügt
    request.json['_id'] = vehicle_id

    # Das neue Auto wird in die "cars" Sammlung der MongoDB eingefügt
    mongo.db.cars.insert_one(request.json)

    # Das angelegte Auto wird im JSON-Format zurückgegeben
    return jsonify(request.json), 201


# PUT-Route: Auto aktualisieren
@app.route('/cars/<vehicle_id>', methods=['PUT'])
def update_car(vehicle_id):
    # Aufruf der Funktion zum Suchen des Autos über die angegebene "vehicle_id"
    find_car_by_id(vehicle_id)
    
    # Aktualisiert das Dokument mit der angegebenen "vehicle_id" in der "cars" Sammlung
    mongo.db.cars.update_one({'_id': int(vehicle_id)}, {'$set': request.json})

    # Sucht das aktualisierte Auto, um es als Antwort zurückzugeben
    updated_car = mongo.db.cars.find_one({'_id': int(vehicle_id)})

    # Das aktualisierte Auto wird im JSON-Format zurückgegeben
    return jsonify(updated_car), 200


# DELETE-Route: Auto löschen
@app.route('/cars/<vehicle_id>', methods=['DELETE'])
def delete_car(vehicle_id):
    # Aufruf der Funktion zum Suchen des Autos über die angegebene "vehicle_id"
    car = find_car_by_id(vehicle_id)

    # Löscht das Dokument mit der angegebenen "vehicle_id" aus der "cars" Sammlung
    mongo.db.cars.delete_one({'_id': int(vehicle_id)})

    # Das gelöschte Auto wird im JSON-Format zurückgegeben
    return jsonify(car), 200


# Flask App starten, die über alle IP-Adressen von außen erreichbar ist und sich im Debug-Modus befindet
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)