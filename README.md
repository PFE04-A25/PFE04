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
python server.py
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

## 6. Test Execution and Metrics with Maven & JaCoCo

RestAuto integrates Maven and JaCoCo to provide comprehensive test execution and code coverage analysis for generated RestAssured tests.

### Maven Configuration

The platform automatically detects Maven installations across different platforms:

**Windows:**
- VS Code Extension Maven: `%USERPROFILE%\AppData\Roaming\Code\User\globalStorage\pleiades.java-extension-pack-jdk\maven\latest\bin\mvn.cmd`
- Standard installations: `C:\Program Files\Apache\maven\bin\mvn.cmd`
- System PATH environment variable

**Linux/macOS:**
- `/usr/bin/mvn`, `/usr/local/bin/mvn`, `/opt/maven/bin/mvn`
- System PATH environment variable

**Manual Configuration:**
If auto-detection fails, set the `MAVEN_PATH` environment variable:

```bash
# Windows (PowerShell - Persistent)
[Environment]::SetEnvironmentVariable("MAVEN_PATH", "C:\path\to\mvn.cmd", "User")

# Windows (PowerShell - Session)
$env:MAVEN_PATH = "C:\path\to\mvn.cmd"

# Linux/macOS
export MAVEN_PATH=/path/to/mvn
```

### Test Execution Process

When you click "Execute Tests" in the application:

1. **Temporary Maven Project Creation:**
   - Creates a temporary directory with proper Maven structure
   - Generates `pom.xml` with Spring Boot and RestAssured dependencies
   - Sets up `src/main/java` and `src/test/java` directories

2. **Spring Boot Test Application:**
   - Auto-generates a minimal Spring Boot application
   - Integrates your API code as controllers
   - Configures proper annotations and dependencies

3. **Maven Test Execution:**
   ```bash
   mvn clean test jacoco:report
   ```
   - Runs all generated RestAssured tests
   - Collects JaCoCo coverage data during execution
   - Generates comprehensive coverage reports

### JaCoCo Code Coverage Integration

JaCoCo is automatically configured to provide detailed coverage metrics:

**Coverage Types:**
- **Line Coverage:** Percentage of code lines executed during tests
- **Branch Coverage:** Percentage of conditional branches tested
- **Instruction Coverage:** Percentage of bytecode instructions covered

**Generated Reports:**
- XML format for programmatic analysis
- HTML format for human-readable reports
- Coverage thresholds validation (50% minimum by default)

**Metrics Collected:**
```json
{
  "line_coverage": 85.5,
  "branch_coverage": 78.2,
  "instruction_coverage": 82.1,
  "lines_covered": 171,
  "lines_total": 200,
  "branches_covered": 25,
  "branches_total": 32,
  "tests_run": 8,
  "success_rate": 100.0,
  "execution_time": 12.3
}
```

### Quality Analysis

The platform provides intelligent quality assessment:

**Coverage Quality Levels:**
- **Excellent:** Line ≥90%, Branch ≥85%
- **Good:** Line ≥80%, Branch ≥70%
- **Fair:** Line ≥60%, Branch ≥50%
- **Poor:** Below fair thresholds

**Test Completeness Analysis:**
- Calculates tests-per-endpoint ratio
- Recommends minimum 2-3 tests per API endpoint
- Provides completeness scoring (insufficient/minimal/adequate/comprehensive)

**Automated Recommendations:**
- Suggests areas needing more coverage
- Identifies untested branches and edge cases
- Provides actionable improvement guidance

### Real-time Execution Monitoring

Track test execution progress in real-time:

1. **Status Updates:** Running → Completed/Failed/Timeout
2. **Live Logs:** Maven build output and test results
3. **Progress Tracking:** Execution time and build phases
4. **Error Reporting:** Detailed failure analysis and compilation errors

### Integration with Test History

All execution results are automatically saved:
- Links generated tests with execution metrics
- Enables re-execution of previous tests
- Maintains historical performance tracking
- Supports comparison across test versions

Now you're all set! 🚀
