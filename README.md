# SmartRecipe AI

## Project Title

**SmartRecipe AI (PS 54 – Recipe Generator from Ingredients)**

## Student Details

**Om Mukund Waghmare** | **Roll No. 54**

## Problem Statement

Food gets wasted at home. Suggest recipes using only the ingredients the user has.

## Key Features

- Select common ingredients or enter custom ingredients.
- Choose dietary preference, meal type, and maximum cooking time.
- Generate three recipes using the available ingredients and basic pantry staples.
- Switch between side-by-side recipe cards and detailed recipe tabs.
- View servings, estimated calories, cooking steps, and zero-waste tips.
- Download generated recipes as a text file.
- Try alternate Gemini models automatically if a model request fails.

## Tech Stack

- Python
- Streamlit
- Google Gemini API via `google-genai`
- `python-dotenv` for loading the API key from `.env`

## How to Run Locally

Run these commands from the project folder in Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in a text editor and set your Gemini API key:

```text
GEMINI_API_KEY=your_gemini_api_key
```

Keep the real key private. The `.env` file is ignored by Git and should never be committed.

Then start the app:

```powershell
streamlit run app.py
```
