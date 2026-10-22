"""Portable, self-contained report formats; all dynamic HTML/XML is escaped."""

import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def json_report(results):
    return json.dumps({"schema_version": 1, "results": [result.to_dict() for result in results]},
                      indent=2, sort_keys=True, allow_nan=False) + "\n"


def junit_report(results):
    root = ET.Element("testsuites")
    for result in results:
        suite = ET.SubElement(root, "testsuite", name=result.adapter,
                              tests=str(len(result.outcomes)),
                              failures=str(sum(not item["passed"] for item in result.outcomes)))
        for item in result.outcomes:
            case = ET.SubElement(suite, "testcase", classname=item["case"], name=str(item["probe"]))
            if not item["passed"]:
                ET.SubElement(case, "failure", message=item["error"] or "oracle mismatch").text = json.dumps(item)
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def html_report(results):
    sections = []
    for result in results:
        metrics = "".join(
            f"<tr><th>{html.escape(name)}</th><td>{metric.numerator}/{metric.denominator}</td>"
            f"<td>{'n/a' if metric.value is None else format(metric.value, '.3f')}</td></tr>"
            for name, metric in result.metrics.items())
        sections.append(f"<section><h2>{html.escape(result.adapter)}</h2>"
                        f"<p>{'PASS' if result.passed else 'FAIL'} · {len(result.outcomes)} probes</p>"
                        "<table><thead><tr><th>Metric</th><th>Count</th><th>Value</th></tr></thead>"
                        f"<tbody>{metrics}</tbody></table><details><summary>Probe evidence</summary>"
                        f"<pre>{html.escape(json.dumps(result.outcomes, indent=2))}</pre></details></section>")
    return ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'\">"
            "<title>Memory Integrity Lab report</title><style>"
            "body{font:16px system-ui;max-width:980px;margin:3rem auto;padding:0 1rem;color:#172133}"
            "table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:.5rem;border-bottom:1px solid #ccc}"
            "pre{overflow:auto;background:#f5f6f8;padding:1rem}section{margin:2rem 0}"
            "</style><h1>Memory Integrity Lab</h1><p>Synthetic engineering regression results. "
            "The naive control is expected to fail. Timing values depend on the host.</p>"
            + "".join(sections) + "</html>\n")


def write_reports(results, directory):
    results = tuple(results)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, renderer in (("report.json", json_report), ("report.xml", junit_report),
                           ("report.html", html_report)):
        (directory / name).write_text(renderer(results), encoding="utf-8")
