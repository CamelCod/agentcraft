"""
Assembles and exports reports in multiple formats.
Every claim includes source URL, timestamp, transcript excerpt, and confidence score.
"""
import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.config import get_settings
from app.core.storage import upload_bytes
from app.services import graph_service as graph
from app.services.llm import call_llm

settings = get_settings()

TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "reports"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=False,
    )


def _generate_executive_summary(report_data: dict) -> str:
    claims_text = "\n".join(
        f"- {c['claim_text']} (confidence: {c['confidence_score']:.2f})"
        for c in report_data["sections"]["verified_claims"][:20]
    )
    prompt = f"""Write a 150-word executive summary for a knowledge extraction report.

Creator: {report_data['creator']['channel_name']}
Videos analyzed: {report_data['config']['total_videos_analyzed']}
Verified claims count: {len(report_data['sections']['verified_claims'])}
Top claims:
{claims_text}

Return only the summary text, no headers."""
    try:
        return call_llm(prompt, model=settings.llm_report_model, max_tokens=300)
    except Exception:
        return (
            f"This report analyzes {report_data['config']['total_videos_analyzed']} videos "
            f"from {report_data['creator']['channel_name']}, extracting "
            f"{len(report_data['sections']['verified_claims'])} verified knowledge claims."
        )


def assemble_report(
    project_id: str,
    report_id: str,
    config: dict,
    creator_meta: dict,
    videos: list[dict],
) -> dict:
    """
    Builds the full report data structure from Neo4j claims.
    """
    confidence_threshold = config.get("confidence_threshold", 0.65)
    selected_domains = config.get("domains", [])

    all_claims = graph.get_project_claims(project_id)

    verified_claims = []
    contradictions = []

    for c in all_claims:
        if c.get("confidence_score", 0) < confidence_threshold:
            continue
        if selected_domains and c.get("domain") not in selected_domains:
            continue
        if c.get("verification_status") not in ("verified", "contradicted"):
            continue

        # Build citations from evidence
        citations = []
        for ev in c.get("evidence", []):
            if not ev.get("youtube_id"):
                continue
            yt_id = ev["youtube_id"]
            start = ev.get("start_time", 0)
            video_info = next((v for v in videos if v.get("youtube_id") == yt_id), {})
            citations.append({
                "video_title": video_info.get("title", "Unknown"),
                "youtube_id": yt_id,
                "published_date": video_info.get("published_at", ""),
                "start_time": start,
                "end_time": ev.get("end_time", start),
                "timestamp_url": f"https://www.youtube.com/watch?v={yt_id}&t={int(start)}s",
                "transcript_excerpt": ev.get("excerpt", ""),
            })

        claim_entry = {
            "claim_text": c["text"],
            "domain": c.get("domain", ""),
            "confidence_score": round(float(c.get("confidence_score", 0)), 3),
            "occurrences": c.get("occurrence_count", 1),
            "citations": citations,
        }

        if c.get("verification_status") == "verified":
            verified_claims.append(claim_entry)

    # Build source appendix
    cited_yt_ids = set()
    for c in verified_claims:
        for cit in c["citations"]:
            cited_yt_ids.add(cit["youtube_id"])

    source_appendix = [
        {
            "video_title": v.get("title", ""),
            "youtube_id": v.get("youtube_id", ""),
            "youtube_url": f"https://www.youtube.com/watch?v={v.get('youtube_id', '')}",
            "published_date": str(v.get("published_at", "")),
            "duration": _format_duration(v.get("duration_seconds", 0)),
            "claims_cited": sum(
                1 for c in verified_claims
                for cit in c["citations"]
                if cit["youtube_id"] == v.get("youtube_id")
            ),
        }
        for v in videos
        if v.get("youtube_id") in cited_yt_ids
    ]

    report_data = {
        "report_id": report_id,
        "project_id": project_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "creator": creator_meta,
        "config": {
            "domains": selected_domains,
            "confidence_threshold": confidence_threshold,
            "total_videos_analyzed": len(videos),
        },
        "sections": {
            "verified_claims": verified_claims,
            "contradictions": contradictions,
            "source_appendix": source_appendix,
            "executive_summary": "",
        },
    }

    report_data["sections"]["executive_summary"] = _generate_executive_summary(report_data)

    return report_data


