from os import environ as __environ

CHANNEL_DEFAULTS = dict(
   diffuse                = dict(abbr = 'col', ncd=False,  channels = ['col', 'color' ,'clr' ,'diff' ,'diffuse' ,'diffuseColor']),
   reflection           = dict(abbr = 'refl', ncd=True, channels = ['refl', 'rfl', 'spec', 'spc' ,'specular' ,'specularColor' ,'reflection' ,'reflectionColor' ,'reflectedColor']),
   refraction           = dict(abbr = 'refr', ncd=True, channels = ['refr' ,'refraction' ,'refractionColor']),
   bump                 = dict(abbr = 'bp', ncd=True,   channels = ['bp' ,'bump' ,'bmp' ,'bumpMap' ,'normalCamera']),
   displacement         = dict(abbr = 'disp', ncd=True, channels = ['disp', 'displacement', 'dsp']),
   normal               = dict(abbr = 'nm', ncd=True,   channels = ['nm' ,'norm' ,'normal' ,'normalMap']),
   opacity              = dict(abbr = 'op', ncd=True,   channels = ['op' ,'opactiy' ,'trans' ,'transparency', 'alpha', 'msk']), 
   
   # VRayFastSSS    
   overallColor         = dict(abbr = 'sov', ncd=False,  channels = ['sov', 'ovt', 'overallTex']),
   #diffuseTex           = dict(abbr = 'sdf',  channels = ['sdf', 'df, diffuseTex']),
   subsurfaceColor      = dict(abbr = 'ssc', ncd=False,  channels = ['ssc', 'subsurfaceColor']),
   scatterRadiusColor   = dict(abbr = 'sca', ncd=False, channels = ['sca', 'scrc', 'scatterRadiusColor']),
   #scatterRadiusMult    = dict(abbr = 'scrm', channels = ['scrm', 'scatterRadiusMult']),   
   )
