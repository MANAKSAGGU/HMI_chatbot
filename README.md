# 🤖 HMI_Chatbot

**HMI_Chatbot** is a full-stack AI video avatar chatbot platform that enables human-like multimodal interaction. Users can upload text, audio, or PDFs, and receive personalized video responses from a lip-synced avatar powered by advanced AI models like SadTalker, XTTS, and InstantID.

---

## 🚀 Features

- 🎤 Text-to-Speech (TTS) using XTTS with optional voice cloning
- 📄 RAG-based Question Answering from uploaded PDFs
- 👄 Talking Avatar Generation using SadTalker
- 📸 Face Reference using InstantID or IP-Adapter
- 🎥 Audio & Video Output of chat responses
- 💡 Modern UI built with Tailwind CSS
- 🔐 User Authentication (Sign up, Login)
- 📁 Upload or record audio, capture webcam images

---

## 📁 Folder Structure

HMI_Chatbot/
- ├── app/ # FastAPI backend logic
- │ ├── routes/ # API endpoints
- │ ├── models/ # Database/user models
- │ ├── utils/ # Helper functions
- │ └── core/ # Pipeline and logic
- ├── templates/ # Jinja2 HTML templates
- ├── static/ # TailwindCSS, JS, and media assets
- ├── uploads/ # Uploaded audio, images, PDFs
- ├── inference3.py # Main avatar generation + TTS script
- ├── rag.py # Main response generation script
- ├── transalte_xtts_api1.py # Main TTS module
- ├── rag_gui_api.py # FastAPI app entry point
- ├── requirements.txt # Python dependencies
- ├── .gitignore
- └── README.md

## AI Models Used
___
Task	| Model
___
TTS & Voice Cloning |	Coqui XTTS
___
Talking Avatar |	SadTalker
___
Face Embedding |	InsightFace (buffalo_l)
___
RAG QA on PDFs |	Custom Retriever + Reader

## 👤 Author
- Hridyansh Katal, Manak Saggu, Ishaan Michu
- GitHub: @Hridyansh30, @MANAKSAGGU, @michuishaan07

## 🙏 Acknowledgements
SadTalker

Coqui XTTS

FastAPI

Tailwind CSS
