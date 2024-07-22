## Overview

This project showcases an AI assistant chat application that supports three communication methods: standard HTTP, Server-Sent Events (SSE), and WebSocket with streaming capabilities. The frontend dynamically connects to two Flask servers based on the chosen communication method. These Flask servers interface with an OpenAI-powered travel assistant, capable of automating various travel inquiries, such as searching flight schedules and checking visa requirements. To enhance AI responses, the system employs Retrieval-Augmented Generation (RAG). Additionally, the application integrates with an external chat system, providing users with a seamless experience when interacting with both AI travel assistants and human consultants.

## Architecture
<img width="882" height="662" alt="intro-m" src="https://github.com/yuguangdang/ai-travel-assistant-frontend/assets/55920971/32ec8ed4-f30a-43d7-8d72-cbde5081475d">

## Features
- Create, update, and manage Azure OpenAI assistants.
- RAG (Retrieval-Augmented Generation) to enhance the AI responses.
- Support for multiple communication platforms including Teams and WhatsApp.
- Streaming responses using Server-Sent Events (SSE).
- Integration with external APIs for additional functionalities like visa checks and flight schedules.
- Integration with an external chat server so that users can switch between chat with AI and chat with humans.

<img width="862" height="700" alt="intro-m" src="https://github.com/yuguangdang/ai-travel-assistant-frontend/assets/55920971/c22cedfa-74cd-461c-95d2-65d5c5a37c77">
<div>
   <img width="420" height="700" alt="intro-m" src="https://github.com/yuguangdang/ai-travel-assistant-frontend/assets/55920971/72757398-f3bf-4155-bc7a-fa14f5255294">
   <img width="420" height="700" alt="intro-m" src="https://github.com/yuguangdang/ai-travel-assistant-frontend/assets/55920971/597ed74e-2908-44c2-b899-961f6a2fb64c">
</div>

