import bpy, math
exec(open('tools/blender_build.py',encoding='utf-8').read().split('def main():')[0].split('main()')[0])

# Builders originales inspirados en refs/ (no copias de personajes con copyright)
def build_generic(name, body, dark, accent, scale=1.0, belly=False):
    clear_scene(); build_armature()
    mat_body=make_mat(name+'_body',body,metallic=0.2,roughness=0.55)
    mat_dark=make_mat(name+'_dark',dark,metallic=0.4,roughness=0.5)
    mat_acc=make_mat(name+'_acc',accent,metallic=0.3,roughness=0.4)
    mat_glow=make_mat(name+'_glow',accent,emissive=accent,strength=2.0)
    s=scale
    cyl_between('Spine',(0,0,0.55),(0,0,1.05),0.38*s,mat_dark,name+'_pelvis')
    cyl_between('Chest',(0,0,1.05),(0,0,1.6),0.44*s,mat_body,name+'_chest')
    sphere('Chest',(0,0,1.05),0.44*s,mat_body,name+'_a')
    sphere('Chest',(0,0,1.6),0.46*s,mat_body,name+'_b')
    if belly:
        sphere('Chest',(0,0.25,1.2),0.42*s,mat_acc,name+'_belly')
    cyl_between('Chest',(0,0,0.92),(0,0,1.02),0.46*s,mat_dark,name+'_belt')
    sphere('Head',(0,0,1.88),0.32*s,mat_body,name+'_face')
    sphere('L_UpperArm',(-0.32,0,1.52),0.18*s,mat_acc,name+'_shL')
    sphere('R_UpperArm',(0.32,0,1.52),0.18*s,mat_acc,name+'_shR')
    cyl_between('L_UpperArm',(-0.3,0,1.48),(-0.9,0,1.1),0.12*s,mat_body,name+'_biL')
    cyl_between('L_ForeArm',(-0.9,0,1.1),(-1.28,0,0.8),0.10*s,mat_body,name+'_forL')
    sphere('L_ForeArm',(-1.34,0,0.75),0.14*s,mat_dark,name+'_fistL')
    cyl_between('R_UpperArm',(0.3,0,1.48),(0.9,0,1.1),0.12*s,mat_body,name+'_biR')
    cyl_between('R_ForeArm',(0.9,0,1.1),(1.28,0,0.8),0.10*s,mat_body,name+'_forR')
    sphere('R_ForeArm',(1.34,0,0.75),0.14*s,mat_dark,name+'_fistR')
    cyl_between('L_Thigh',(-0.3,0,0.82),(-0.38,0,0.42),0.14*s,mat_dark,name+'_thL')
    cyl_between('L_Shin',(-0.38,0,0.4),(-0.4,0,0.05),0.12*s,mat_dark,name+'_shnL')
    sphere('L_Shin',(-0.4,0.08,0.03),0.16*s,mat_acc,name+'_footL',squash=(1,1.4,0.55))
    cyl_between('R_Thigh',(0.3,0,0.82),(0.38,0,0.42),0.14*s,mat_dark,name+'_thR')
    cyl_between('R_Shin',(0.38,0,0.4),(0.4,0,0.05),0.12*s,mat_dark,name+'_shnR')
    sphere('R_Shin',(0.4,0.08,0.03),0.16*s,mat_acc,name+'_footR',squash=(1,1.4,0.55))
    # detalle unico por personaje
    if name=='vamp':
        box('Head',(0,0.3,1.9),(0.4,0.12,0.12),mat_glow,name+'_eyes')
        cyl_between('R_ForeArm',(1.34,0,0.75),(1.34,0,1.25),0.03,mat_acc,name+'_blaster')
    elif name=='ronin':
        sphere('Head',(0,0,2.22),0.08,mat_acc,name+'_knot')
        cyl_between('R_ForeArm',(1.34,0,0.75),(1.34,0,1.35),0.03,mat_acc,name+'_blade')
    elif name=='rhino':
        cyl_between('Head',(0,0,2.05),(0,0,2.45),0.08,mat_acc,name+'_horn')
        box('Head',(0,0.32,1.9),(0.4,0.12,0.12),mat_glow,name+'_eyes')
    elif name=='panda':
        sphere('Head',(-0.25,0,2.1),0.1,mat_dark,name+'_earL')
        sphere('Head',(0.25,0,2.1),0.1,mat_dark,name+'_earR')
        cyl_between('R_ForeArm',(1.34,0,0.75),(1.34,0,1.25),0.05,mat_dark,name+'_gun')
    elif name=='roja':
        cyl_between('Head',(0,-0.2,2.1),(0,-0.35,1.7),0.08,mat_acc,name+'_pony')
        cyl_between('R_ForeArm',(1.34,0,0.75),(1.34,0,1.25),0.03,mat_glow,name+'_blaster')
    elif name=='ogro':
        box('Head',(0,0,2.25),(0.08,0.25,0.4),mat_dark,name+'_mohawk')
        box('Head',(0,0.32,1.9),(0.4,0.12,0.12),mat_glow,name+'_eyes')

out='C:/Users/USUARIO/pelea-IA-VS/assets/models'
specs=[
 ('vamp',(0.12,0.14,0.19),(0.05,0.06,0.1),(0.86,0.15,0.15),1.0,False),
 ('ronin',(0.11,0.1,0.09),(0.05,0.05,0.05),(0.85,0.47,0.02),0.95,False),
 ('rhino',(0.38,0.65,0.98),(0.07,0.09,0.15),(0.98,0.45,0.09),1.1,False),
 ('panda',(0.97,0.98,0.99),(0.12,0.16,0.24),(0.98,0.45,0.09),1.05,True),
 ('roja',(0.09,0.64,0.29),(0.42,0.45,0.5),(0.86,0.15,0.15),0.9,False),
 ('ogro',(0.53,0.94,0.67),(0.12,0.16,0.22),(0.73,0.11,0.11),1.15,False),
]
for name,body,dark,acc,scale,belly in specs:
    build_generic(name,body,dark,acc,scale,belly); make_actions(); export_glb(out+'/'+name+'.glb')
    print('DONE',name)
print('DONE all new fighters')
