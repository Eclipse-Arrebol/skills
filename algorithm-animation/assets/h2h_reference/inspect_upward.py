import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw, ImageFont
from graph_data import VERTICES, EDGES, UPDATED_EDGES
from h2h_algorithm import build

ROOT=Path(__file__).resolve().parent


def run(args):
    return subprocess.check_output(args,encoding="utf-8",errors="replace")


def inspect(preview=False):
    directory=ROOT/("preview" if preview else "media")
    movie=next((directory/"videos"/"scene_upward_labels").glob("*/H2HUpwardLabels.mp4"))
    delivered=ROOT/"H2H_SC上行边保存_标签逐项递推.mp4"
    if not preview and delivered.exists():
        movie=delivered
    probe=json.loads(run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(movie)]))
    assert not any(s["codec_type"]=="audio" for s in probe["streams"])
    run(["ffmpeg","-v","error","-i",str(movie),"-f","null","-"])
    data=json.loads((ROOT/"timeline.json").read_text(encoding="utf-8"))
    events={e["name"]:e for e in data["events"]}
    old,new=build(EDGES),build(UPDATED_EDGES)
    for v in VERTICES:
        assert events[f"saved_SC_{v}"]["sc"]==old["upward"][v]
    for f in data["formula_checks"]:
        model=new if f["updating"] else old
        assert f["sc"]==model["upward"][f["v"]]
        assert f["value"]==model["labels"][f["v"]][f["a"]]
        if f["terms"]:
            assert f["value"]==min(f["terms"].values())
    assert len(data["formula_checks"])==21
    out=ROOT/("qa_preview" if preview else "qa_final")
    out.mkdir(exist_ok=True)
    keys=["saved_SC_A","saved_SC_D","saved_SC_B","saved_SC_E",
          "tree_complete","derive_C_F","derive_B_F","derive_A_E",
          "labels_complete","query_before","SC_A_updated","SC_B_updated",
          "update_B_F","update_A_B","update_A_C","query_after"]
    font=ImageFont.truetype("C:/Windows/Fonts/msyh.ttc",21)
    for start in range(0,len(keys),4):
        sheet=Image.new("RGB",(1440,870),"#111827")
        draw=ImageDraw.Draw(sheet)
        for i,key in enumerate(keys[start:start+4]):
            t=events[key]["time"]+.15
            file=out/f"{key}.png"
            run(["ffmpeg","-v","error","-ss",str(t),"-i",str(movie),"-frames:v","1","-y",str(file)])
            x,y=i%2*720,i//2*435
            sheet.paste(Image.open(file).convert("RGB").resize((720,405)),(x,y+30))
            draw.text((x+8,y+3),f"{key} | {t:.2f}s",font=font,fill="white")
        sheet.save(out/f"contact_{start//4}.png")
    report=dict(duration=float(probe["format"]["duration"]),width=probe["streams"][0]["width"],
                height=probe["streams"][0]["height"],fps=probe["streams"][0]["r_frame_rate"],
                audio=False,saved_incident_maps=6,derivations=21,frames=len(keys),probe=probe)
    (out/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="probe"},ensure_ascii=False))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--preview",action="store_true")
    inspect(p.parse_args().preview)
