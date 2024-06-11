from datetime import date, datetime
import json
import os
import uuid
import requests
import pymssql
from flask import session
from dotenv import load_dotenv
from flask import current_app

load_dotenv()

CANCELLATION_URL = os.getenv("CANCELLATION_URL")


def get_itinerary(pnr):
    """
    Retrieve the itinerary based on the PNR.

    Parameters:
    pnr (str): The Passenger Name Record identifier.

    Returns:
    dict: A dictionary containing the itinerary details, or None if an error occurs.
    """
    data = {
        "PNR": pnr,
        "LASTNAME": "test_lastname",
        "USER_ROLE": "traveller",
        "EMAIL": "test_email@example.com",
        "DEBTORID": "CTMZZZZZZZ",
        "OFFICE": "test_office",
        "INTENT": "check_if_cancel_possible",
    }

    try:
        res = requests.post(CANCELLATION_URL, json=data)
        itinerary = res.text
        print(f"itinerary: {itinerary}")
        return itinerary
    except requests.RequestException as e:
        print(f"Error fetching itinerary: {e}")
        return None


def flight_schedule(departure_airport, arrival_airport, year, month, day):
    # API endpoint
    url = f"https://api.flightstats.com/flex/schedules/rest/v1/json/from/{departure_airport}/to/{arrival_airport}/departing/{year}/{month}/{day}"

    # API credentials (replace with your actual appId and appKey)
    params = {"appId": "38d3993c", "appKey": "b26e24febea74f8426496d989190874c"}

    # Make the API request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Return the JSON data
        return response.json()
    else:
        # Return the error status and message if something went wrong
        return {"error": response.status_code, "message": "Failed to retrieve data"}


def visa_check(
    passportCountry: str,  # Country code of the passport (e.g., 'USA')
    departureDate: str,  # Departure date in YYYY-MM-DD format
    arrivalDate: str,  # Arrival date in YYYY-MM-DD format
    departureAirport: str,  # Airport code for the departure airport (e.g., 'JFK')
    arrivalAirport: str,  # Airport code for the arrival airport (e.g., 'LHR')
    transitCities: list,  # List of transit city airport codes (e.g., ['DXB', 'CDG'])
    travelPurpose: str,  # Purpose of travel (e.g., 'TOURISM')
):
    """
    Makes a request to the Sherpa API to check visa requirements based on travel details.

    Returns the JSON response from the Sherpa API.
    """
    url = "https://requirements-api.joinsherpa.com/v3/trips?include=restriction,procedure&base&=&="
    locationCode = "airportCode"  # This could be dynamic based on the requirements; set as 'airportCode' for example

    # Construct the API payload with the travel details
    payload = {
        "data": {
            "type": "TRIP",
            "attributes": {
                "locale": "en-US",
                "traveller": {
                    "passports": [passportCountry],
                    "travelPurposes": [travelPurpose.upper()],
                },
                "travelNodes": [
                    {
                        "type": "ORIGIN",
                        locationCode: departureAirport,
                        "departure": {
                            "date": departureDate,
                            "time": "12:59",  # Example time; may need to be adjusted or dynamically set
                        },
                    },
                    {
                        "type": "DESTINATION",
                        locationCode: arrivalAirport,
                        "arrival": {
                            "date": arrivalDate,
                            "time": "12:59",  # Example time; as above
                        },
                    },
                ],
            },
        }
    }

    # Add transit cities to the travel nodes, if any
    for t in transitCities:
        if t:  # Check to ensure the city code is not empty
            payload["data"]["attributes"]["travelNodes"].insert(
                -1,  # Insert before the last node (destination)
                {
                    "type": "TRANSIT",
                    "departure": {"date": departureDate, "time": "00:00"},
                    "arrival": {"date": arrivalDate, "time": "00:00"},
                    locationCode: t,
                },
            )

    # Serialize the payload to JSON format for the request
    payload = json.dumps(payload)
    headers = {
        "Content-Type": "application/vnd.api+json",
        "x-affiliate-id": "ctmapiasia",
        "x-api-key": "AIzaSyCxEnJIc6sVnOrgcgDofSD_yCBSPL-r2ME",  # API key should be securely managed
    }

    # Send the POST request to the Sherpa API and return the parsed JSON response
    response = requests.post(url, headers=headers, data=payload)

    msg = ""
    serpa_data = json.loads(response.text)
    detailsId = []
    dstName = []
    requirements = serpa_data["data"]["attributes"]["informationGroups"]
    for req in requirements:
        if req["name"] == "Visa Requirements":
            visaReq = req["headline"]
            msg = msg + "\n Summary: " + visaReq + "\n"
            for group in req["groupings"]:
                detailsId.append(group["data"][0]["id"])
                dstName.append(group["name"])
                enforcement = group["enforcement"]

                print(visaReq, " Enforcement:", enforcement)
                msg = msg + "\n Enforcement to " + group["name"] + ": " + enforcement

    details = ""
    immi_url = ""
    msg = msg + "\n"
    for inc in serpa_data["included"]:
        # print("..............")
        # print(inc)

        if inc["id"] in detailsId:
            print(inc["attributes"]["description"])
            details = details + inc["attributes"]["description"] + "\n"
            # msg=msg+"\n\n Details: " +inc['attributes']['description']
            if "lengthOfStay" in inc["attributes"]:
                print(inc["attributes"]["lengthOfStay"])
                print(
                    "\nLength of stay:",
                    inc["attributes"]["lengthOfStay"][0]["text"] + "\n",
                )
                msg = (
                    msg
                    + "\n Length of Stay in "
                    + dstName[detailsId.index(inc["id"])]
                    + " "
                    + inc["attributes"]["lengthOfStay"][0]["text"]
                    + "\n"
                )
            print("\nFor more information: ", inc["attributes"]["sources"][0]["url"])
            immi_url += (
                "\n\nFor more information: " + inc["attributes"]["sources"][0]["url"]
            )
        if "type" in inc and inc["type"] == "RESTRICTION":
            print(inc["attributes"]["description"])
            details = details + inc["attributes"]["description"] + "\n"
            # msg=msg+"\n\n Details: " +inc['attributes']['description']

    msg = msg + "\nDetails: \n" + details
    msg = msg + immi_url
    return msg


