"""
Adaugă tranzițiile (Morph / Fade) și animațiile de apariție (Fade In) din v3
peste prezentarea `Atlasul secetei din 2024 — v4.pptx`, păstrând intacte
videoclipurile încorporate, filele de navigare din dreapta (neanimate, mereu vizibile),
actualizările IC 95% / INS / Anexa A și notițele vorbitorului.
"""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ppt" / "Atlasul secetei din 2024 — v4.pptx"
DST = ROOT / "ppt" / "Atlasul secetei din 2024 — v4 (animatii).pptx"

NS = {"p": "http://schemas.openxmlformats.org/presentationml/2006/main"}

MORPH_XML = (
    '<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
    '<mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" Requires="p159">'
    '<p:transition xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" spd="slow" p14:dur="1400">'
    '<p159:morph option="byObject"/>'
    "</p:transition>"
    "</mc:Choice>"
    "<mc:Fallback>"
    '<p:transition spd="slow"><p:fade/></p:transition>'
    "</mc:Fallback>"
    "</mc:AlternateContent>"
)


def build_timing_xml(auto_groups, click_groups):
    """
    auto_groups: list of (delay_ms, [spids]) triggered automatically on slide begin.
    click_groups: list of [spids] each triggered by user mouse click.
    """
    cid = [1]

    def nid():
        val = cid[0]
        cid[0] += 1
        return str(val)

    def make_effect_par(spid, node_type):
        return (
            f'<p:par><p:cTn id="{nid()}" presetID="10" presetClass="entr" presetSubtype="0" '
            f'fill="hold" grpId="0" nodeType="{node_type}">'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            "<p:childTnLst>"
            f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold">'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            "<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>"
            '</p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
            f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="600"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl>'
            "</p:cBhvr></p:animEffect>"
            "</p:childTnLst></p:cTn></p:par>"
        )

    all_spids = []
    root_id = nid()  # 1
    main_seq_id = nid()  # 2

    steps_xml = []

    if auto_groups:
        sub_xml = []
        for delay_ms, spids in auto_groups:
            effects = []
            for idx, spid in enumerate(spids):
                nt = "afterEffect" if idx == 0 else "withEffect"
                effects.append(make_effect_par(spid, nt))
                all_spids.append(spid)
            sub_xml.append(
                f'<p:par><p:cTn id="{nid()}" fill="hold">'
                f'<p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst>'
                f'<p:childTnLst>{"".join(effects)}</p:childTnLst></p:cTn></p:par>'
            )
        steps_xml.append(
            f'<p:par><p:cTn id="{nid()}" fill="hold">'
            "<p:stCondLst>"
            '<p:cond delay="indefinite"/>'
            f'<p:cond evt="onBegin" delay="0"><p:tn val="{main_seq_id}"/></p:cond>'
            "</p:stCondLst>"
            f'<p:childTnLst>{"".join(sub_xml)}</p:childTnLst></p:cTn></p:par>'
        )

    for spids in click_groups:
        effects = []
        for idx, spid in enumerate(spids):
            nt = "clickEffect" if idx == 0 else "withEffect"
            effects.append(make_effect_par(spid, nt))
            all_spids.append(spid)
        sub = (
            f'<p:par><p:cTn id="{nid()}" fill="hold">'
            '<p:stCondLst><p:cond delay="0"/></p:stCondLst>'
            f'<p:childTnLst>{"".join(effects)}</p:childTnLst></p:cTn></p:par>'
        )
        steps_xml.append(
            f'<p:par><p:cTn id="{nid()}" fill="hold">'
            '<p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
            f"<p:childTnLst>{sub}</p:childTnLst></p:cTn></p:par>"
        )

    bld_xml = "".join(
        f'<p:bldP spid="{spid}" grpId="0" animBg="1"/>' for spid in all_spids
    )

    return (
        f'<p:timing><p:tnLst><p:par><p:cTn id="{root_id}" dur="indefinite" restart="never" nodeType="tmRoot">'
        f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="{main_seq_id}" dur="indefinite" nodeType="mainSeq">'
        f'<p:childTnLst>{"".join(steps_xml)}</p:childTnLst></p:cTn>'
        '<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
        '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst>'
        f"</p:seq></p:childTnLst></p:cTn></p:par></p:tnLst><p:bldLst>{bld_xml}</p:bldLst></p:timing>"
    )


