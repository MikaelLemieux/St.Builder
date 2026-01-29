# Streamlit Builder (Django)

This Django app lets users describe Streamlit apps in a chat panel, generates code with an LLM, and lets them download the resulting codebase.

## Features
- Chat-driven app creation.
- Live code preview.
- Downloadable Streamlit app bundle.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Environment variables
- `OPENAI_API_KEY`: Required to enable LLM generation.
- `OPENAI_MODEL`: Optional. Defaults to `gpt-4o-mini`.
- `DJANGO_DEBUG`: Defaults to `true`.
- `DJANGO_ALLOWED_HOSTS`: Defaults to `localhost,127.0.0.1`.
