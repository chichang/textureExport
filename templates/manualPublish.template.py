#!/X/tools/binlinux/xpython
from DefinedAssets import *
import subprocess, os

rootdir = '${rootDir}'
lods=${lods}
lods.update(source=True)
exclusions=${exclusions}

def addDefines(asset, show, shot):   
    assets=DefinedAssets(show, shot)
    assetNames=[a.name() for a in assets.assets()]

    defines=[
        ('%s_tex_src' % asset, 'source'),
        ('%s_tex_fullres' % asset, 'full'),
        ('%s_tex_hires' % asset, 'high'),
        ('%s_tex_midres' % asset, 'medium'),
        ('%s_tex_lores' % asset,  'low'),
        ('%s_tex_tinyres' % asset, 'tiny'),
    ]

    result=dict()

    new_defs = []
    for define in defines:            
        assetName=define[0]
        res=define[1]
        if res not in exclusions:    
            # IMPORTANT, CONSTRAIN THE DEFINES TO THE CURRENT LODS 
            if res in lods.keys():       
                if assetName not in assetNames:
                    print ('# creating define for asset "%s"' % assetName)            
                    new_asset=Asset()
                    new_asset.setName(assetName)
                    new_asset.setType('tex_dir')
                    new_asset.setPublishDir('textures/%s' % asset)
                    new_asset.setDirFlag('dir')
                    new_asset.setDescription("%s resolution textures used to create the textures in %s_tex_palette_json" % (res, asset))
                    new_defs.append(new_asset)
                    result[assetName]=dict(asset=new_asset)
                    result.get(assetName).update(lod=res)
                else:
                    result[assetName]=dict(asset=assets.getAsset(assetName))
                    result.get(assetName).update(lod=res)
                    print ('# define "%s" already exists...' % assetName)

    # palette
    if 'palette' not in exclusions:
        palName='%s_tex_palette_json' % asset
        if  palName not in assetNames:
            print('# creating define for asset "%s"' % palName) 
            pal_asset=Asset()
            pal_asset.setName(palName)
            pal_asset.setType('tex_palette_json')
            pal_asset.setPublishDir('textures/%s' % asset)
            pal_asset.setDescription("JSON asset, palette info for %s_tex_palette_json" % asset)
            #pal_asset.setDirFlag('json')
            pal_asset.setExtension('json')
            result[palName]=dict(asset=pal_asset)
            assets.addDefine(pal_asset)
        else:
            result[palName]=dict(asset=assets.getAsset(palName))
            print('# define "%s" already exists...' % '%s_tex_palette_json' % asset)

    if new_defs:
        assets.addDefine(new_defs)
    return result

if __name__ == '__main__':
    result=addDefines('${asset}', '${SHOW}', '${SHOT}')
    for define, attrs in result.iteritems():
        if '_tex_palette_json' not in define:
            publish_dir = os.path.join(rootdir, define)
            if os.path.exists(publish_dir):
                if len(os.listdir(publish_dir)):
                    publish = subprocess.Popen(['xpub','-a', define,'-p', publish_dir, '-q'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                    out, err = publish.communicate()
                    rv=publish.wait()
                    if not rv:
                        print '# asset publish "%s" succeeded!' % define
            else:
                print '# texture directory "%s" does not exist, skipping publish...' % publish_dir
        else:
            palette = os.path.join(rootdir, '%s_texturePublish.json' % define)
            if os.path.exists(palette):
                if 'palette' not in exclusions:
                    palpublish = subprocess.Popen(['xpub','-a', define,'-p', palette, '-q'], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                    out, err = palpublish.communicate()
                    pv=palpublish.wait()
                    if not pv:
                        print '# asset publish "%s" succeeded!' % '%s_texturePublish.json' % define
        
    
    
    