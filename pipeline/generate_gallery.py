#!/bin/env python

import os
import pipe_globals


show_root = pipe_globals.get_show_folder()
shots_root = pipe_globals.get_subfolder(show_root, "shots")
shot_folder = pipe_globals.get_subfolder(shots_root, "s001_001")
renders_folder = pipe_globals.get_subfolder(shot_folder, "usdrecord_renders")
readme_path = os.path.join(renders_folder, "README.md")

renderers = [
    ("Arnold","Arnold","rgba","jpg"),
    ("ArnoldMTOA","ArnoldMTOA","rgba","jpg"),
    ("Gemini","Gemini","rgba","jpg"),
    ("GL","Storm","rgba","jpg"),
    ("Karma CPU","Karma CPU","rgba","jpg"),
    ("O3DE","O3DE","rgba","jpg"),
    ("OmniverseRaytraceCapture","OmniverseRT","Capture","png"),
    ("Redshift","Redshift","rgba","jpg"),
    ("RenderMan RIS","RenderMan RIS","rgba","jpg"),
]


with open(readme_path, "w", encoding="utf-8") as file:
    file.write("# Renders comparison on important-frames\n\n")
    for purpose in ["render","proxy"]:
        file.write("## {} purpose\n\n".format(purpose))
        file.write("|Frame|")
        for renderer in renderers:
            file.write("{}|".format(renderer[1]))
        file.write("\n")
        file.write("|-|")
        for renderer in renderers:
            file.write("-|")
        file.write("\n")
        for frame in pipe_globals.IMPORTANT_FRAMES:
            file.write("|{}|".format(frame))
            for renderer in renderers:
                file.write('<img src="./{}/{}/{}.{}.{}" width="200">|'.format(purpose,renderer[0].replace(" ","%20"), renderer[2], frame, renderer[3]))
            file.write("\n")
        file.write("\n")
