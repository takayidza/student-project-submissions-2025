import json
import jwt
import requests
from server import app, db
from flask import request, jsonify
from datetime import datetime, timedelta
from server.models.model import Responder, Incident, User, Vehicle, DeviceAssociation, EmergencyContact, Admin
from werkzeug.security import generate_password_hash, check_password_hash



def get_incident_address(lt, lo, google_map_key = None):

    if google_map_key is None:

        headers = {
            'User-Agent': 'YourAppName/1.0 (your_email@example.com)'
        }

        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lt}&lon={lo}"
        response = requests.get(url, headers = headers)
        data = response.json()
        print("ADDRESS DATA:",data)
        address = data['display_name']

        return address
    
    else:
        #else we use a google API key

        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lt},{lo}&key={google_map_key}"
        response = requests.get(url)
        data = response.json()
        address = data['results'][0]['formatted_address']

        return address



@app.route('/api/v1/users', methods=['GET'])
def get_users():
    users = User.query.all()
    response = []
    for user in users:
        user_data = {
            'user_id': user.user_id,
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'home_address': user.home_address,
            'city': user.city,
            'registration_date': user.registration_date.isoformat() if user.registration_date else None,
            'is_active': user.is_active,
        }
        response.append(user_data)
    return jsonify(response)


@app.route('/api/v1/users', methods=['POST'])
def create_user():
    data = request.json
    new_user = User(full_name=data['name'],
                    phone_number=data['phone'],
                    email=data['email'],
                    city=data['city'],
                    home_address=data['address']
                    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to add user to database'
                        }), 500
    return jsonify({
        'message': 'User added successfully',
        'status': True
    })

@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    response = {
        'user_id': user.user_id,
        'full_name': user.full_name,
        'phone_number': user.phone_number,
        'email': user.email,
        'home_address': user.home_address,
        'city': user.city,
        'registration_date': user.registration_date.isoformat() if user.registration_date else None,
        'is_active': user.is_active,
        'vehicles': [{
            'vehicle_id': v.vehicle_id,
            'registration_number': v.registration_number,
            'make': v.make,
            'model': v.model,
            'year': v.year,
            'color': v.color,
            'added_date': v.added_date.isoformat() if v.added_date else None
        } for v in user.vehicles],
        'emergency_contacts': [{
            'contact_id': ec.contact_id,
            'name': ec.name,
            'relationship': ec.relationship,
            'phone_number': ec.phone_number,
            'is_primary': ec.is_primary
        } for ec in user.emergency_contacts]
    }
    return jsonify(response)


@app.route('/api/v1/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    data = request.json
    user.full_name = data['full_name']
    user.phone_number = data['phone_number']
    user.email = data['email']

    try:
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to update user in database'
                        }), 500
    return jsonify({
        "message": "User updated successfully",
        "status": True
    }), 200

@app.route('/api/v1/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify(user.to_dict())  # Return the deleted user


@app.route('/api/v1/vehicles', methods=['GET'])
def get_vehicles():
    vehicles = Vehicle.query.all()
    response = []
    for vehicle in vehicles:
        vehicle_data = {
            'vehicle_id': vehicle.vehicle_id,
            'registration_number': vehicle.registration_number,
            'make': vehicle.make,
            'model': vehicle.model,
            'year': vehicle.year,
            'color': vehicle.color,
            'user_id': vehicle.user_id,
            'added_date': vehicle.added_date.isoformat() if vehicle.added_date else None,
            #'is_active': vehicle.is_active
        }
        response.append(vehicle_data)
    return jsonify(response)


@app.route('/api/v1/vehicles', methods=['POST'])
def create_vehicle():
    data = request.json
    new_vehicle = Vehicle(
                          registration_number=data['reg'],
                          make=data['make'], model=data['model'],
                          year=data['year'], color=data['colour'],
                          user_id=data['user_id'])
    try:
        db.session.add(new_vehicle)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to add vehicle to database'
                        }), 500
    return jsonify({
        'message': 'Vehicle added successfully',
        'status': True
    })   # Return the newly created vehicle

@app.route('/api/v1/vehicles/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    return jsonify(vehicle.to_dict())


@app.route('/api/v1/vehicles/<int:vehicle_id>', methods=['PUT'])
def update_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    data = request.json
    vehicle.registration_number = data['registration_number']
    vehicle.make = data['make']
    vehicle.model = data['model']
    vehicle.year = data['year']
    vehicle.color = data['color']

    try:
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to update vehicle in database'
                        }), 500
    return jsonify({
        'message': 'Vehicle updated successfully',
        'status': True
    }), 200


