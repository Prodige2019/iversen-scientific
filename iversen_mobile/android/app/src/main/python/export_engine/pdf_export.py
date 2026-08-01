"""
Export PDF d'une correction — reprend l'identité visuelle de la maquette
(encre bleu-nuit, accent rouge pour les remarques, doré pour la note).
"""
import os
import tempfile
from typing import Any, Dict

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, KeepTogether,
)
from reportlab.lib.enums import TA_RIGHT

from .latex_render import render_latex_to_png

INK = colors.HexColor("#1B2A45")
INK_SOFT = colors.HexColor("#4B5A73")
RED = colors.HexColor("#B23A2F")
GOLD = colors.HexColor("#8A6A15")
GREEN = colors.HexColor("#3E7A52")


def _styles():
    ss = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=ss["Title"], textColor=INK, fontSize=18, spaceAfter=2),
        "subject": ParagraphStyle("subject", parent=ss["Normal"], textColor=INK_SOFT, fontSize=10.5, spaceAfter=14),
        "step_title": ParagraphStyle("step_title", parent=ss["Heading3"], textColor=INK, fontSize=12, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("body", parent=ss["Normal"], textColor=INK_SOFT, fontSize=10, leading=14),
        "warning": ParagraphStyle("warning", parent=ss["Normal"], textColor=colors.HexColor("#8A3B2F"), fontSize=9, leading=12),
        "score": ParagraphStyle("score", parent=ss["Normal"], textColor=GOLD, fontSize=16, alignment=TA_RIGHT, fontName="Helvetica-Bold"),
        "footer": ParagraphStyle("footer", parent=ss["Normal"], textColor=INK_SOFT, fontSize=8, alignment=TA_RIGHT),
    }


def _math_flowable(latex_str: str, tmpdir: str, idx: int, max_width_mm: float = 150) -> RLImage:
    path = os.path.join(tmpdir, f"formula_{idx}.png")
    render_latex_to_png(latex_str, path)
    img = RLImage(path)
    max_w = max_width_mm * mm
    if img.imageWidth > max_w:
        ratio = max_w / img.imageWidth
        img.drawWidth = max_w
        img.drawHeight = img.imageHeight * ratio
    else:
        img.drawWidth = img.imageWidth
        img.drawHeight = img.imageHeight
    return img


def export_correction_to_pdf(correction: Dict[str, Any], output_path: str) -> None:
    """Génère un PDF à partir du dict produit par engine.correction_to_dict()."""
    styles = _styles()

    with tempfile.TemporaryDirectory() as tmpdir:
        doc = SimpleDocTemplate(
            output_path, pagesize=A4,
            topMargin=20 * mm, bottomMargin=18 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
        )
        story = []

        header_table = Table(
            [[
                Paragraph(correction.get("exercise_title", "Correction"), styles["title"]),
                Paragraph(f"{correction.get('score', '')}/{correction.get('score_max', 20)}", styles["score"]),
            ]],
            colWidths=[130 * mm, 40 * mm],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(header_table)

        subject_line = correction.get("subject_line") or f"f(x) = {correction.get('function_str', '')}"
        story.append(Paragraph(subject_line.replace("$", ""), styles["subject"]))
        story.append(Spacer(1, 4 * mm))

        img_idx = 0
        for i, step in enumerate(correction.get("steps", []), start=1):
            block = []
            block.append(Paragraph(f"Étape {i} — {step['title']}", styles["step_title"]))

            if step.get("result_latex"):
                img_idx += 1
                try:
                    block.append(_math_flowable(step["result_latex"], tmpdir, img_idx))
                    block.append(Spacer(1, 2 * mm))
                except Exception:
                    block.append(Paragraph(step["result_latex"], styles["body"]))

            if step.get("explanation"):
                block.append(Paragraph(step["explanation"], styles["body"]))

            if step.get("rule_recalled"):
                img_idx += 1
                try:
                    rule_img = _math_flowable(step["rule_recalled"], tmpdir, img_idx, max_width_mm=140)
                    rule_table = Table([[rule_img]], colWidths=[150 * mm])
                    rule_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF3F0")),
                        ("BOX", (0, 0), (-1, -1), 0.5, GREEN),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]))
                    block.append(Spacer(1, 1.5 * mm))
                    block.append(rule_table)
                except Exception:
                    pass

            if step.get("warning"):
                block.append(Spacer(1, 1.5 * mm))
                warn_table = Table([[Paragraph("⚠ " + step["warning"], styles["warning"])]], colWidths=[150 * mm])
                warn_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7E9E7")),
                    ("BOX", (0, 0), (-1, -1), 0.5, RED),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                block.append(warn_table)

            block.append(Spacer(1, 4 * mm))
            story.append(KeepTogether(block))

        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(
            "Iversen Scientific — correction générée automatiquement (moteur symbolique, sans IA générative)",
            styles["footer"],
        ))

        doc.build(story)