SLIDE_SPECS = {
    1: {
        "morph": False,
        "auto": [
            (150, ["8", "9", "11", "12", "14", "15"]),
            (570, ["18", "19", "20", "21"]),
        ],
        "click": [],
    },
    2: {
        "morph": True,
        "auto": [
            (150, ["6", "7", "8"]),
            (570, ["9", "10"]),
            (990, ["11", "12", "13", "14"]),
            (1410, ["15", "16"]),
        ],
        "click": [],
    },
    3: {
        "morph": True,
        "auto": [
            (150, [str(i) for i in ([5, 6, 7] + list(range(12, 70)))]),
            (570, ["8", "9", "10", "11"]),
            (990, ["70", "71", "72", "73", "74", "75", "76"]),
        ],
        "click": [],
    },
    # 4: video_zbor — untouched
    5: {
        "morph": False,
        "auto": [
            (150, ["5", "6", "7", "8", "9", "10"]),
            (570, [str(i) for i in range(11, 41)]),
        ],
        "click": [
            ["43", "44"],
            ["45", "46"],
            [str(i) for i in range(47, 63)],
        ],
    },
    6: {
        "morph": True,
        "auto": [
            (150, ["5", "9", "12", "13"]),
            (570, ["6", "10", "14", "15"]),
            (990, ["7", "11", "16", "17"]),
            (1410, ["8", "18", "19"]),
            (1830, ["27", "28", "29", "30", "31", "32", "33"]),
            (2250, ["20", "21", "22", "23", "24", "25", "26"]),
            (2670, ["34", "35", "36", "37", "38"]),
        ],
        "click": [],
    },
    7: {
        "morph": True,
        "auto": [
            (150, ["5", "6", "15", "19", "20"]),
            (570, ["7", "8", "16", "21", "22"]),
            (990, ["9", "10", "17", "23", "24"]),
            (1410, ["11", "12", "18", "25", "26"]),
            (1830, ["13", "14", "27", "28"]),
            (2250, ["29", "30", "31", "32"]),
        ],
        "click": [
            [str(i) for i in range(33, 44)],
        ],
    },
    # 8: video_film — untouched
    9: {
        "morph": False,
        "auto": [],
        "click": [
            [str(i) for i in range(5, 20)],
            [str(i) for i in range(20, 30)],
            [str(i) for i in range(30, 49)],
        ],
    },
    10: {
        "morph": True,
        "auto": [],
        "click": [
            ["5", "6"],
            ["7", "8"],
            ["9", "10"],
        ],
    },
    # 11, 12, 13: appendices — Fade, no timing for instant Q&A jump
}


def main():
    with zipfile.ZipFile(SRC, "r") as zin, zipfile.ZipFile(
        DST, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            m = re.match(r"^ppt/slides/slide(\d+)\.xml$", item.filename)
            if m:
                snum = int(m.group(1))
                spec = SLIDE_SPECS.get(snum)
                if spec is not None:
                    xml_str = data.decode("utf-8")
                    root = ET.fromstring(data)

                    # Verify every target spid exists and is NOT a nav_* tab
                    existing_shapes = {}
                    for el in root.findall(".//p:spTree/*", NS):
                        nv = el.find(".//p:cNvPr", NS)
                        if nv is not None:
                            existing_shapes[nv.attrib["id"]] = nv.attrib.get("name", "")

                    targets = [s for _, grp in spec["auto"] for s in grp] + [
                        s for grp in spec["click"] for s in grp
                    ]
                    for spid in targets:
                        assert spid in existing_shapes, f"S{snum}: missing spid {spid}"
                        assert not existing_shapes[spid].startswith(
                            "nav_"
                        ), f"S{snum}: nav shape {spid} should not be animated"

                    # Replace transition if morph=True
                    if spec["morph"]:
                        xml_str, n = re.subn(
                            r"<p:transition\b[^>]*>.*?</p:transition>",
                            MORPH_XML,
                            xml_str,
                            count=1,
                            flags=re.DOTALL,
                        )
                        assert n == 1, f"S{snum}: failed to replace transition"

                    # Strip any existing <p:timing>...</p:timing> (safety)
                    xml_str = re.sub(
                        r"<p:timing\b.*?</p:timing>", "", xml_str, flags=re.DOTALL
                    )

                    # Insert new <p:timing> right before </p:sld>
                    timing_xml = build_timing_xml(spec["auto"], spec["click"])
                    assert xml_str.endswith("</p:sld>"), f"S{snum}: unexpected tail"
                    xml_str = xml_str[: -len("</p:sld>")] + timing_xml + "</p:sld>"

                    # Validate resulting XML parses cleanly
                    ET.fromstring(xml_str.encode("utf-8"))
                    data = xml_str.encode("utf-8")
                    print(
                        f"S{snum:02d}: morph={spec['morph']} | animated_shapes={len(targets)}"
                    )
            zout.writestr(item, data)

    print(f"\nCreated: {DST} ({DST.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
