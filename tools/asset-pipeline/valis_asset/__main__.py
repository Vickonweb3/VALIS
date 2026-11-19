import argparse
import json
import sys

from .bake import BakeConfig, bake, write
from .glb import Glb, GlbError


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="valis_asset", description="Bake valis_anim.v1 from a GLB")
    ap.add_argument("glb")
    ap.add_argument("outdir")
    ap.add_argument("--overrides", help="clip_overrides.json")
    a = ap.parse_args(argv)
    try:
        glb = Glb.load(a.glb)
        ov = json.load(open(a.overrides)) if a.overrides else None
        index, payload = bake(glb, BakeConfig(overrides=ov))
    except (GlbError, OSError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    jp, bp = write(index, payload, a.outdir)
    loops = sum(c["loopable"] for c in index["clips"])
    print(f"{len(index['clips'])} clips ({loops} loopable) -> {jp} ({bp.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
