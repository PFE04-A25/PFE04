# Autotest: Automated Test Generation

Autotest simplifies automated test generation by leveraging AI models. Follow these three simple steps to set up and run the project.

## 1. Frontend Setup

First, clone the repository:

```bash
git clone git@github.com:PierreLouisLetoquart/autotest.git
```

Navigate to the project folder and install dependencies:

> **Note:** We use [pnpm](https://pnpm.io/) as the package manager. Install it [here](https://pnpm.io/installation) if you haven't already.

```bash
pnpm i
```

Run the development server:

```bash
pnpm dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## 2. LLM Model Setup:

## 2.1 Case 1: DeepSeek

Autotest relies on an AI model for generating tests. We recommend using `DeepSeek-r1:7b` with [Ollama](https://ollama.com/).

1. **Install Ollama** (if not installed): Follow the instructions [here](https://ollama.com).
2. **Download the model**:

   ```bash
   ollama pull deepseek-r1:7b
   ```

Ollama will handle model execution locally, ensuring fast and private processing.

---

## 2.2 Case 2: Gemini

Analyze a Java Spring Boot API code and generate RestAssured tests using Google's Gemini model via LangChain.

1. **Obtain your gemini key** : Follow the instructions [here](https://ai.google.dev/gemini-api/docs/api-key?hl=fr).
2. **Copier la clé API** : Once the key is generated, you can copy it. This key is your identifier to interact with the Gemini API.
   Keep the key secure: **Do not share this key and keep it in a safe place**
3. **Add your key in the gemini.py file** :
   - **a**: You can manually add your API key to the code [api_key = 'YOUR_API_KEY']
   - **b**: Use environment variables (more secure): For better security, it is recommended to add the API key to your environment variables instead of hardcoding it into the code.

## 3. Backend Setup

First, navigate to the backend folder:

```bash
cd backend
```

Set up a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the backend server:

```bash
python gemini.py
```

The server will start on [http://localhost:5000](http://localhost:5000).

To customize the backend URL, set the `BACKEND_BASE_URL` environment variable:

```bash
export BACKEND_BASE_URL=http://localhost:6969
python server.py
```

Or update the `.env` file:

```env
BACKEND_BASE_URL=http://localhost:6969
```

## 4.Backend Mistral 

First, navigate to the backend folder:

```bash
cd backend
```

Set up a virtual environment and activate it:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install fastapi uvicorn httpx pydantic
```

Add your Mistral API key in the `Server_mistral.py` file to the `MISTRAL_API_KEY` variable

## Start the server

```bash
uvicorn Server_mistral:app --reload
```

## 5.Backend MongoDB

First, make sure to pupdate you .env with the connexion to mongo instance :

```bash
MONGODB_URL=yourmongourl
```

The server will start on [http://127.0.0.1:8000](http://127.0.0.1:8000).

Now you're all set! 🚀
