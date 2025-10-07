# Kopiert Medientyp in Feld Inhaltstyp für alle Vereinbarungen, entsprechend vorgegebener Konkordanz
import requests
import json
import yaml

# Parameter
# Credentials und URLS aus YAML KonfigurationsDatei
with open("folio-acq_parameter.yaml") as stream:
	try:
		param = yaml.safe_load(stream)
	except yaml.YAMLError as exc:
		print(exc)
		exit(2)
		
# FOLIO system URLs

url_folio = param['folio']['url_sas']  # URL for FOLIO agreements API
url_token = param['folio']['url_login']  # URL for FOLIO login (authentication)
url_erm_refdata = param['folio']['url_erm_refdata'] #URL for FOLIO assignements Auswahllisten

#Handzuordnung Welcher Medientyp-Value wird zu welchem Inhaltstyp

inhaltstyp={}
inhaltstyp['datenbank'] = ["Datenbanken","database"]
inhaltstyp['datenbank_bibliographie'] = ["Datenbanken","database"]
inhaltstyp['datenbank_e-book'] = ["Datenbanken","database"]
inhaltstyp['datenbank_e-books'] = ["Datenbanken","database"]
inhaltstyp['datenbank_e-book_e-journal'] = ["Datenbanken","database"]
inhaltstyp['datenbank_e-books_e-journals'] = ["Datenbanken","database"]
inhaltstyp['datenbank_ebs'] = ["Datenbanken","database"]
inhaltstyp['datenbank_loseblatt'] = ["Datenbanken","database"]
inhaltstyp['datenbank_zeitungen'] = ["Datenbanken","database"]
inhaltstyp['datenbank_e-journal'] = ["Datenbanken","database"]
inhaltstyp['e-book_einzeln'] = ["E-Books","books"]
inhaltstyp['e-books_einzeln'] = ["E-Books","books"]
inhaltstyp['e-books'] = ["E-Books","books"]
inhaltstyp['e-book_paket'] = ["E-Books","books"]
inhaltstyp['e-book_eba_ebs'] = ["E-Books","books"]
inhaltstyp['e-book_eba/ebs'] = ["E-Books","books"]
inhaltstyp['e-journal_einzeln'] = ["E-Journals","journals"]
inhaltstyp['e-journal_paket'] = ["E-Journals","journals"]
inhaltstyp['e-journals'] = ["E-Journals","journals"]

# Credentials für FOLIO login
payload_token = json.dumps({
	"username": param['folio']['user'],
	"password": param['folio']['password']
})

# Headers für FOLIO login request
headers_token = {
	'x-okapi-tenant': param['folio']['mandant'],  # FOLIO tenant ID
	'Content-Type': 'application/json'
}
# Funktionen

def get_refdata(_list):
	"""
	Werte/UUID einer Auswahlliste ermitteln
	
	Parameter:
	_list: String, Description der Auswahlliste / über FOLIO-Einstellungen ermitteln
	
	Return:
	refdata: dict, Werte der Liste mit UUID
	
	"""
	parameters = {
		"perPage":"100" # muss erst einmal reichen
	}
	refdata = {}
	try:
		response = requests.get( url_erm_refdata, headers=headers_folio, params=parameters)
		response.raise_for_status()
		print(len(response.json()))
		for r in response.json():
			if r.get('desc') == _list:
				for v in r.get('values'):
					refdata[v.get('value')] = v.get('id')
		return refdata
	except requests.exceptions.HTTPError as http_err:
		# Gib eine Fehlermeldung zurück, falls die Anfrage fehlschlägt
		print(f"HTTP error occurred: {http_err}")
	except requests.exceptions.RequestException as req_err:
		# Gib eine Fehlermeldung zurück, falls ein anderer Fehler auftritt
		print(f"Error occurred: {req_err}")
	# Gib 0 zurück, falls ein Fehler aufgetreten ist
	return 0
#
def get_number_of_sas():
	"""
	Ermittelt die Anzahl der Vereinbarungen
	
	"""
	# Parameter für die GET-Anfrage
	parameters = {
		"sort":"name;asc",
		"stats":"true"
	}
	try:
		response = requests.get( url_folio, headers=headers_folio, params=parameters)
		response.raise_for_status()
		# Gesamtzahl der Datensätze
		return response.json().get('totalRecords', 0)
	except requests.exceptions.HTTPError as http_err:
		# Gib eine Fehlermeldung zurück, falls die Anfrage fehlschlägt
		print(f"HTTP error occurred: {http_err}")
	except requests.exceptions.RequestException as req_err:
		# Gib eine Fehlermeldung zurück, falls ein anderer Fehler auftritt
		print(f"Error occurred: {req_err}")
	# Gib 0 zurück, falls ein Fehler aufgetreten ist
	return 0

