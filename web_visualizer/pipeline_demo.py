"""Adapt the standalone demo's renderer to the visualizer's shared workspace.

Keep algorithm scenes in their source module rather than maintaining a second
copy of the large renderer. All DOM lookups and styles stay inside the demo.
"""
import re
import colorsys
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
from functools import lru_cache

DEMO_PATH = Path(__file__).resolve().parents[1] / "methods/main_method/interactive_pipeline_demo.py"


@lru_cache(maxsize=1)
def _load_demo(path, version):
    spec = importlib.util.spec_from_file_location("visualizer_pipeline_source", path)
    module = importlib.util.module_from_spec(spec)
    # Read source directly so rapid edits cannot hit a stale Python bytecode file.
    exec(compile(path.read_text(encoding="utf-8-sig"), str(path), "exec"), module.__dict__)
    return module


def demo_module():
    return _load_demo(DEMO_PATH, DEMO_PATH.stat().st_mtime_ns)


def demo_defaults():
    class Inputs(HTMLParser):
        def __init__(self):
            super().__init__()
            self.values = {}

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "input" and "id" in attrs:
                self.values[attrs["id"]] = attrs.get("value", "")

    inputs = Inputs()
    inputs.feed(demo_module().PAGE)
    return {
        "clusters": inputs.values.get("custom-k", "6"),
        "lambda": inputs.values.get("lambda", "0.6"),
        "cosineThreshold": inputs.values.get("cosine-threshold", "0.35"),
    }


def demo_script():
    script = re.search(r"<script>(.*?)</script>", demo_module().PAGE, re.S).group(1)
    script = script.replace(
        "const $=id=>document.getElementById(id);",
        "const root=document.querySelector('#interactiveDemo');"
        "const $=id=>root.querySelector('#'+CSS.escape(id));",
    )
    script = script.replace("resetSample();$('add-doc').onclick=()=>addDoc('');$('sample').onclick=resetSample;", "")
    # The host handles shared input, uploads, requests and keyboard shortcuts.
    script = re.sub(r"^document\.addEventListener\('keydown'.*$", "", script, flags=re.M)
    script = script[:script.index("$('run').onclick=async")]
    enhancements = (Path(__file__).parent / "static" / "demo_enhancements.js").read_text(encoding="utf-8")
    bridge = """
window.PipelineDemo = {
  sample: () => SAMPLE.slice(),
  stepCounts: () => ({source: flowSteps.length - 1, total: flowSteps.length}),
  stop: () => { flowStop(); kmLessonStopTimer(); if (typeof kmMoveStopTimer === "function") kmMoveStopTimer(); },
  move: direction => { if (DATA) { flowStop(); flowGo(flowIndex + direction); } },
  load: payload => {
    flowStop(); kmLessonStopTimer(); if (typeof kmMoveStopTimer === "function") kmMoveStopTimer();
    DATA = {...payload, final: payload.sorting.before};
    RUN_DOCS = payload.sourceDocuments.map(document => document.text);
    stage = 0;
    kmRestart = Math.max(0, Number(DATA.kmeans.best_run || 1) - 1);
    kmStep = centroidStep = mmrStep = kmAnimIndex = 0;
    $('results').style.display = 'block';
    render();
  }
};
"""
    bridge = bridge.replace("window.PipelineDemo = {", "window.PipelineDemo = {\n  defaults: " + json.dumps(demo_defaults()) + ",")
    return "(() => {\n" + script + enhancements + bridge + "\n})();"


def demo_styles():
    styles = re.search(r"<style>(.*?)</style>", demo_module().PAGE, re.S).group(1)
    styles = styles.replace(":root", ":scope")
    # Match the web's teal theme; keep warm warning and cluster colors intact.
    def theme_color(match):
        value = match.group()[1:]
        rgb = tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))
        hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
        if not 215 <= hue * 360 <= 295 or saturation < 0.1:
            return match.group()
        color = ("#182230" if lightness < 0.25 else "#667085" if saturation < 0.4 and lightness < 0.65
                 else "#115e59" if lightness < 0.4 else "#0f766e" if lightness < 0.7
                 else "#d9e1e8" if lightness < 0.9 else "#edf7f5")
        return color + value[6:]
    styles = re.sub(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b", theme_color, styles)
    styles += """
:scope { --ink:#182230; --muted:#667085; --line:#d9e1e8; --blue:#0f766e;
  --teal:#0f766e; --paper:#fff; --wash:#f9fbfc; --pastel-lilac:#d9f3ee;
  --pastel-blue:#e7effd; --pastel-mint:#d9f3ee; }
.eyebrow { color:#0f766e; }
.pills#flow-groups button.on { background:#0f766e!important; border-color:#0f766e!important; color:#fff!important; }
.pills#flow-groups button.on span, .pills#flow-groups button.on .flow-group-number { color:#fff!important; }
.pills#flow-groups button.on .flow-group-number { background:#ffffff26!important; }
button.primary:hover, .flow-controls #flow-play:hover { background:#115e59!important; border-color:#115e59!important; }
"""
    return "@scope (#interactiveDemo) {\n" + styles + "\n}"
