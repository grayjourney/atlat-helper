# Atlassian Helper Agent - User Manual

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- An Atlassian Account (Jira/Confluence)
- An AI API Key (Google Gemini or Anthropic Claude)

### Installation

1.  **Clone the repository** (if you haven't already).
2.  **Start the application**:
    ```bash
    make dev
    # OR
    docker compose up --build
    ```
3.  **Access the UI**: Open [http://localhost:8081](http://localhost:8081) in your browser.

---

## 🔐 Authentication (OAuth)

1.  When you first open the app, you will see a **"Connect to Atlassian"** button in the chat.
2.  Click the button to be redirected to Atlassian's secure login page.
3.  Grant permissions for the **Atlassian Helper** to access your Jira and Confluence sites.
4.  You will be redirected back to the app.
5.  **Restart the chat** (refresh or click "New Chat") to start using the agent.

> **Note:** Your credentials are saved securely in `token_storage.json` inside the container. You don't need to login every time.

---

## 🤖 Using the Agent

### Configuration
1.  Click the **Settings (⚙️)** icon in the bottom left.
2.  Select your **AI Model** (Gemini or Claude).
3.  Enter your **API Key**.

### Common Commands

#### 🎫 Jira Tickets
- "What is the status of ticket `PROJ-123`?"
- "Assign `PROJ-123` to me."
- "What requires my attention in `PROJ-456`?"
- "Create a bug ticket for the login page crash."

#### 📝 Confluence
- "Search for documentation about `Authentication`."
- "Find pages related to `Onboarding`."

#### 📊 Sprint Planning (Beta)
- "Show me the current sprint status."

---

## 🛠️ Troubleshooting

### "Connect" button doesn't work
- Ensure the API is running at `http://localhost:8000`.
- Check if port `8000` is blocked.

### "No valid credentials found"
- If verifying E2E, make sure you have logged in via the UI first.
- Or check `token_storage.json` permissions.

### UI Errors
- If you see a "Validation Error", try refreshing the page or rebuilding the UI container:
  ```bash
  docker compose up -d --build ui
  ```
