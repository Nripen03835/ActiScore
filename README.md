# ActiScore :-

## Project Description
ActiScore is a web application designed to provide real-time analysis and insights, likely related to performance or emotional states, given the presence of "FER_Dataset" (Facial Expression Recognition) and "SER_Dataset" (Speech Emotion Recognition) in the project structure. It features a user authentication system, team management, and a chatbot for interactive assistance. The application aims to offer a dynamic and engaging user experience through its various functionalities.

## Features
*   **User Authentication:** Secure login and registration for users.
*   **Team Management:** Create and manage teams for collaborative analysis.
*   **Real-time Analysis:** Integration of real-time data processing, potentially for facial expressions and speech emotions.
*   **Interactive Chatbot:** An AI-powered assistant to provide support and information.
*   **Dashboard:** A centralized view for users to monitor their activities and insights.
*   **API Documentation:** Endpoints for external integrations.

## Installation

To set up and run ActiScore locally, follow these steps:

### Prerequisites
*   Python 3.x
*   pip (Python package installer)
*   Node.js and npm (if there are any frontend build steps, though not explicitly seen in the current structure, it's good practice to include)

### Backend Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/ActiScore-Latest.git
    cd ActiScore-Latest
    ```
    (Replace `https://github.com/your-username/ActiScore-Latest.git` with your actual repository URL)

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**
    *   **Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    Also install rustc using below link
    https://rustup.rs/
    ```

5.  **Database Initialization:**
    The application uses SQLite. The database will be created automatically when the application runs for the first time, or you might need to run migrations if available (e.g., Flask-Migrate).

### Running the Application

1.  **Start the Flask application:**
    ```bash
    python app.py
    before above command, run the sub AI Projects using 'python app.py' in the terminal
    ```
    The application will typically run on `http://127.0.0.1:5000` (or the port configured in `app.py`).

## Usage

Once the application is running:

1.  Open your web browser and navigate to `http://127.0.0.1:5000` (or your configured port).
2.  Register a new account or log in if you already have one.
3.  Explore the dashboard, create teams, and utilize the real-time analysis features.
4.  Interact with the ActiScore Assistant chatbot for help.

## Technologies Used
*   **Backend:** Python, Flask, Flask-SocketIO
*   **Frontend:** HTML, CSS, JavaScript
*   **Database:** SQLite
*   **Machine Learning:** Potentially Dlib for facial analysis, and other libraries for FER/SER (e.g., TensorFlow, Keras, scikit-learn based on `models` directory).
