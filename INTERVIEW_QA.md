# 📌 Quantum Project - Interview Questions & Answers

## 🔹 Basic Questions
- **What is the objective of this project?**
  The objective of **Quantum** is to solve the problem of "meeting fatigue" and information loss. It uses AI to automate the boring parts of meetings—like taking notes, tracking decisions, and assigning tasks—so teams can focus on the actual conversation while ensuring nothing important is missed.

- **Explain the overall workflow of your system.**
  It’s a 4-step process: 
  1. **Join**: A Vexa AI bot joins the meeting (Google Meet/Teams) via a URL.
  2. **Transcribe**: The bot captures audio and generates a real-time transcript with speaker identification.
  3. **Analyze**: Our backend processes the text using NLP to extract summaries, sentiment, and action items.
  4. **Action**: Insights are pushed to the frontend dashboard, and tasks are automatically created in the Kanban board.

## 🔹 System Design & Architecture
- **Explain the frontend-backend architecture.**
  We use a **decoupled architecture**. The frontend is a **Next.js 14** Single Page Application (SPA) that communicates with a **FastAPI** backend via RESTful APIs. For real-time updates like live transcription, we use a polling mechanism (or WebSockets) to fetch the latest data from the Vexa AI integration.

- **Why did you choose Next.js and FastAPI?**
  I chose **Next.js** for its excellent developer experience, built-in routing, and fast rendering (Turbopack). **FastAPI** was the choice for the backend because it's high-performance, asynchronous by nature, and has native support for Pydantic models, which makes handling AI data structures very easy and type-safe.

## 🔹 Machine Learning / AI (VERY IMPORTANT SECTION)
- **How does speech-to-text work in your project?**
  We integrate with the **Vexa AI API**, which provides a meeting bot that joins the call. The bot uses advanced **Whisper-based models** to convert audio streams into text. It handles background noise and different accents quite well, providing the text to our backend in real-time.

- **Which NLP techniques are used for summarization?**
  We use **LLM-based summarization** (like GPT-4 or similar via Langflow). Instead of simple extractive summarization (picking sentences), we use **abstractive summarization**. This means the AI understands the context and "rewrites" a concise version focusing on decisions and "next steps" rather than just shortening the text.

- **How does emotion analysis work?**
  We perform **Text-based Sentiment Analysis**. Once we have the transcript, we pass segments to a sentiment model that looks for keywords, tone indicators, and context. It calculates a "Sentiment Score" (0-10) and tracks how the mood shifts throughout the meeting timeline.

- **What is speaker diarization?**
  It’s the process of "who spoke when." The Vexa AI bot identifies unique voice profiles and labels the transcript with "Speaker A," "Speaker B," etc. This is crucial for our **Task Automation** because it helps us attribute specific action items to the correct person automatically.

- **How do you handle multilingual input?**
  The system supports **English, Hindi, and Gujarati**. We use the Vexa AI bot's native language detection and transcription capabilities. Since the underlying models are trained on diverse datasets, they can transcribe these languages directly without needing a separate translation step first.

- **What challenges did you face in ML integration?**
  The biggest challenge was **latency**. Getting a transcript in real-time while a person is still speaking requires a very fast pipeline. We had to optimize how often we poll the API to ensure the UI feels snappy without hitting rate limits or consuming too many credits.

- **How do you evaluate model performance?**
  For transcription, we look at **Word Error Rate (WER)**. For summarization and task extraction, we do manual "Ground Truth" testing—comparing the AI's extracted tasks against what a human would have written to check for hallucinations or missed items.

- **Why did you choose API-based AI instead of training your own model?**
  As a student/hackathon project, using **Vexa AI** and specialized APIs allowed us to focus on the **Product Logic** and **User Experience**. Training a custom STT or diarization model requires massive compute resources and data, which wasn't feasible for a quick-turnaround project.

## 🔹 Features & Functionality
- **Explain the transcription feature.**
  It's a live feed in the Meeting Intelligence page. As the bot listens, it sends chunks of text. The UI maps these chunks to speaker avatars so you can follow the conversation visually, even if you join the meeting late.

- **Explain task automation.**
  The system scans the transcript for "intent" words like "I will," "Can you," or "Need to." It extracts the **Subject**, **Assignee**, and **Context**, then automatically populates a Kanban card. Users can then sync these directly to Jira or Trello with one click.

- **Explain the emotion analytics dashboard.**
  It provides a high-level view of team health. It shows a **Timeline Chart** of engagement and a **Sentiment Breakdown**. If a meeting had many "Concerns" or low engagement, managers can see exactly at which minute the energy dropped.

## 🔹 Technical Stack Justification
- **Why Next.js?**
  It provides **App Router** for clean folder-based routing and **Optimized Images/Fonts** out of the box, making the landing page and dashboard load extremely fast.
- **Why FastAPI?**
  It's much faster than Flask or Django for I/O-bound tasks like calling AI APIs. The **Auto-generated Swagger docs** also made frontend-backend integration much smoother.
- **Why Tailwind CSS?**
  It allowed me to build a professional "Enterprise" look (using **shadcn/ui**) without writing thousands of lines of custom CSS. It's very easy to maintain and supports dark mode natively.

## 🔹 Challenges Faced
- **Real-time transcription issues**: Sometimes the bot takes ~10 seconds to join, which can be confusing for users. I handled this by adding "Loading States" and "Bot Status" indicators in the UI.
- **API latency**: Processing large transcripts for summary can take a few seconds. I used **Async/Await** on the backend and "Skeleton Screens" on the frontend to keep the UI from freezing.
- **Emotion detection accuracy**: Sarcasm or technical jargon can sometimes confuse sentiment models. I mitigated this by focusing more on "Engagement Levels" (how much people are talking) which is a more reliable metric.

## 🔹 Future Improvements
- **Model fine-tuning**: I want to fine-tune the summarization model on **technical/coding meetings** to better understand Jira-style tasks.
- **Real-time AI streaming**: Moving from polling to a full **WebSocket** implementation for zero-latency transcript updates.
- **Video Analysis**: Adding facial expression analysis alongside text-based sentiment for a 360-degree view of meeting emotions.

## 🔹 Rapid Fire Questions
- **Q: Database used?** A: SQLite for dev (easy to set up), PostgreSQL for prod.
- **Q: How do you handle auth?** A: JWT (JSON Web Tokens) for secure, stateless sessions.
- **Q: Best feature?** A: The automated Kanban task extraction—it saves hours of manual work.
- **Q: UI Library?** A: shadcn/ui—it's highly customizable and accessible.
- **Q: AI Engine?** A: Vexa AI for transcription and LLMs for intelligent processing.
