#!/bin/bash
''''exec /X/tools/binlinux/python_goshow2 2.6 $$0 "$$@"
'
    This script must be run from within Maya *OR* in a Maya
    batch job (please see the mel file of the same name located
    in the same directory).
'''

import os
import sys

def ${asset}_updateToPublishedTextures() :
    sys.path.insert(0, "${txPath}")

    import texturizer2.lib.xpalette as xp
    import texturizer2.texturizer as tx

    show = "${SHOW}"
    shot = "${SHOT}"
    asset = "${asset}"
    name = "%s_tex_palette_json" % asset
    
    tt = tx.Texturizer()
    palette = tx.getPublishFile(name, show, shot)
    
    if os.path.exists(palette):
        tt.importPalette(palette)
        if tt.options.getMayaAttr('finalFile'):
            mayaFile = tt.options.getMayaAttr('finalFile')
            tt.xpalette.updateMayaFile(mayaFile, lod="${lod}")
        else:
            print '>> Final Maya file not defined, skipping.. <<'
    else:
        print '>> XPalette does not exist, stopping <<'

    print "DONE.\n"

if __name__ == "__main__" :
    ${asset}_updateToPublishedTextures()

