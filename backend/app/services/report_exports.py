from __future__ import annotations

import csv
import html
import io
import json
from typing import Any


def full_csv(payload: dict[str, Any]) -> str:
    """Flatten every report section into one portable CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["section", "record", "field", "value"])
    writer.writeheader()
    for section, value in payload.items():
        if isinstance(value, list):
            for index, record in enumerate(value, 1):
                if isinstance(record, dict):
                    for field, cell in record.items():
                        writer.writerow({"section": section, "record": index, "field": field, "value": _cell(cell)})
                else:
                    writer.writerow({"section": section, "record": index, "field": "value", "value": _cell(record)})
        elif isinstance(value, dict):
            for field, cell in value.items():
                writer.writerow({"section": section, "record": 1, "field": field, "value": _cell(cell)})
        else:
            writer.writerow({"section": section, "record": 1, "field": "value", "value": _cell(value)})
    return output.getvalue()


def _cell(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return "Not available"
    return str(value)


def full_html(report_date: str, payload: dict[str, Any]) -> str:
    sections = []
    for name, value in payload.items():
        title = name.replace("_", " ").title()
        if isinstance(value, list):
            body = _table(value)
        elif isinstance(value, dict):
            body = _table([value])
        else:
            body = f"<p>{html.escape(str(value))}</p>"
        sections.append(f"<section><h2>{html.escape(title)}</h2>{body}</section>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>SignalScope - {html.escape(report_date)}</title><style>
body{{font-family:Arial,sans-serif;color:#172426;margin:32px;line-height:1.45}}h1{{font-size:32px}}h2{{margin-top:32px;border-bottom:2px solid #0c6f69;padding-bottom:6px}}table{{width:100%;border-collapse:collapse;font-size:12px;margin:12px 0}}th,td{{border:1px solid #dce2dd;padding:7px;vertical-align:top;text-align:left}}th{{background:#edf5f2}}a{{color:#0c6f69}}.notice{{background:#fff9e8;border-left:4px solid #e3b341;padding:12px}}@media print{{body{{margin:12mm}}section{{break-inside:avoid}}}}
</style></head><body><h1>SignalScope</h1><p><b>Daily intelligence report: {html.escape(report_date)}</b></p><p class="notice">Observed within the monitored sample. Coverage is not exhaustive.</p>{''.join(sections)}</body></html>"""


def _table(records: list[Any]) -> str:
    dictionaries = [x for x in records if isinstance(x, dict)]
    if not dictionaries:
        return "<p>Not available in the supplied dataset.</p>"
    fields: list[str] = []
    for record in dictionaries:
        for field in record:
            if field not in fields:
                fields.append(field)
    head = "".join(f"<th>{html.escape(x.replace('_', ' ').title())}</th>" for x in fields)
    rows = []
    for record in dictionaries:
        cells = []
        for field in fields:
            raw = record.get(field)
            escaped = html.escape(_cell(raw))
            if field == "url" and raw:
                escaped = f'<a href="{html.escape(str(raw), quote=True)}">Open on TikTok</a>'
            cells.append(f"<td>{escaped}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return f"<div style='overflow:auto'><table><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"

