import os
import sys
import json
import re
import urllib.request
import urllib.parse
import ssl
import subprocess

def log(msg):
    print(f"[OpenSpec Orchestrator] {msg}", flush=True)

# 1. Environment & Event Parsing
linear_api_key = os.environ.get("LINEAR_API_KEY", "").strip()
gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
github_repository = os.environ.get("GITHUB_REPOSITORY", "")
input_ticket_id = os.environ.get("INPUT_TICKET_ID", "").strip()
input_comment_body = os.environ.get("INPUT_COMMENT_BODY", "").strip()
input_comment_id = os.environ.get("INPUT_COMMENT_ID", "").strip()

event_payload_str = os.environ.get("EVENT_PAYLOAD", "{}")
try:
    event_payload = json.loads(event_payload_str)
except Exception:
    event_payload = {}

ticket_id = input_ticket_id
comment_body = input_comment_body

if not ticket_id:
    client_payload = event_payload.get("client_payload", {})
    inputs_payload = event_payload.get("inputs", {})
    ticket_id = (
        client_payload.get("ticket_id")
        or client_payload.get("issue_id")
        or inputs_payload.get("issue_id")
        or inputs_payload.get("ticket_id")
        or client_payload.get("data", {}).get("issue", {}).get("identifier")
        or client_payload.get("data", {}).get("issueId")
        or ""
    )
    comment_body = (
        comment_body
        or client_payload.get("comment_body")
        or client_payload.get("comment")
        or inputs_payload.get("comment")
        or client_payload.get("data", {}).get("body")
        or ""
    )

if not linear_api_key:
    log("ERROR: LINEAR_API_KEY secret is missing in GitHub Secrets.")
    sys.exit(1)

if not gemini_api_key:
    log("ERROR: GEMINI_API_KEY secret is missing in GitHub Secrets.")
    sys.exit(1)

# SSL Context
ctx = ssl._create_unverified_context()

# 2. Linear GraphQL Helper
def query_linear(query, variables=None):
    url = "https://api.linear.app/graphql"
    headers = {
        "Authorization": linear_api_key,
        "Content-Type": "application/json"
    }
    data = {"query": query}
    if variables:
        data["variables"] = variables
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, context=ctx) as resp:
        return json.loads(resp.read().decode("utf-8"))

def post_linear_comment(issue_uuid, comment_markdown):
    comment_mutation = """
    mutation CommentCreate($input: CommentCreateInput!) {
      commentCreate(input: $input) {
        success
      }
    }
    """
    try:
        res = query_linear(comment_mutation, {
            "input": {
                "issueId": issue_uuid,
                "body": comment_markdown
            }
        })
        return res.get("data", {}).get("commentCreate", {}).get("success", False)
    except Exception as e:
        log(f"Error posting comment to Linear: {e}")
        return False

# Fallback: If ticket_id is missing but comment_id is present, resolve issue from comment
if not ticket_id and input_comment_id:
    log(f"Resolving ticket ID from comment_id: {input_comment_id}...")
    get_comment_issue_query = """
    query GetCommentIssue($commentId: String!) {
      comment(id: $commentId) {
        issue {
          id
          identifier
        }
      }
    }
    """
    try:
        res_comment_issue = query_linear(get_comment_issue_query, {"commentId": input_comment_id})
        resolved_issue = res_comment_issue.get("data", {}).get("comment", {}).get("issue")
        if resolved_issue:
            ticket_id = resolved_issue.get("identifier") or resolved_issue.get("id")
            log(f"Resolved ticket ID: {ticket_id}")
    except Exception as e:
        log(f"Error resolving comment_id: {e}")

if not ticket_id:
    log("ERROR: No Ticket ID provided in input or payload, and could not resolve from comment_id.")
    sys.exit(1)

log(f"Processing Ticket ID: {ticket_id}")
log(f"Trigger Comment: {comment_body}")

# Fetch Ticket Details
get_issue_query = """
query GetIssue($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    priority
    priorityLabel
    state { name }
    team { key name }
    project { name }
    url
  }
}
"""

res_linear = query_linear(get_issue_query, {"id": ticket_id})
issue_data = res_linear.get("data", {}).get("issue")

if not issue_data:
    log(f"ERROR: Could not find Linear issue for ID '{ticket_id}'. Response: {res_linear}")
    sys.exit(1)

issue_uuid = issue_data.get("id")
identifier = issue_data.get("identifier")
title = issue_data.get("title", "")
description = issue_data.get("description", "Sin descripción provista.")
priority_label = issue_data.get("priorityLabel", "Normal")
project_name = issue_data.get("project", {}).get("name", "N/A") if issue_data.get("project") else "N/A"

log(f"Fetched Ticket [{identifier}]: {title}")

# 3. Create Git Branch
def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text[:40]

branch_name = f"feat-{identifier.lower()}-{slugify(title)}"
log(f"Target Branch Name: {branch_name}")