def get_live_bookings(role, email, debtorId):
    """Fetch and return the bookings/itineraries for the given role, email, and debtorId."""

    if role != "traveller":
        return "You are listed as a Travel Arranger in your profile. Please enter the Agency Reference or PNR."

    server = "sqlserv-preview-prod-fog.secondary.database.windows.net"
    database = "PREVIEW"
    username = "scoutreader"
    password = "termFinish_08!"
    port = 1433

    query = f"""
        SELECT TOP (1000) [PNRID], [PNRLOC], [CRS], [CREATEDATE], [AGENCY], [BOOKDATE], [PSEUDO],
               [FIRSTFLIGHTDATE], [LASTFLIGHTDATE], [TRAVELER_UID], [COMPANY_ID], [CLIENT_GROUP_CODE],
               [HIROLL], [HIHIER], [ONLINE_BKG], [MISSING_HTL], [EMAIL_TRAVELER], [EMAIL_ADMIN1],
               [EMAIL_ADMIN2], [EMAIL_OTHER1], [EMAIL_MANAGER], [CELL_PHONE], [EMERG_NAME], [EMERG_PHONE],
               [AIR_CITIES], [AIR_CARRIERS], [PROFILE_ID], [GLOBAL_GROUP_CODE], [AGENTID]
        FROM [dbo].[PREVIEW_PNR]
        WHERE COMPANY_ID='{debtorId}' AND EMAIL_TRAVELER='{email}'
    """

    try:
        conn = pymssql.connect(
            server=server,
            user=username,
            password=password,
            database=database,
            port=port,
        )
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        return f"Error connecting to database: {e}"

    # Filter out bookings where the LASTFLIGHTDATE is in the past
    today = datetime.today().date()
    future_bookings = []

    for row in rows:
        if "LASTFLIGHTDATE" in row and row["LASTFLIGHTDATE"]:
            if row["LASTFLIGHTDATE"].date() >= today:
                future_bookings.append(row)

    # Convert date and datetime objects to strings
    for row in future_bookings:
        for key, value in row.items():
            if isinstance(value, (datetime, date)):
                row[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                row[key] = str(value)

    return future_bookings


def chat_with_consultant(platform, session_data, initial_message):
    if platform != "web":
        payload = {
            "chatId": str(uuid.uuid4()),
            "teamsChat": True,
            "conversationId": session_data["conversation_id"],
            "aadObjectId": session_data["aadObjectId"],
            "clientName": session_data["metadata"]["name"],
            "clientEmail": session_data["metadata"]["email"],
            "debtorId": session_data["metadata"]["debtorId"],
            "region": "Asia",
            "reason": "Client requested to talk to a consultant",
            "initialMessage": initial_message,
        }
    else:
        payload = {
            "chatId": str(uuid.uuid4()),
            "teamsChat": False,
            "conversationId": None,
            "aadObjectId": None,
            "clientName": session_data["metadata"]["name"],
            "clientEmail": session_data["metadata"]["email"],
            "debtorId": session_data["metadata"]["debtorId"],
            "region": "Asia",
            "reason": "Client requested to talk to a consultant",
            "initialMessage": initial_message,
        }

    try:
        print(f'payload: {payload}')
        response = requests.post(os.getenv("CHAT_INIT"), json=payload)
        if response.status_code == 200:
            return response.json()  # Return the response as a dictionary
        else:
            print(f"Handover to consultant failed: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error initiating handover to consultant: {e}")
        return None


#################################### Example usage ####################################

# result = visa_check('USA', '2024-07-01', '2024-07-15', 'JFK', 'LHR', ['CDG'], 'tourism')
# print(result)

# role = "traveller"
# email = "ben.saul@downergroup.com"
# debtorId = "EDIZZZZZZZ"
# bookings = getBookings(role, email, debtorId)
# print(json.dumps(bookings, indent=4))
