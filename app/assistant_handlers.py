import json
import os
from typing_extensions import override

from .functions import (
    chat_with_consultant,
    flight_schedule,
    get_itinerary,
    get_live_bookings,
    visa_check,
)


def get_response_from_assistant(platform, token, thread_id, message, client):
    try:
        # Add a message to the assistant thread
        print(f"\nclient >", message)
        message = client.beta.threads.messages.create(
            thread_id=thread_id, role="user", content=message
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id,
            assistant_id=os.getenv("ASSISTANT_ID"),
        )

        if run.status == "completed":
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            # Print and return the latest message
            latest_message = messages.data[0].content[0].text.value
            print(f"\nassistant >", latest_message)
            return latest_message
        else:
            print(f"Run status: {run.status}")

        # Define the list to store tool outputs
        tool_outputs = []

        # Loop through each tool in the required action section
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "get_itinerary":
                arguments = json.loads(tool.function.arguments)
                print(f"{tool.function.name} arguments: {arguments}")
                pnr = arguments["PNR"]
                itinerary = get_itinerary(pnr)
                tool_outputs.append({"tool_call_id": tool.id, "output": itinerary})
            elif tool.function.name == "flight_schedule":
                arguments = json.loads(tool.function.arguments)
                print(f"{tool.function.name} arguments: {arguments}")
                departure_airport = arguments["departure_airport"]
                arrival_airport = arguments["arrival_airport"]
                year = arguments["year"]
                month = arguments["month"]
                day = arguments["day"]
                solution = flight_schedule(
                    departure_airport, arrival_airport, year, month, day
                )
                print(solution)
                tool_outputs.append(
                    {"tool_call_id": tool.id, "output": json.dumps(solution)}
                )
            elif tool.function.name == "visa_check":
                arguments = json.loads(tool.function.arguments)
                print(f"{tool.function.name} arguments: {arguments}")
                passportCountry = arguments.get("passportCountry")
                departureDate = arguments.get("departureDate")
                arrivalDate = arguments.get("arrivalDate")
                departureAirport = arguments.get("departureAirport")
                arrivalAirport = arguments.get("arrivalAirport")
                transitCities = arguments.get("transitCities", [])
                travelPurpose = arguments.get("travelPurpose")
                result = visa_check(
                    passportCountry,
                    departureDate,
                    arrivalDate,
                    departureAirport,
                    arrivalAirport,
                    transitCities,
                    travelPurpose,
                )
                print(result)
                tool_outputs.append(
                    {"tool_call_id": tool.id, "output": json.dumps(result)}
                )
            elif tool.function.name == "get_live_bookings":
                arguments = json.loads(tool.function.arguments)
                print(f"{tool.function.name} arguments: {arguments}")
                role = arguments["role"]
                email = arguments["email"]
                debtorId = arguments["debtorId"]
                bookings = get_live_bookings(role, email, debtorId)
                print(bookings)
                tool_outputs.append(
                    {"tool_call_id": tool.id, "output": json.dumps(bookings)}
                )
            elif tool.function.name == "chat_with_consultant":
                arguments = json.loads(tool.function.arguments)
                print(f"{tool.function.name} arguments: {arguments}")
                initial_message = arguments["initial_message"]
                chat_response = chat_with_consultant(platform, token, initial_message)
                print(f"{tool.function.name} respones: {chat_response}")
                response = "Connecting the client to a consultnat in a new tab."
                tool_outputs.append(
                    {"tool_call_id": tool.id, "output": json.dumps(response)}
                )

        # Submit all tool outputs at once after collecting them in a list
        if tool_outputs:
            try:
                run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                )
                print("Tool outputs submitted successfully.")
            except Exception as e:
                print("Failed to submit tool outputs:", e)
        else:
            print("No tool outputs to submit.")

        if run.status == "completed":
            # Print and return the latest message
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            latest_message = messages.data[0].content[0].text.value
            print(f"\nassistant >", latest_message)
            return latest_message
        else:
            print(run.status)

    except Exception as e:
        print(f"An error occurred: {e}")
