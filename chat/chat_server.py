import json
import os
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env")
if not os.environ.get("OPENAI_API_KEY") and os.environ.get("open_ai_key"):
    os.environ["OPENAI_API_KEY"] = os.environ["open_ai_key"]

from references.agent_assembly import run_agent
from references.agent_init import get_agent
from references.sqlalchemy_models import MemoryBlock, get_session, init_default_blocks

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

STATIC_DIR = Path(__file__).parent / "static"
UPLOAD_DIR = Path(__file__).parent / "uploads"
CONVERSATION_LABEL = "conversation_log"


def _ensure_memory_blocks() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    session = get_session()
    init_default_blocks(session)
    session.close()


def _append_conversation(role: str, content: str, session_id: str) -> None:
    session = get_session()
    block = session.query(MemoryBlock).filter_by(label=CONVERSATION_LABEL).first()
    if not block:
        block = MemoryBlock(
            label=CONVERSATION_LABEL,
            content="No conversations recorded yet.",
            description="Rolling log of recent chat turns.",
            char_limit=6000,
            read_only=False,
        )
        session.add(block)
        session.commit()

    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"[{timestamp}] ({session_id}) {role}: {content}".strip()

    if block.content.strip() == "No conversations recorded yet.":
        updated = entry
    else:
        updated = f"{block.content}\n{entry}"

    if len(updated) > block.char_limit:
        # Keep the most recent content within the limit to avoid overflow.
        tail = updated[-block.char_limit :]
        updated = "[...truncated...]\n" + tail

    block.content = updated
    session.add(block)
    session.commit()
    session.close()


def _safe_filename(name: str) -> str:
    base = os.path.basename(name)
    base = base.replace(" ", "_")
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base)


def _extract_pdf_text(file_path: str, max_chars: int = 5000) -> str:
    """Extract text from PDF file."""
    if not PdfReader:
        return f"[PDF: {os.path.basename(file_path)} - PyPDF2 not installed]"
    
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            text = ""
            for page_num, page in enumerate(reader.pages):
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.extract_text()
        
        # Truncate if too long
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... PDF truncated, total {len(text)} chars ...]"
        
        return text
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"


def _parse_multipart(body: bytes, boundary: bytes) -> tuple[dict[str, str], dict[str, dict]]:
    fields: dict[str, str] = {}
    files: dict[str, dict] = {}

    boundary_marker = b"--" + boundary
    parts = body.split(boundary_marker)
    for part in parts:
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue

        header_blob, _, content = part.partition(b"\r\n\r\n")
        if not header_blob:
            continue

        headers: dict[str, str] = {}
        for line in header_blob.split(b"\r\n"):
            key, _, value = line.decode("utf-8", errors="ignore").partition(":")
            if key and value:
                headers[key.strip().lower()] = value.strip()

        disposition = headers.get("content-disposition", "")
        name_match = re.search(r"name=\"([^\"]+)\"", disposition)
        if not name_match:
            continue
        field_name = name_match.group(1)

        filename_match = re.search(r"filename=\"([^\"]+)\"", disposition)
        content = content.rstrip(b"\r\n")
        if filename_match:
            files[field_name] = {
                "filename": filename_match.group(1),
                "content": content,
                "content_type": headers.get("content-type", ""),
            }
        else:
            fields[field_name] = content.decode("utf-8", errors="ignore")

    return fields, files


def _handle_multipart(
    handler: BaseHTTPRequestHandler,
) -> tuple[str, str, str, str | None, int | None]:
    content_type = handler.headers.get("Content-Type", "")
    boundary_match = re.search(r"boundary=([^;]+)", content_type)
    if not boundary_match:
        raise ValueError("Invalid multipart data: boundary missing.")

    boundary = boundary_match.group(1).encode("utf-8")
    length = int(handler.headers.get("Content-Length", "0"))
    body = handler.rfile.read(length)

    fields, files = _parse_multipart(body, boundary)

    user_input = (fields.get("user_input") or "").strip()
    session_id = (fields.get("session_id") or "session").strip()
    user_id = (fields.get("user_id") or "web").strip()

    file_path = None
    file_size = None

    file_info = files.get("file")
    if file_info and file_info.get("filename"):
        filename = _safe_filename(file_info["filename"])
        if not filename.lower().endswith(".pdf"):
            raise ValueError("Only PDF files are allowed.")

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        stored_name = f"{session_id}_{timestamp}_{filename}"
        file_path = str(UPLOAD_DIR / stored_name)

        content = file_info.get("content", b"")
        with open(file_path, "wb") as out_file:
            out_file.write(content)
        file_size = len(content)

    return user_input, session_id, user_id, file_path, file_size