@app.route('/api/v1/vehicles/<int:vehicle_id>', methods=['DELETE'])
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({
        'message': 'Vehicle deleted successfully',
        'status': True,
    }), 200  # Return the deleted vehicle

@app.route('/api/v1/devices', methods = ['POST'])
def add_device():
    data = request.json
    device = DeviceAssociation(
        vehicle_id = data['vehicle_id'],
        device_serial = data['device_id'],
        is_active = data['is_active'],
    )
    try:
        db.session.add(device)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to add device to database'
                        }), 500
    return jsonify({'message': 'Device added successfully'}), 201

@app.route('/api/v1/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    device = DeviceAssociation.query.get(association_id=device_id)
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    data = request.json
    device.vehicle_id = data.get('vehicle_id', device.vehicle_id)
    device.device_serial = data.get('device_id', device.device_serial)
    device.is_active = data.get('is_active', device.is_active)

    try:
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                       'message': 'Failed to update device in database'
                       }), 500
    return jsonify({'message': 'Device updated successfully'}), 200


@app.route('/api/v1/devices', methods=['GET']) 
def get_devices():
    devices = DeviceAssociation.query.all()
    response = []
    for device in devices:
        device_data = {
            'device_id': device.association_id,
            'device_serial': device.device_serial,
            'vehicle_id': device.vehicle_id,
            'installation_date': device.installation_date.isoformat() if device.installation_date else None,
            'last_maintenance': device.last_maintenance.isoformat() if device.last_maintenance else None,
            'is_active': device.is_active
        }
        response.append(device_data)
    return jsonify(response)


@app.route('/api/v1/emergency_contacts', methods=['GET'])
def get_emergency_contacts():
    contacts = EmergencyContact.query.all()
    return jsonify([contact.to_dict() for contact in contacts])

@app.route('/api/v1/emergency_contacts', methods=['POST'])
def create_emergency_contact():
    data = request.json
    new_contact = EmergencyContact(user_id=data['user_id'],
                                   name=data['name'],
                                   relationship=data['relationship'],
                                   phone_number=data['phone_number'],
                                   is_primary=data['is_primary']
                                )
    try:
        db.session.add(new_contact)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to add emergency contact to database'
        }), 500
    return jsonify(new_contact.to_dict())   # Return the newly created emergency contact

@app.route('/api/v1/emergency_contacts/<int:contact_id>', methods=['GET'])
def get_emergency_contact(contact_id):
    contact = EmergencyContact.query.get(contact_id)
    return jsonify(contact.to_dict())

@app.route('/api/v1/emergency_contacts/<int:contact_id>', methods=['PUT'])
def update_emergency_contact(contact_id):
    contact = EmergencyContact.query.get(contact_id)
    data = request.json
    contact.name = data['name']
    contact.relationship = data['relationship']
    contact.phone_number = data['phone_number']
    contact.is_primary = data['is_primary']

    try:
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to update emergency contact in database'
                        }), 500
    return jsonify(contact.to_dict()), 200

@app.route('/api/v1/emergency_contacts/<int:contact_id>', methods=['DELETE'])
def delete_emergency_contact(contact_id):
    contact = EmergencyContact.query.get(contact_id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify(contact.to_dict())  # Return the deleted emergency contact


@app.route('/api/v1/incidents', methods=['GET'])
def get_incidents():
    incidentses = Incident.query.all()
    collection = []
    for incident in incidentses:
        collection.append({
            "device_id": incident.device_id,
            "vehicleId": incident.vehicle_id,
            "lat": float(incident.latitude),
            "lng": float(incident.longitude),
            "severity": incident.severity,
            "score": float(incident.score),
            "timestamp": incident.incident_time
        })

    return jsonify(collection)

@app.route('/api/v1/incidents', methods=['POST'])
def create_incident():
    data = request.get_json(force=True)
    #data = json.loads(data)
    print(data)
    print(type(data))
    responders = Responder.query.all()
    addresses = []
    geo_addresses = []
    new_incident = Incident(device_id=int(data['device_id']),
                            vehicle_id=int(data['vehicle_id']),
                            latitude=data['gps']['latitude'],
                            longitude=data['gps']['longitude'],
                            description="Incident",
                            severity=data['severity']['level'],
                            score=data['severity']['score']
                        )
    
    try:
        db.session.add(new_incident)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to report incident'
                        }), 500
    for responder in responders:
        addresses.append(responder.address)

    incident_address = get_incident_address(lt = -17.8395913, lo = 31.0104764)

    return jsonify({"message":"incident has been reported successfully", "address": incident_address}), 201   # Return the newly created incident



