from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMPORTER_PATH = PROJECT_ROOT / "tools" / "import_team_logos.py"

spec = importlib.util.spec_from_file_location("import_team_logos", IMPORTER_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def check(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"PASS  {label}")


check("JAC maps to ESPN JAX", module.espn_code_for("JAC") == "jax")
check("WAS maps to ESPN WSH", module.espn_code_for("WAS") == "wsh")
check("normal team lowercases", module.espn_code_for("GB") == "gb")
check(
    "logo URL uses NFL endpoint",
    module.logo_url("DET").endswith("/nfl/500/det.png"),
)
check("32 canonical NFL teams", len(module.NFL_TEAM_CODES) == 32)
check("FA ignored", "FA" in module.IGNORED_TEAM_CODES)

# Synthetic logo: an opaque near-black canvas with a black logo detail isolated
# from the edge. Only the edge-connected canvas should be removed.
image = Image.new("RGBA", (12, 12), (8, 8, 8, 255))
for x in range(4, 8):
    for y in range(4, 8):
        image.putpixel((x, y), (0, 0, 0, 255))
image.putpixel((5, 5), (200, 20, 20, 255))

cleaned = module.remove_uniform_edge_background(image)
check("dark edge background becomes transparent", cleaned.getpixel((0, 0))[3] == 0)
check("interior logo detail remains opaque", cleaned.getpixel((5, 5))[3] == 255)

transparent = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
transparent.putpixel((4, 4), (255, 0, 0, 255))
transparent_cleaned = module.remove_uniform_edge_background(transparent)
check("existing alpha is preserved", transparent_cleaned.getpixel((0, 0))[3] == 0)

print("\nALL TEAM LOGO IMPORTER TESTS PASSED")
