## Overview

The project is an AI assistant chat application showcasing three distinct communication methods: standard HTTP, Server-Sent Events (SSE), and WebSocket with a streaming effect. The frontend dynamically connects to two separate Flask servers based on the chosen communication method. These Flask servers interface with an OpenAI-powered travel assistant, capable of automating travel inquiries such as flight schedule searches and visa requirement checks. The system leverages Retrieval-Augmented Generation (RAG) to enhance AI responses. Additionally, the application seamlessly integrates with an external chat system, facilitating smooth interactions between AI travel assistants and human consultants. The platform also supports third-party integrations, including MS Teams and WhatsApp, via webhooks.

## Architecture
<img width="882" height="662" alt="intro-m" src="https://github.com/user-attachments/assets/d4720ae0-b6d8-418b-9f7e-b990bde28492">


## Features

- **Chat with AI Assistant using HTTP:** Server remains RESTful but does not provide a streaming effect. 
- **Chat with AI Assistant using SSE:** Server-Sent Events (SSE) for real-time streaming. Each SSE connection is maintained only for the duration of a single query-response cycle, ensuring the server remains RESTful.
- **Chat with AI Assistant using SocketIo:** Real-time communication with AI assistant using WebSocket for streaming responses. However, due to the stateful nature of WebSocket, the server is not RESTful, which can pose challenges for horizontal scaling.
- **Switch between AI Assistant and Human Consultant:** The AI assistant can facilitate the switch between chatting with the AI or a human consultant based on the conversation context.
- **Integration with third-party platforms:** The application can be easily integrated with third-party platforms, including MS Teams and WhatsApp, via webhooks.
- **Speech recognition:** The application includes speech recognition functionality using the Web Speech API. Users can toggle the microphone to enable or disable speech input, providing a hands-free chat experience.

## Screenshots
<div> 
   <img width="600" height="650" alt="intro-m" src="https://github.com/user-attachments/assets/2346b0c9-be4c-4b43-b648-b2917b7bfebb">
   <img width="400" height="650" alt="intro-m" src="https://github.com/user-attachments/assets/5ff70724-a9f3-42cd-b878-eab2106db0ee">
</div>

<div>
   <img width="500" height="650" alt="intro-m" src="https://github.com/yuguangdang/ai-travel-assistant-frontend/assets/55920971/72757398-f3bf-4155-bc7a-fa14f5255294">
   <img width="500" height="650" alt="intro-m" src="https://github.com/yuguangdang/ai-travel-assistant-frontend/assets/55920971/597ed74e-2908-44c2-b899-961f6a2fb64c">
</div>