def export_json(report_data: dict) -> bytes:
    return json.dumps(report_data, ensure_ascii=False, indent=2).encode("utf-8")


def export_markdown(report_data: dict) -> bytes:
    env = _get_jinja_env()
    tpl = env.get_template("report.md.j2")
    return tpl.render(**report_data).encode("utf-8")


def export_html(report_data: dict) -> bytes:
    env = _get_jinja_env()
    tpl = env.get_template("report.html.j2")
    return tpl.render(**report_data).encode("utf-8")


def export_pdf(html_bytes: bytes) -> bytes:
    from weasyprint import HTML, CSS
    return HTML(string=html_bytes.decode("utf-8")).write_pdf(
        stylesheets=[CSS(string="@page { size: A4; margin: 2cm; }")]
    )


def export_docx(report_data: dict) -> bytes:
    from docx import Document
    from docx.shared import Pt
    from io import BytesIO

    doc = Document()
    doc.add_heading(f"Report: {report_data['creator']['channel_name']}", 0)
    doc.add_paragraph(f"Generated: {report_data['generated_at'][:10]}")
    doc.add_heading("Executive Summary", 1)
    doc.add_paragraph(report_data["sections"]["executive_summary"])
    doc.add_heading("Verified Claims", 1)
    for claim in report_data["sections"]["verified_claims"]:
        doc.add_heading(claim["claim_text"][:100], 3)
        doc.add_paragraph(f"Confidence: {claim['confidence_score']} | Domain: {claim['domain']}")
        for cit in claim["citations"]:
            p = doc.add_paragraph()
            p.add_run(f'  "{cit["transcript_excerpt"][:200]}"').italic = True
            p.add_run(f'\n  — {cit["video_title"]}, {cit["published_date"]}, {cit["timestamp_url"]}')
    doc.add_heading("Sources", 1)
    for src in report_data["sections"]["source_appendix"]:
        doc.add_paragraph(f"{src['video_title']} — {src['youtube_url']}")
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def upload_all_formats(report_data: dict, report_id: str, project_id: str, formats: list[str]) -> dict[str, str]:
    """Exports requested formats and uploads to MinIO. Returns {format: storage_key}."""
    keys: dict[str, str] = {}
    prefix = f"reports/{project_id}/{report_id}"

    if "json" in formats:
        key = f"{prefix}/json/report.json"
        upload_bytes(settings.minio_bucket_reports, key, export_json(report_data), "application/json")
        keys["json"] = key

    if "markdown" in formats or "md" in formats:
        key = f"{prefix}/md/report.md"
        upload_bytes(settings.minio_bucket_reports, key, export_markdown(report_data), "text/markdown")
        keys["markdown"] = key

    html_bytes = None
    if "html" in formats or "pdf" in formats:
        html_bytes = export_html(report_data)

    if "html" in formats:
        key = f"{prefix}/html/report.html"
        upload_bytes(settings.minio_bucket_reports, key, html_bytes, "text/html")
        keys["html"] = key

    if "pdf" in formats and html_bytes:
        try:
            key = f"{prefix}/pdf/report.pdf"
            upload_bytes(settings.minio_bucket_reports, key, export_pdf(html_bytes), "application/pdf")
            keys["pdf"] = key
        except Exception as e:
            keys["pdf_error"] = str(e)

    if "docx" in formats:
        try:
            key = f"{prefix}/docx/report.docx"
            upload_bytes(settings.minio_bucket_reports, key, export_docx(report_data),
                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            keys["docx"] = key
        except Exception as e:
            keys["docx_error"] = str(e)

    return keys


def _format_duration(seconds: int | None) -> str:
    if not seconds:
        return "0:00"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