try:
    subprocess.run(["git", "fetch", "origin"], check=True)
    res_dev = subprocess.run(["git", "rev-parse", "--verify", "origin/dev"], capture_output=True)
    base_branch = "dev" if res_dev.returncode == 0 else "main"
    log(f"Base branch selected: {base_branch}")

    subprocess.run(["git", "checkout", "-B", branch_name, f"origin/{base_branch}"], check=True)
except Exception as e:
    log(f"Warning during git branch checkout: {e}")

# 4. Generate OpenSpec via Gemini API using gemini-3.5-flash
log("Calling Gemini API (model: gemini-3.5-flash) to generate OpenSpec...")

prompt = f"""
Eres un Arquitecto de Software Senior especializado en la metodología OpenSpec y en la plataforma AutoERP.

Stack del Proyecto:
- Backend (BE): Python 3.10+, FastAPI, SQLAlchemy, Alembic, PostgreSQL, Pydantic.
- Frontend (FE): React 18+, Vite, JavaScript, Tailwind CSS.

Instrucciones:
Analiza el siguiente ticket de Linear y genera 3 documentos en formato Markdown dentro de una estructura JSON válida:
1. "proposal": Propuesta técnica del cambio (Contexto, Impacto en BE/FE, Cambios en DB/API, Riesgos).
2. "spec": Especificación de requerimientos funcionales y no funcionales, contratos de datos API JSON (Pydantic / React interfaces), y criterios de aceptación.
3. "tasks": Lista detallada de tareas accionables paso a paso con casillas de verificación markdown (- [ ] Tarea).

Ticket Details:
- ID: {identifier}
- Título: {title}
- Prioridad: {priority_label}
- Proyecto: {project_name}
- Descripción:
{description}

Responde ÚNICAMENTE con un objeto JSON válido con la siguiente clave y estructura (sin etiquetas de bloque ```json alrededor):
{{
  "proposal": "# Propuesta...",
  "spec": "# Especificación...",
  "tasks": "# Tareas..."
}}
"""

def call_gemini_strict(prompt_text):
    model = "gemini-3.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"}
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return text
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise Exception(f"Error HTTP {e.code} con modelo {model}: {err_body}")
    except Exception as e:
        raise Exception(f"Error con modelo {model}: {str(e)}")

try:
    gemini_output_raw = call_gemini_strict(prompt)
except Exception as e:
    error_msg = str(e)
    log(f"CRITICAL ERROR in Gemini API call: {error_msg}")
    
    # Report error to Linear comment so user is notified immediately
    err_comment_markdown = f"""⚠️ **Error en OpenSpec Orchestrator**

No se pudo generar la especificación técnica para el ticket **[{identifier}]({issue_data.get('url')})**.

❌ **Detalle del Error (Modelo: `gemini-3.5-flash`):**
```
{error_msg}
```

💡 *Por favor revisa la configuración de GEMINI_API_KEY o el nombre del modelo en Google AI Studio.*
"""
    post_linear_comment(issue_uuid, err_comment_markdown)
    sys.exit(1)

try:
    openspec_json = json.loads(gemini_output_raw)
except Exception as e:
    log(f"JSON parsing fallback: {e}")
    clean_raw = re.sub(r"^```json\s*", "", gemini_output_raw.strip(), flags=re.MULTILINE)
    clean_raw = re.sub(r"```$", "", clean_raw.strip(), flags=re.MULTILINE)
    openspec_json = json.loads(clean_raw)

proposal_content = openspec_json.get("proposal", f"# Proposal for {identifier}\n\n{title}")
spec_content = openspec_json.get("spec", f"# Spec for {identifier}\n\n{title}")
tasks_content = openspec_json.get("tasks", f"# Tasks for {identifier}\n\n- [ ] Implementar {title}")

# 5. Write OpenSpec files
target_dir = os.path.join("openspec", "changes", identifier)
os.makedirs(target_dir, exist_ok=True)

with open(os.path.join(target_dir, "proposal.md"), "w", encoding="utf-8") as f:
    f.write(proposal_content.strip() + "\n")

with open(os.path.join(target_dir, "spec.md"), "w", encoding="utf-8") as f:
    f.write(spec_content.strip() + "\n")

with open(os.path.join(target_dir, "tasks.md"), "w", encoding="utf-8") as f:
    f.write(tasks_content.strip() + "\n")

log(f"OpenSpec files created in {target_dir}/")

# 6. Post Success Comment on Linear
spec_url_base = f"https://github.com/{github_repository}/tree/{branch_name}/openspec/changes/{identifier}"

success_comment_markdown = f"""🤖 **OpenSpec generado con éxito**

Se ha creado la especificación técnica para el ticket **[{identifier}]({issue_data.get('url')})** en la rama `{branch_name}`.

📄 **Archivos de especificación creados:**
- [`proposal.md`]({spec_url_base}/proposal.md)
- [`spec.md`]({spec_url_base}/spec.md)
- [`tasks.md`]({spec_url_base}/tasks.md)

🚀 **Siguiente paso:** El Agente de IA puede consultar esta rama para iniciar la implementación según el protocolo OpenSpec.
"""

post_linear_comment(issue_uuid, success_comment_markdown)
log("OpenSpec generation workflow script completed successfully.")
