import json
import os
import logging
from typing_extensions import override
from openai import AssistantEventHandler

from .functions import (
    chat_with_consultant,
    flight_schedule,
    get_itinerary,
    get_live_bookings,
    visa_check,
)


# Without streaming
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


# With streaming
class EventHandler(AssistantEventHandler):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.tool_outputs  = None
        self.run_id = None

    @override
    def on_text_created(self, text) -> None:
        # Log when text is created by the assistant
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        # Log and emit the text delta as it is generated by the assistant
        # print(delta.value, end="", flush=True)
        pass

    def on_tool_call_created(self, tool_call):
        # Log when a tool call is created
        print(
            f"\nassistant > {tool_call.type}: {tool_call.function.name}\n", flush=True
        )

    @override
    def on_event(self, event):
        # Handle events that require action
        if event.event == "thread.run.requires_action":
            run_id = event.data.id
            self.run_id = run_id
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data, run_id):
        # Handle required actions by processing tool calls
        tool_outputs = []
        for tool in data.required_action.submit_tool_outputs.tool_calls:
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
                chat_response = chat_with_consultant(initial_message)
                print(chat_response)
                self.socketio.emit("chat_with_consultant", chat_response, room=self.sid)
                response = "Connecting the client to a consultnat in a new tab."
                tool_outputs.append(
                    {"tool_call_id": tool.id, "output": json.dumps(response)}
                )

        # Submit the tool outputs  
        self.tool_outputs = tool_outputs


def get_streaming_response_from_assistant(thread_id, message, client):
    event_handler=EventHandler(client)
    # Add a message to the assistant thread
    print(f"\nclient >", message)
    message = client.beta.threads.messages.create(
        thread_id=thread_id, role="user", content=message
    )
    # Stream the assistant's response to the message
    with client.beta.threads.runs.stream(
        thread_id=thread_id,
        assistant_id=os.getenv("ASSISTANT_ID"),
        event_handler=event_handler,
    ) as stream:
        for delta in stream.text_deltas:
            print(delta, end="", flush=True)
            yield delta
    
    if event_handler.tool_outputs and event_handler.run_id:
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=thread_id,
            run_id=event_handler.run_id,
            tool_outputs=event_handler.tool_outputs,
        ) as stream:
            for delta in stream.text_deltas:
                print(delta, end="", flush=True)
                yield delta
