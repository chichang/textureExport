#!/bin/bash
''''exec /X/tools/binlinux/python_goshow2 2.6 $$0 "$$@"
' '''
import os, sys, glob

def ${asset}_publishTextures(publishPalette=${publishPalette}, publishTextures=${publishTextures}, verbose=${verbose}):
    sys.path.insert(0, '${txPath}')
    publishAttrs=dict(
        user = '${user}',
        asset = '${asset}',
        show = '${SHOW}',
        shot = '${SHOT}',
        lods = ${lods},
        rootdir='${rootDir}',
        processPalette='${processPalette}',
        palBase='${palBase}',
        comments='${comments}',
        publishPalette=publishPalette,
        publishTextures=publishTextures,
        verbose=verbose,
        copyPublish=${copyPublish},
        debug=${debug},
        patch=${patch},
        location='${location}',
        srgb_full='${srgb_full}',
        )

    from textureManager import publish
    publishTextures=publish.PublishTextures(**publishAttrs)


if __name__ == "__main__" :
    ${asset}_publishTextures()