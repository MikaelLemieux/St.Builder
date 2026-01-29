import io
import json
import textwrap
import zipfile
from datetime import datetime

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

SYSTEM_PROMPT = """
You are a senior Streamlit engineer. Generate Streamlit app code and guidance.
Return a JSON object with keys:
- assistant_reply: short response for the user
- streamlit_code: full Python code for streamlit app
- requirements: list of pip requirements (strings)
- notes: optional list of usage notes
""".strip()

DEFAULT_CODE = textwrap.dedent(
    """
    import streamlit as st

    st.set_page_config(page_title="Streamlit Builder", layout="wide")
    st.title("Your Streamlit App")
    st.write("Describe the app you want on the left to generate code.")
    """
).strip()


def home(request):
    session_state = request.session.get('builder_state', {})
    context = {
        'messages': session_state.get('messages', []),
        'streamlit_code': session_state.get('streamlit_code', DEFAULT_CODE),
    }
    return render(request, 'home.html', context)


@require_POST
@ensure_csrf_cookie
def chat(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    user_message = (payload.get('message') or '').strip()
    if not user_message:
        return JsonResponse({'error': 'Message is required.'}, status=400)

    session_state = request.session.get('builder_state', {'messages': []})
    messages = session_state.get('messages', [])
    messages.append({'role': 'user', 'content': user_message})

    assistant_reply, streamlit_code, requirements, notes = generate_response(messages)

    messages.append({'role': 'assistant', 'content': assistant_reply})
    session_state['messages'] = messages
    session_state['streamlit_code'] = streamlit_code
    session_state['requirements'] = requirements
    session_state['notes'] = notes
    request.session['builder_state'] = session_state

    return JsonResponse({
        'assistant_reply': assistant_reply,
        'streamlit_code': streamlit_code,
        'requirements': requirements,
        'notes': notes,
    })


@ensure_csrf_cookie
def download_bundle(request):
    session_state = request.session.get('builder_state', {})
    streamlit_code = session_state.get('streamlit_code', DEFAULT_CODE)
    requirements = session_state.get('requirements', ['streamlit'])
    notes = session_state.get('notes', [])

    readme = build_readme(notes)

    buffer = io.BytesIO()
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('app.py', streamlit_code)
        archive.writestr('requirements.txt', '\n'.join(requirements) + '\n')
        archive.writestr('README.md', readme)

    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="streamlit_app_{timestamp}.zip"'
    return response


def generate_response(messages):
    if not settings.OPENAI_API_KEY:
        reply = (
            "Add an OPENAI_API_KEY to enable live generation. "
            "Here is a starter template you can build on."
        )
        return reply, DEFAULT_CODE, ['streamlit'], ["Set OPENAI_API_KEY to enable AI code generation."]

    chat_payload = {
        'model': settings.OPENAI_MODEL,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            *messages,
        ],
        'temperature': 0.2,
    }

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {settings.OPENAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json=chat_payload,
            timeout=45,
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
    except (requests.RequestException, KeyError, IndexError) as exc:
        reply = f"Unable to reach OpenAI ({exc}). Showing the last known template."
        return reply, DEFAULT_CODE, ['streamlit'], ["Check your OpenAI API key and network."]

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = {
            'assistant_reply': 'Here is the generated Streamlit code based on your request.',
            'streamlit_code': content,
            'requirements': ['streamlit'],
            'notes': [],
        }

    assistant_reply = parsed.get('assistant_reply', 'Here is the updated Streamlit app.')
    streamlit_code = parsed.get('streamlit_code', DEFAULT_CODE)
    requirements = parsed.get('requirements', ['streamlit'])
    notes = parsed.get('notes', [])

    return assistant_reply, streamlit_code, requirements, notes


def build_readme(notes):
    notes_block = '\n'.join(f"- {note}" for note in notes) if notes else "- Generated with Streamlit Builder"
    return textwrap.dedent(
        f"""
        # Streamlit App

        ## Run locally
        ```bash
        python -m venv .venv
        source .venv/bin/activate
        pip install -r requirements.txt
        streamlit run app.py
        ```

        ## Notes
        {notes_block}
        """
    ).strip()
