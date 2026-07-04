# 🥗 NutriBot — AI Nutrition Agent

An AI-powered nutrition advisor and meal planner built with **Python Flask** and **IBM Watsonx.ai (Granite)**. Features a fully responsive chat UI, nutrition dashboard, BMI calculator, meal planner, and family profile management.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **Chat UI** | Conversational nutrition agent powered by `ibm/granite-3-8b-instruct` |
| 📊 **Nutrition Dashboard** | AI calorie & macro breakdown with Chart.js visualisations |
| 🍽️ **Meal Planner** | 1/3/7-day personalised AI meal plans with Indian food focus |
| ⚖️ **BMI Calculator** | Interactive gauge meter with AI health tips |
| 👨‍👩‍👧‍👦 **Family Profiles** | SQLite-backed CRUD profiles for personalised advice |
| 🌙 **Dark Mode** | Persisted in `localStorage`, zero page-flash |
| 📱 **Mobile Responsive** | Bootstrap 5.3 grid, works on all screen sizes |

---

## 🛠️ Prerequisites

- Python **3.10** or newer
- `pip` package manager
- An **IBM Cloud** account ([sign up free](https://cloud.ibm.com/registration))
- A **Watsonx.ai** project ([create one](https://dataplatform.cloud.ibm.com/))

---

## 🚀 Quick Start

### 1. Clone / unzip the project

```bash
git clone <your-repo-url> nutrition-agent
cd nutrition-agent
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your credentials:

```dotenv
IBM_API_KEY=your-ibm-cloud-api-key-here
WATSONX_PROJECT_ID=your-watsonx-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
FLASK_SECRET_KEY=replace-with-a-long-random-string
FLASK_ENV=development
```

### 5. Run the development server

```bash
flask --app app run --debug
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

---

## 🔑 Environment Variables

| Variable | Required | Description | Where to find it |
|---|---|---|---|
| `IBM_API_KEY` | ✅ | IBM Cloud API Key | [cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys) → Create |
| `WATSONX_PROJECT_ID` | ✅ | Watsonx.ai Project ID | Open your project → Manage → General → Project ID |
| `WATSONX_URL` | ✅ | Regional endpoint | See table below |
| `FLASK_SECRET_KEY` | ✅ | Flask session secret | Any long random string |
| `FLASK_ENV` | ❌ | `development` or `production` | Set manually |

**Regional Watsonx.ai endpoints:**

| Region | URL |
|---|---|
| US South (Dallas) | `https://us-south.ml.cloud.ibm.com` |
| EU (Frankfurt) | `https://eu-de.ml.cloud.ibm.com` |
| EU (London) | `https://eu-gb.ml.cloud.ibm.com` |
| Asia Pacific (Tokyo) | `https://jp-tok.ml.cloud.ibm.com` |

---

## 🌐 Production Deployment

### Gunicorn (local/VPS)

```bash
gunicorn app:app --bind 0.0.0.0:8080 --workers 2 --timeout 120
```

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]
```

Build and run:

```bash
docker build -t nutribot .
docker run -p 8080:8080 --env-file .env nutribot
```

### IBM Cloud Code Engine

```bash
# Install IBM Cloud CLI + Code Engine plugin first
ibmcloud login --apikey $IBM_API_KEY -r us-south
ibmcloud ce project create --name nutribot-project
ibmcloud ce project select --name nutribot-project

# Deploy from container registry (push your Docker image first)
ibmcloud ce application create \
  --name nutribot \
  --image <your-registry>/nutribot:latest \
  --port 8080 \
  --env IBM_API_KEY=$IBM_API_KEY \
  --env WATSONX_PROJECT_ID=$WATSONX_PROJECT_ID \
  --env WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env FLASK_SECRET_KEY=$FLASK_SECRET_KEY
```

---

## 🎛️ Customising the Agent

All agent behaviour is controlled by the **`AGENT_INSTRUCTIONS`** block in [`config.py`](config.py).
You never need to touch any other file.

### Sections you can edit

| Section | What it controls |
|---|---|
| `[ROLE]` | Agent persona, expertise, and primary purpose |
| `[TONE]` | Communication style — formal, casual, empathetic, etc. |
| `[DIET_SPECIALIZATION]` | Which diets and conditions the agent specialises in |
| `[INDIAN_FOOD_PREFERENCES]` | Indian foods to prioritise, spices, regional diversity |
| `[SAFETY_RULES]` | Hard limits — medical advice, calorie floors, allergies policy |
| `[OUTPUT_FORMAT]` | How responses are structured — tables, bullets, markdown |

### Example: make the agent stricter about calories

```python
# In config.py → AGENT_INSTRUCTIONS → [SAFETY_RULES]
# Change:
"Do not suggest extreme caloric restriction below 1200 kcal/day for adults."
# To:
"Do not suggest caloric restriction below 1400 kcal/day for adults. Always recommend consulting a dietitian before going below 1600 kcal/day."
```

### Example: add a language preference

```python
# Add to [TONE] section:
"If the user writes in Hindi or uses Hindi words, reply in a friendly mix of Hindi and English (Hinglish)."
```

### Tuning the AI model

In `config.py`, edit `WATSONX_PARAMS`:

```python
WATSONX_PARAMS = {
    "max_new_tokens": 1024,   # increase for longer meal plans
    "temperature":    0.7,    # lower for more factual, higher for creative
    "top_p":          0.95,
    "top_k":          50,
    "repetition_penalty": 1.1,
}
```

---

## 📁 Project Structure

```
nutrition-agent/
├── app.py                    # Flask app entry point — registers blueprints, page routes
├── config.py                 # ⭐ AGENT_INSTRUCTIONS + all config constants
├── db.py                     # SQLite helpers — init, CRUD for family_profiles table
├── watsonx_client.py         # IBM Watsonx.ai wrapper — chat(), analyse_nutrition(), generate_meal_plan()
├── routes/
│   ├── chat.py               # POST /api/chat
│   ├── nutrition.py          # POST /api/nutrition/analyse, /api/meal-plan/generate
│   ├── bmi.py                # POST /api/bmi
│   └── profiles.py           # GET/POST/PUT/DELETE /api/profiles
├── templates/
│   ├── base.html             # Shared layout: navbar, dark-mode toggle, CDN links
│   ├── index.html            # Chat UI page
│   ├── dashboard.html        # Nutrition Dashboard
│   ├── meal_plan.html        # Meal Planner
│   ├── bmi.html              # BMI Calculator
│   └── profiles.html         # Family Profiles manager
├── static/
│   ├── css/style.css         # All custom styles, dark mode CSS variables, animations
│   └── js/app.js             # Dark mode, apiFetch(), showToast(), animateCount()
├── .env                      # 🔒 Your secrets (gitignored)
├── .env.example              # Safe template — commit this
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔒 Security Notes

- Never commit `.env` — it's in `.gitignore`
- Rotate your `FLASK_SECRET_KEY` before any public deployment
- In production, set `FLASK_ENV=production` to disable the debugger
- The app has no authentication — it's designed for single-household use on a private network. Add a reverse proxy (nginx) with basic auth if exposing publicly.

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `AuthenticationError` | Check `IBM_API_KEY` is correct and not expired |
| `ProjectNotFound` | Verify `WATSONX_PROJECT_ID` from the Watsonx dashboard |
| Empty AI responses | Increase `max_new_tokens` in `WATSONX_PARAMS` |
| Charts not rendering | Ensure JavaScript is enabled; check browser console |
| `nutrition.db` permissions | Ensure the app directory is writable |

---

## 📜 Disclaimer

NutriBot provides **general nutritional information only** and is not a substitute for professional medical or dietetic advice. Always consult a registered dietitian or physician for clinical nutrition guidance.

---

<p align="center">Made with ❤️ using IBM Watsonx.ai + Granite</p>
