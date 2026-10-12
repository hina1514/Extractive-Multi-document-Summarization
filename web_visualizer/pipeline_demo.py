"""Adapt the standalone demo's renderer to the visualizer's shared workspace.

Keep algorithm scenes in their source module rather than maintaining a second
copy of the large renderer. All DOM lookups and styles stay inside the demo.
"""
import re
from pathlib import Path
from functools import lru_cache

from methods.main_method.interactive_pipeline_demo import PAGE


@lru_cache(maxsize=1)
def demo_script():
    script = re.search(r"<script>(.*?)</script>", PAGE, re.S).group(1)
    script = script.replace(
        "const $=id=>document.getElementById(id);",
        "const root=document.querySelector('#interactiveDemo');"
        "const $=id=>root.querySelector('#'+CSS.escape(id));",
    )
    script = script.replace("resetSample();$('add-doc').onclick=()=>addDoc('');$('sample').onclick=resetSample;", "")
    # The host handles shared input, uploads, requests and keyboard shortcuts.
    script = re.sub(r"^document\.addEventListener\('keydown'.*$", "", script, flags=re.M)
    script = script[:script.index("$('run').onclick=async")]
    colors = "['#0F766E','#2563EB','#D97706','#7C3AED','#DB2777','#0891B2','#4D7C0F','#DC2626','#4338CA','#0E7490']"
    script = re.sub(r"const (COLORS|KM_COLORS)=\[[^\]]+\];", lambda m: f"const {m.group(1)}={colors};", script)
    enhancements = (Path(__file__).parent / "static" / "demo_enhancements.js").read_text(encoding="utf-8")
    bridge = """
window.PipelineDemo = {
  sample: () => SAMPLE.slice(),
  stop: () => { flowStop(); kmLessonStopTimer(); },
  move: direction => { if (DATA) { flowStop(); flowGo(flowIndex + direction); } },
  load: payload => {
    flowStop(); kmLessonStopTimer();
    DATA = payload;
    RUN_DOCS = payload.sourceDocuments.map(document => document.text);
    stage = 0;
    kmRestart = Math.max(0, Number(DATA.kmeans.best_run || 1) - 1);
    kmStep = centroidStep = mmrStep = kmAnimIndex = 0;
    $('results').style.display = 'block';
    render();
  }
};
"""
    return "(() => {\n" + script + enhancements + bridge + "\n})();"


@lru_cache(maxsize=1)
def demo_styles():
    styles = re.search(r"<style>(.*?)</style>", PAGE, re.S).group(1)
    # The demo's last theme is purple; reuse the web's teal palette while keeping
    # semantic cluster and comparison colors in the diagrams.
    palette = {
        "#3020b8": "#0f766e", "#24158f": "#115e59", "#2917a4": "#115e59",
        "#6958c8": "#0f766e", "#6c5ac8": "#0f766e", "#5268e8": "#0f766e",
        "#d9d0ff": "#d9f3ee", "#fbfaff": "#f8fbfb", "#e9e5f6": "#e7efee",
        "#e3ddf6": "#d9e1e8", "#d8d0fb": "#bde5d5", "#a99bea": "#78bfa9",
        "#e1dbf4": "#d9e1e8", "#5d547b": "#667085",
        "#3020a0": "#115e59", "#514765": "#667085", "#30264a": "#182230",
        "#201638": "#182230", "#392d55": "#182230", "#e7e1fa": "#d9e1e8",
        "#d8d1f0": "#d9e1e8", "#dcd5f3": "#d9e1e8", "#f2effb": "#f9fbfc",
    }
    styles = re.sub(r"#[0-9a-fA-F]{6}", lambda m: palette.get(m.group().lower(), m.group()), styles)
    return "@scope (#interactiveDemo) {\n" + styles + "\n}"