class ChatHandler(BaseHTTPRequestHandler):
    agent = get_agent()

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/" or self.path == "/index.html":
            html = (STATIC_DIR / "chat.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return

        if self.path == "/chat.css":
            css = (STATIC_DIR / "chat.css").read_bytes()
            self._send(200, css, "text/css; charset=utf-8")
            return

        if self.path == "/chat.js":
            js = (STATIC_DIR / "chat.js").read_bytes()
            self._send(200, js, "application/javascript; charset=utf-8")
            return

        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return

        content_type = self.headers.get("Content-Type", "")
        file_path = None
        file_size = None

        if content_type.startswith("multipart/form-data"):
            try:
                user_input, session_id, user_id, file_path, file_size = _handle_multipart(self)
            except ValueError as exc:
                self._send(400, str(exc).encode("utf-8"), "text/plain; charset=utf-8")
                return
        else:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._send(400, b"Invalid JSON", "text/plain; charset=utf-8")
                return

            user_input = (payload.get("user_input") or "").strip()
            session_id = (payload.get("session_id") or "session").strip()
            user_id = (payload.get("user_id") or "web").strip()

        if not user_input and not file_path:
            self._send(400, b"Empty message", "text/plain; charset=utf-8")
            return

        if user_input:
            _append_conversation("user", user_input, session_id)
        
        pdf_content = None
        if file_path:
            file_note = f"User uploaded PDF: {os.path.basename(file_path)}"
            if file_size is not None:
                file_note += f" ({file_size} bytes)"
            _append_conversation("user", file_note, session_id)
            
            # Extract PDF content once and reuse
            pdf_content = _extract_pdf_text(file_path)
            pdf_memory_entry = f"📄 PDF Content from {os.path.basename(file_path)}:\n{pdf_content}"
            _append_conversation("system", pdf_memory_entry, session_id)

        agent_input = user_input or "User uploaded a PDF for context."
        if pdf_content:
            agent_input = f"{agent_input}\n\n📄 PDF Content:\n{pdf_content}"

        try:
            result = run_agent(
                agent=self.agent,
                user_input=agent_input,
                session_id=session_id,
                user_id=user_id,
            )
            print(f'agent = {self.agent}, user_input={agent_input},session_id={session_id},user_id={user_id}')
        
        except Exception as e:
            print(f"❌ Erro ao executar agente: {e}")
            import traceback
            traceback.print_exc()
            assistant_reply = f"Erro ao processar: {str(e)}"
            _append_conversation("assistant", assistant_reply, session_id)
            response = json.dumps(
                {"assistant": assistant_reply, "session_id": session_id}
            ).encode("utf-8")
            self._send(200, response, "application/json; charset=utf-8")
            return

        assistant_reply = result.get("messages", []) if isinstance(result, dict) else []
        assistant_reply = "\n".join(
            msg.get("content", "") for msg in assistant_reply if isinstance(msg, dict) and msg.get("role") == "assistant"
        ).strip()
        _append_conversation("assistant", assistant_reply, session_id)

        response = json.dumps(
            {"assistant": assistant_reply, "session_id": session_id}
        ).encode("utf-8")
        self._send(200, response, "application/json; charset=utf-8")


def run_server() -> None:
    _ensure_memory_blocks()
    host = os.environ.get("CHAT_HOST", "127.0.0.1")
    port = int(os.environ.get("CHAT_PORT", "8000"))

    server = ThreadingHTTPServer((host, port), ChatHandler)
    print(f"Chat server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