@app.route('/api/v1/incidents/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    incident = Incident.query.get(incident_id)
    return jsonify(incident.to_dict())

@app.route('/api/v1/incidents/<int:incident_id>', methods=['PUT'])
def update_incident(incident_id):
    incident = Incident.query.get(incident_id)
    data = request.json
    incident.vehicle_id = data['vehicle_id']
    incident.reported_by = data['reported_by']
    incident.location = data['location']
    incident.incident_date = data['incident_date']
    incident.description = data['description']

    try:
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to update incident in database'
                        }), 500
    
    return jsonify(incident.to_dict()), 200


@app.route('/api/v1/incidents/<int:incident_id>/attend', methods=['PUT'])
def attend_incident(incident_id):
    incident = Incident.query.get(incident_id)
    if incident:
        incident.status = 'attending'

        try:
            db.session.commit()
        except Exception as error:
            return jsonify({'error': str(error),
                            'message': 'Failed to update incident status in database'
                            }), 500
        return jsonify(incident.to_dict()), 200
    else:
        return jsonify({'error': 'Incident not found'}), 404


####################################################################################################
# Responder endpoints
####################################################################################################


@app.route('/api/v1/add/responder', methods=['POST'])
def add_respoder():
    data = request.json
    responder = Responder(
        name=data['serviceName'],           # Changed from 'name' to match form's v-model
        service_type=data['serviceType'],   # Changed from 'service_type' to match form's v-model
        incident_type=data['incidentType'], # Changed from 'incident_type' to match form's v-model
        contact_number=data['contactNumber'], # Changed from 'contact_number' to match form's v-model
        is_available=True,
        city=data['city'],                 # Matches form's v-model
        password=generate_password_hash(data['password']), # Matches form's v-model
        province=data['province'],         # Matches form's v-model
        address=data['address'],           # Matches form's v-model
        email=data['email']                # Matches form's v-model
    )
    
    try:
        db.session.add(responder)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to add responder to database',
                        'status': False
                        }), 500
    
    return jsonify({'message': 'Responder added successfully', 'status': True}), 201


@app.route("/api/v1/login", methods=['POST'])
def login():
    data = request.json
    responder = Responder.query.filter_by(email=data['email']).first()

    if responder and check_password_hash(responder.password, data['password']):

        token = jwt.encode({
                'responder_id': responder.responder_id,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, app.config['SECRET_KEY'])
            
        return jsonify({'token': token, 'status':True})
    else:
        return jsonify({'error': 'Invalid login credentials'}), 401





#########################################################################################
#   Admin endpoints
#########################################################################################

@app.route('/api/v1/admins/add', methods=['POST'])
def add_admin():
    data = request.json
    admin = Admin(
        firstname=data['firstname'],
        lastname=data['lastname'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        is_superuser=data['is_superuser']
    )
    
    try:
        db.session.add(admin)
        db.session.commit()
    except Exception as error:
        return jsonify({'error': str(error),
                        'message': 'Failed to add admin to database',
                        'status': False
                        }), 500
    
    return jsonify({'message': 'Admin added successfully', 'status': True}), 201


@app.route("/api/v1/admin/login", methods=['POST'])
def admin_login():
    data = request.json
    admin = Admin.query.filter_by(email=data['email']).first()

    if admin and check_password_hash(admin.password, data['password']):

        token = jwt.encode({
                'id': admin.id,
                'exp': datetime.utcnow() + timedelta(days=30)
            }, app.config['SECRET_KEY'])
            
        return jsonify({'token': token, 'status':True})
    else:
        return jsonify({'error': 'Invalid login credentials'}), 


@app.route('/api/v1/admins/device', methods=['GET'])
def admin_get_device():

    devices = DeviceAssociation.query.all()

@app.route('/api/v1/admins/add/device', methods = ['POST'])
def admin_add_device():

    pass
