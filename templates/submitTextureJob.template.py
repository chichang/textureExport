#!/usr/bin/python25

import sys

def ${asset}_submitTextureJob(debug=${debug}, convert_only=${convert_only}):
    sys.path.insert(0, "${txPath}")

    import LinuxJob
    import ShotGlobals
    import XSubmit

    todo = XSubmit.XSubmit()

    convertShot = ShotGlobals.ShotGlobals()
    convertShot.setSoftwareType('texture')
    convertShot.setShow("${SHOW}")
    #convertShot.setShot("${SHOT}")
    convertShot.setFrames(1, ${nchunks})
    convertShot.setVersion(${pubVer})
    convertShot.setSlaveGroup("${slave}")

    ##  Converting the textures ...
    convertJob = LinuxJob.LinuxJob("${asset}_convertTextures", convertShot)
    convertJob.setJobName('${convertJobName}')
    convertJob.setBatchFile("${scriptDir}/${asset}_makeTextures.py")
    convertJob.setAutoResurrect(False) # for debugging
    todo.addPass(convertJob)
    
    ##  Publishing the textures ...
    publishTextures = ShotGlobals.ShotGlobals()
    publishTextures.setSoftwareType('texture')
    publishTextures.setShow("${SHOW}")
    publishTextures.setShot("${SHOT}")
    publishTextures.setNumParts(1)
    publishTextures.setVersion(${pubVer})
    
    if not convert_only:
        publishTextures.setSlaveGroup("${slave}")
        textureJob = LinuxJob.LinuxJob("${asset}_publishTextures", publishTextures)
        textureJob.setJobName('${publishJobName}')
        textureJob.setBatchFile("${scriptDir}/${asset}_publishTextures.py")
        textureJob.setAutoResurrect(False) # for debugging
        todo.addPass(textureJob)
    
    todo.submit()

if __name__ == "__main__" :
    ${asset}_submitTextureJob()