def get_id_medientyp_all_sas(_number):
	"""
	Auflistung aller Vereinbarungen
	muss in Gruppen von perPage erfolgen
	
	Parameter:
	_number: Int, Gesamtzahl Vereinbarungen

	Return:
	ids: Vereinbarungs -ID, -Name, -Medientyp Wert, -Inhaltstyp Wert
	
	"""
	# Parameter für die GET-Anfrage
	parameters = {
		"sort":"name;asc",
		"stats":"true",
		"perPage":"10"
	}
	page = 1
	ids = []
	try:
		for sas in range(0,_number ,10):
			
			parameters['page'] = str(page)
			response = requests.get( url_folio, headers=headers_folio, params=parameters)
			response.raise_for_status()
			results = response.json().get('results', [])
			for item in results:
				custom_properties = item.get('customProperties', {})
				agreement_content_types = item.get('agreementContentTypes', [])
				if 'Medientyp' in custom_properties:
					agree_id = item['id']
					agree_name = item['name']
					agree_value = custom_properties['Medientyp'][0]['value']['value']
					agree_inhaltstyp = agreement_content_types[0]['contentType']['value'] if agreement_content_types else ""
					ids.append({
						'id': agree_id,
						'name': agree_name,
						'value': agree_value,
						'inhalt': agree_inhaltstyp
					})
				else:
					print(f"Kein Medientyp: {item['id']} ** {item['name']}")
			page+= 1
	except requests.exceptions.HTTPError as http_err:
		# Gib eine Fehlermeldung zurück, falls die Anfrage fehlschlägt
		print(f"HTTP error occurred: {http_err}")
	except requests.exceptions.RequestException as req_err:
		# Gib eine Fehlermeldung zurück, falls ein anderer Fehler auftritt
		print(f"Error occurred: {req_err}")
	return ids

def update_inhaltstyp(_id,_payload):
	"""
	Update des Feldes Inhaltstyp der Assignment
	
	Parameter
	_id: assignment uuid
	_payload: JSON formatierte Anpassung
	
	"""
	try:
		response = requests.request("PUT", f"{url_folio}/{_id}", headers=headers_folio, data=_payload)
		response.raise_for_status()
		return response.status_code
	except requests.exceptions.HTTPError as http_err:
		print(f"HTTP error occurred: {http_err}")
	except requests.exceptions.RequestException as req_err:
		print(f"Error occurred: {req_err}")
		return None

def get_token(_url_token, _headers_token,_payload_token):
	"""
	Holt API-Token mit entsprechenden Credentials
	
	"""
	try:
		response = requests.request("POST", _url_token, headers=_headers_token, data=_payload_token)
		response.raise_for_status()
		return (response.json().get('okapiToken'))
	except requests.exceptions.HTTPError as http_err:
		# Gib eine Fehlermeldung zurück, falls die Anfrage fehlschlägt
		print(f"HTTP error occurred: {http_err}") 
	except requests.exceptions.RequestException as req_err:
		# Gib eine Fehlermeldung zurück, falls ein anderer Fehler auftritt
		print(f"Error occurred: {req_err}")
	except KeyError as key_err:
		# Gib eine Fehlermeldung zurück, falls das Token nicht im JSON-Objekt vorhanden ist
		print(f"Key error: {key_err}")
	# Gib None zurück, falls ein Fehler aufgetreten ist
	return None


## MAIN START

# Folio API Token holen
token  = get_token(url_token,headers_token,payload_token)
if token is None:
	print("Fehler beim Login")
	exit(1)

# Headers für FOLIO API requests
headers_folio = {
	'x-okapi-tenant': param['folio']['mandant'],
	'Content-Type': 'application/json',
	'x-okapi-token': token
}

# System-UUID des Inhaltstyps in Konkordanzzuordnung ergänzen
subscript_list = get_refdata("SubscriptionAgreement.ContentType")
if subscript_list == 0:
	print("Keine passende Auswahlliste gefunden")
	exit(1)

for inh in inhaltstyp:
	inhaltstyp[inh].append(subscript_list[inhaltstyp[inh][1]])


# Anzahl der insgesamt zu prüfenden Vereinbarung
number_ass = get_number_of_sas()
if number_ass == 0:
	print("Keine Vereinbarung gefunden")
	exit(1)

all_sass = get_id_medientyp_all_sas(number_ass) # Vereinbarungen mit einem Eintrag in Medientyp
if len(all_sass) == 0:
	print("Keine Vereinbarung gelistet")
	exit(1)

# über List alle Vereinbarungen ggf. Anpassung Inhaltstyp
for sas in all_sass:

	# nur wenn es nicht bereits einen Eintrag im Feld Inhaltstyp gibt
	if sas['inhalt'] != "":
		print(str(sas['id']) +"--" + str(sas['name'])+ " wird nicht angepasst, hat Inhaltsfeld " + str(sas['inhalt']))
	else:
		print(str(sas['id']) +"--" + str(sas['name'])+ " wird angepasst, mit Inhaltstyp aus Medientyp " + inhaltstyp[str(sas['value'])][1])
		
		# Zusammenstellung des JSON Update Strings aus den entsprechenden Werten
		payload = '{"agreementContentTypes": [ \
		{ \
			"contentType": { \
			"id": "' + inhaltstyp[str(sas['value'])][2] + '" \
			, "_delete": false \
			, "value": "' + inhaltstyp[str(sas['value'])][1] + '" \
			, "label": "' +inhaltstyp[str(sas['value'])][0] + '" \
		}}]}'
		# update
		status_code = update_inhaltstyp(str(sas['id']),payload) 
		if status_code is not None:
			print(f"Statuscode: {status_code}")

