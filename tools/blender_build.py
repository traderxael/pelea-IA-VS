import bpy, math
from mathutils import Vector, Matrix

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials, bpy.data.collections):
        for x in list(block):
            try: block.remove(x)
            except Exception: pass

def make_mat(name, color, metallic=0.0, roughness=0.5, emissive=None, strength=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if emissive is not None:
        bsdf.inputs['Emission Color'].default_value = (*emissive, 1.0)
        bsdf.inputs['Emission Strength'].default_value = strength
    return m

ARM_DATA = 'Armature'
arm_obj = None

def build_armature():
    global arm_obj
    data = bpy.data.armatures.new(ARM_DATA)
    arm_obj = bpy.data.objects.new(ARM_DATA, data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    ebones = data.edit_bones
    defs = [
        ('Root',        (0,0,0.15), (0,0,0.55), None),
        ('Spine',       (0,0,0.55), (0,0,1.05), 'Root'),
        ('Chest',       (0,0,1.05), (0,0,1.62), 'Spine'),
        ('Head',        (0,0,1.62), (0,0,2.15), 'Chest'),
        ('L_UpperArm',  (-0.22,0,1.5), (-0.9,0,1.1), 'Chest'),
        ('L_ForeArm',   (-0.9,0,1.1), (-1.3,0,0.78), 'L_UpperArm'),
        ('R_UpperArm',  (0.22,0,1.5), (0.9,0,1.1), 'Chest'),
        ('R_ForeArm',   (0.9,0,1.1), (1.3,0,0.78), 'R_UpperArm'),
        ('L_Thigh',     (-0.3,0,0.85), (-0.38,0,0.4), 'Root'),
        ('L_Shin',      (-0.38,0,0.4), (-0.4,0,0.02), 'L_Thigh'),
        ('R_Thigh',     (0.3,0,0.85), (0.38,0,0.4), 'Root'),
        ('R_Shin',      (0.38,0,0.4), (0.4,0,0.02), 'R_Thigh'),
    ]
    for name, head, tail, parent in defs:
        b = ebones.new(name)
        b.head, b.tail = head, tail
        if parent: b.parent = ebones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    arm_obj.show_in_front = True

def assign(obj, bone):
    vg = obj.vertex_groups.new(name=bone)
    vg.add(range(len(obj.data.vertices)), 1.0, 'REPLACE')
    mod = obj.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm_obj
    obj.parent = arm_obj

def cyl_between(bone, p1, p2, radius, mat, name):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    length = d.length
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, location=(p1+p2)/2, vertices=16)
    o = bpy.context.active_object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    o.data.materials.append(mat)
    assign(o, bone)
    return o

def sphere(bone, loc, radius, mat, name, squash=None):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=radius, location=loc, subdivisions=2)
    o = bpy.context.active_object
    o.name = name
    if squash: o.scale = squash
    o.data.materials.append(mat)
    assign(o, bone)
    return o

def box(bone, loc, size, mat, name):
    bpy.ops.mesh.primitive_cube_add(location=loc, size=1.0)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(mat)
    assign(o, bone)
    return o

def build_robot(body_color, body_metal, emissive_color, name):
    clear_scene()
    build_armature()
    mat_body = make_mat(name+'_body', body_color, metallic=body_metal, roughness=0.25)
    mat_dark = make_mat(name+'_dark', (0.06,0.08,0.12), metallic=0.6, roughness=0.45)
    mat_steel = make_mat(name+'_steel', (0.58,0.63,0.71), metallic=0.95, roughness=0.18)
    mat_glow = make_mat(name+'_glow', emissive_color, metallic=0.0, roughness=0.4, emissive=emissive_color, strength=4.0)

    # Torso: capsule (cilindro + esferas) + cinturón + núcleo
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.44, mat_body, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.6), 0.5, mat_body, name+'_chest')
    sphere('Chest', (0,0,1.05), 0.5, mat_body, name+'_chestBot')
    sphere('Chest', (0,0,1.6), 0.52, mat_body, name+'_chestTop')
    cyl_between('Chest', (0,0,0.92), (0,0,1.02), 0.52, mat_dark, name+'_belt')
    sphere('Chest', (0,0.42,1.42), 0.15, mat_glow, name+'_core')
    # Cabeza
    sphere('Head', (0,0,1.88), 0.34, mat_body, name+'_HEAD')
    box('Head', (0,0.3,1.9), (0.4,0.12,0.12), mat_glow, name+'_visor')
    cyl_between('Head', (0.2,0,2.18), (0.2,0,2.55), 0.02, mat_steel, name+'_ant')
    sphere('Head', (0.2,0,2.56), 0.05, mat_glow, name+'_antTip')
    # Hombreras
    sphere('L_UpperArm', (-0.32,0,1.52), 0.22, mat_steel, name+'_shL')
    sphere('R_UpperArm', (0.32,0,1.52), 0.22, mat_steel, name+'_shR')
    # Brazos
    cyl_between('L_UpperArm', (-0.3,0,1.48), (-0.9,0,1.1), 0.15, mat_body, name+'_bicepsL')
    sphere('L_UpperArm', (-0.9,0,1.1), 0.13, mat_steel, name+'_elbowL')
    cyl_between('L_ForeArm', (-0.9,0,1.1), (-1.28,0,0.8), 0.13, mat_body, name+'_foreL')
    sphere('L_ForeArm', (-1.34,0,0.75), 0.18, mat_dark, name+'_fistL')
    cyl_between('R_UpperArm', (0.3,0,1.48), (0.9,0,1.1), 0.15, mat_body, name+'_bicepsR')
    sphere('R_UpperArm', (0.9,0,1.1), 0.13, mat_steel, name+'_elbowR')
    cyl_between('R_ForeArm', (0.9,0,1.1), (1.28,0,0.8), 0.13, mat_body, name+'_foreR')
    sphere('R_ForeArm', (1.34,0,0.75), 0.18, mat_dark, name+'_fistR')
    # Piernas
    cyl_between('L_Thigh', (-0.3,0,0.82), (-0.38,0,0.42), 0.17, mat_dark, name+'_thighL')
    sphere('L_Thigh', (-0.38,0,0.4), 0.14, mat_steel, name+'_kneeL')
    cyl_between('L_Shin', (-0.38,0,0.4), (-0.4,0,0.05), 0.15, mat_dark, name+'_shinL')
    sphere('L_Shin', (-0.4,0.08,0.03), 0.19, mat_body, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.3,0,0.82), (0.38,0,0.42), 0.17, mat_dark, name+'_thighR')
    sphere('R_Thigh', (0.38,0,0.4), 0.14, mat_steel, name+'_kneeR')
    cyl_between('R_Shin', (0.38,0,0.4), (0.4,0,0.05), 0.15, mat_dark, name+'_shinR')
    sphere('R_Shin', (0.4,0.08,0.03), 0.19, mat_body, name+'_footR', squash=(1,1.4,0.55))
    # Tanque de propelente
    cyl_between('Chest', (0,-0.42,1.25), (0,-0.42,1.72), 0.18, mat_steel, name+'_tank')

def key_rot(pbones, bone, frame, euler):
    b = pbones[bone]
    b.rotation_mode = 'XYZ'
    b.rotation_euler = euler
    b.keyframe_insert('rotation_euler', frame=frame)

def key_loc(pbones, bone, frame, loc):
    b = pbones[bone]
    b.location = loc
    b.keyframe_insert('location', frame=frame)

def make_actions():
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 75
    arm_obj.animation_data_create()
    pbones = arm_obj.pose.bones

    idle = bpy.data.actions.new('Idle')
    arm_obj.animation_data.action = idle
    for frame, spine, chest, hips in [(1, (0,0,0), (0,0,0), 0.0), (20, (0.06,0,0), (-0.04,0,0), 0.05), (40, (0,0,0), (0,0,0), 0.0)]:
        sc.frame_set(frame)
        key_rot(pbones, 'Spine', frame, (spine[0], 0, 0))
        key_rot(pbones, 'Chest', frame, (chest[0], 0, 0))
        key_loc(pbones, 'Root', frame, (0, 0, hips))
        key_rot(pbones, 'R_UpperArm', frame, (0, 0, 0.35 + spine[0]*2))
        key_rot(pbones, 'L_UpperArm', frame, (0, 0, -0.35 - spine[0]*2))

    attack = bpy.data.actions.new('Attack')
    arm_obj.animation_data.action = attack
    # windup (1-20), strike (45), recover (75)
    seq = [
        (1,  (0,0,0),   (0,0,0),  0.35, 0),
        (20, (0.25,0,0.15), (-0.2,0,-0.5), 0.9, -0.4),
        (45, (-0.35,0,-0.1), (0.35,0,0.7), -1.3, 1.0),
        (60, (-0.1,0,0), (0.1,0,0.25), 0.15, 0.2),
        (75, (0,0,0),   (0,0,0),  0.35, 0),
    ]
    for frame, spine, chest, armz, bend in seq:
        sc.frame_set(frame)
        key_rot(pbones, 'Spine', frame, spine)
        key_rot(pbones, 'Chest', frame, chest)
        key_rot(pbones, 'R_UpperArm', frame, (0, 0, armz))
        key_rot(pbones, 'R_ForeArm', frame, (0, math.radians(-70)*bend if False else 0, bend*0.9))
        key_loc(pbones, 'Root', frame, (0.15*bend, 0, 0.05*bend))
    arm_obj.animation_data.action = None

    # Push both actions to NLA tracks for export as separate clips
    ad = arm_obj.animation_data
    for act in (idle, attack):
        track = ad.nla_tracks.new()
        track.name = act.name
        strip = track.strips.new(act.name, 1, act)
        strip.action_frame_end = act.frame_range[1]

def export_glb(path):
    sc = bpy.context.scene
    sc.frame_set(1)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_animations=True, export_skins=True)

def build_soldier(name):
    clear_scene()
    build_armature()
    mat_skin = make_mat(name+'_skin', (0.79,0.55,0.37), metallic=0.05, roughness=0.65)
    mat_gr = make_mat(name+'_gr', (0.09,0.3,0.16), metallic=0.25, roughness=0.55)
    mat_dark = make_mat(name+'_dark', (0.11,0.17,0.11), metallic=0.35, roughness=0.55)
    mat_black = make_mat(name+'_black', (0.04,0.06,0.04), metallic=0.4, roughness=0.5)
    mat_glow = make_mat(name+'_glow', (0.52,0.8,0.09), metallic=0.0, roughness=0.4, emissive=(0.52,0.8,0.09), strength=3.5)
    # Torso con chaleco
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.4, mat_skin, name+'_pelvis')
    cyl_between('Chest', (0,0,1.02), (0,0,1.6), 0.51, mat_dark, name+'_vest')
    cyl_between('Chest', (0,0,1.6), (0,0,1.62), 0.46, mat_skin, name+'_collar')
    box('Chest', (-0.2,0.3,1.2), (0.19,0.09,0.14), mat_black, name+'_pouchL')
    box('Chest', (0.2,0.3,1.2), (0.19,0.09,0.14), mat_black, name+'_pouchR')
    cyl_between('Chest', (0,0,0.92), (0,0,1.04), 0.46, mat_black, name+'_belt')
    sphere('Chest', (0,0.34,1.52), 0.07, mat_glow, name+'_insignia')
    # Cabeza: rostro + casco + ala
    sphere('Head', (0,0,1.86), 0.26, mat_skin, name+'_face')
    sphere('Head', (0,0,1.96), 0.32, mat_gr, name+'_helmet', squash=(1,1,0.78))
    cyl_between('Head', (-0.31,0,1.9), (0.31,0,1.9), 0.035, mat_dark, name+'_brim')
    box('Head', (0,0.22,1.88), (0.3,0.07,0.07), mat_glow, name+'_visor')
    # Hombreras + brazos + rifle
    sphere('L_UpperArm', (-0.29,0,1.52), 0.17, mat_gr, name+'_shL')
    sphere('R_UpperArm', (0.29,0,1.52), 0.17, mat_gr, name+'_shR')
    cyl_between('L_UpperArm', (-0.28,0,1.48), (-0.88,0,1.1), 0.13, mat_gr, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.88,0,1.1), (-1.26,0,0.8), 0.11, mat_gr, name+'_foreL')
    sphere('L_ForeArm', (-1.3,0,0.75), 0.15, mat_skin, name+'_fistL')
    cyl_between('R_UpperArm', (0.28,0,1.48), (0.88,0,1.1), 0.13, mat_gr, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.88,0,1.1), (1.26,0,0.8), 0.11, mat_gr, name+'_foreR')
    # Rifle en brazo derecho: cuerpo + cañón + mira
    cyl_between('R_ForeArm', (0.95,0,1.02), (1.5,0,0.68), 0.045, mat_black, name+'_rifleBody')
    cyl_between('R_ForeArm', (1.42,0,0.7), (1.86,0,0.55), 0.028, mat_black, name+'_rifleBarrel')
    box('R_ForeArm', (1.24,0,1.06), (0.1,0.05,0.08), mat_dark, name+'_scope')
    # Piernas
    cyl_between('L_Thigh', (-0.3,0,0.82), (-0.38,0,0.42), 0.15, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.38,0,0.4), (-0.4,0,0.05), 0.13, mat_dark, name+'_shinL')
    sphere('L_Shin', (-0.4,0.07,0.03), 0.17, mat_black, name+'_bootL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.3,0,0.82), (0.38,0,0.42), 0.15, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.38,0,0.4), (0.4,0,0.05), 0.13, mat_dark, name+'_shinR')
    sphere('R_Shin', (0.4,0.07,0.03), 0.17, mat_black, name+'_bootR', squash=(1,1.4,0.55))
    # Mochila
    cyl_between('Chest', (0,-0.45,1.1), (0,-0.45,1.62), 0.2, mat_gr, name+'_pack')

def build_ninja(name):
    clear_scene()
    build_armature()
    mat_cloth = make_mat(name+'_cloth', (0.04,0.04,0.08), metallic=0.1, roughness=0.8)
    mat_trim = make_mat(name+'_trim', (0.35,0.12,0.55), metallic=0.3, roughness=0.5)
    mat_dark = make_mat(name+'_dark', (0.02,0.02,0.04), metallic=0.2, roughness=0.7)
    mat_glow = make_mat(name+'_glow', (1.0,0.15,0.15), metallic=0.0, roughness=0.4, emissive=(1.0,0.15,0.15), strength=4.0)
    mat_steel = make_mat(name+'_steel', (0.6,0.65,0.75), metallic=0.95, roughness=0.2)
    # Cuerpo esbelto
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.34, mat_cloth, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.58), 0.38, mat_cloth, name+'_chest')
    sphere('Chest', (0,0,1.05), 0.38, mat_cloth, name+'_chestBot')
    sphere('Chest', (0,0,1.58), 0.38, mat_cloth, name+'_chestTop')
    cyl_between('Chest', (0,0,0.92), (0,0,1.02), 0.36, mat_trim, name+'_belt')
    box('Chest', (0,0.32,1.3), (0.34,0.08,0.1), mat_trim, name+'_strap')
    sphere('Chest', (0,0.36,1.45), 0.08, mat_glow, name+'_emblem')
    # Cabeza con capucha
    sphere('Head', (0,0,1.86), 0.24, mat_dark, name+'_face')
    sphere('Head', (0,0,1.92), 0.32, mat_cloth, name+'_hood', squash=(1,1,1.15))
    box('Head', (0,0.24,1.88), (0.32,0.06,0.06), mat_glow, name+'_eyes')
    # Cintas de la cinta en la espalda
    cyl_between('Head', (-0.1,-0.2,2.0), (-0.18,-0.55,1.55), 0.025, mat_trim, name+'_tailL')
    cyl_between('Head', (0.12,-0.2,2.0), (0.2,-0.5,1.6), 0.025, mat_trim, name+'_tailR')
    # Brazos delgados + kunai
    cyl_between('L_UpperArm', (-0.26,0,1.48), (-0.82,0,1.1), 0.11, mat_cloth, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.82,0,1.1), (-1.2,0,0.8), 0.09, mat_cloth, name+'_foreL')
    sphere('L_ForeArm', (-1.26,0,0.75), 0.13, mat_dark, name+'_fistL')
    cyl_between('R_UpperArm', (0.26,0,1.48), (0.82,0,1.1), 0.11, mat_cloth, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.82,0,1.1), (1.2,0,0.8), 0.09, mat_cloth, name+'_foreR')
    sphere('R_ForeArm', (1.26,0,0.75), 0.13, mat_dark, name+'_fistR')
    cyl_between('R_ForeArm', (1.28,0,0.72), (1.48,0,0.6), 0.02, mat_steel, name+'_kunai')
    box('R_ForeArm', (1.24,0,0.76), (0.08,0.04,0.1), mat_trim, name+'_kunaiGrip')
    # Piernas
    cyl_between('L_Thigh', (-0.26,0,0.82), (-0.34,0,0.42), 0.13, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.34,0,0.4), (-0.36,0,0.05), 0.11, mat_dark, name+'_shinL')
    sphere('L_Shin', (-0.36,0.07,0.03), 0.15, mat_cloth, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.26,0,0.82), (0.34,0,0.42), 0.13, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.34,0,0.4), (0.36,0,0.05), 0.11, mat_dark, name+'_shinR')
    sphere('R_Shin', (0.36,0.07,0.03), 0.15, mat_cloth, name+'_footR', squash=(1,1.4,0.55))

def build_samurai(name):
    clear_scene()
    build_armature()
    mat_armor = make_mat(name+'_armor', (0.38,0.07,0.09), metallic=0.55, roughness=0.35)
    mat_gold = make_mat(name+'_gold', (0.85,0.6,0.15), metallic=0.9, roughness=0.25)
    mat_dark = make_mat(name+'_dark', (0.08,0.05,0.05), metallic=0.3, roughness=0.6)
    mat_skin = make_mat(name+'_skin', (0.79,0.58,0.42), metallic=0.05, roughness=0.65)
    mat_glow = make_mat(name+'_glow', (1.0,0.75,0.2), metallic=0.0, roughness=0.4, emissive=(1.0,0.75,0.2), strength=3.5)
    mat_steel = make_mat(name+'_steel', (0.65,0.7,0.78), metallic=0.95, roughness=0.18)
    # Torso blindado
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.42, mat_dark, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.6), 0.5, mat_armor, name+'_chest')
    sphere('Chest', (0,0,1.05), 0.48, mat_armor, name+'_chestBot')
    sphere('Chest', (0,0,1.6), 0.5, mat_armor, name+'_chestTop')
    cyl_between('Chest', (0,0,0.92), (0,0,1.02), 0.5, mat_gold, name+'_belt')
    box('Chest', (0,0.42,1.35), (0.2,0.06,0.3), mat_gold, name+'_crest')
    sphere('Chest', (0,0.42,1.5), 0.09, mat_glow, name+'_mon')
    # Hombreras grandes (sode)
    sphere('L_UpperArm', (-0.36,0,1.54), 0.3, mat_armor, name+'_sodeL', squash=(1.3,1,0.7))
    sphere('R_UpperArm', (0.36,0,1.54), 0.3, mat_armor, name+'_sodeR', squash=(1.3,1,0.7))
    # Brazos
    cyl_between('L_UpperArm', (-0.3,0,1.48), (-0.88,0,1.1), 0.13, mat_dark, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.88,0,1.1), (-1.26,0,0.8), 0.11, mat_dark, name+'_foreL')
    sphere('L_ForeArm', (-1.3,0,0.75), 0.15, mat_skin, name+'_fistL')
    cyl_between('R_UpperArm', (0.3,0,1.48), (0.88,0,1.1), 0.13, mat_dark, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.88,0,1.1), (1.26,0,0.8), 0.11, mat_dark, name+'_foreR')
    sphere('R_ForeArm', (1.3,0,0.75), 0.15, mat_skin, name+'_fistR')
    # Katana cruzada en la espalda
    cyl_between('Chest', (-0.45,-0.45,1.85), (0.5,-0.5,1.15), 0.035, mat_dark, name+'_katanaSheath')
    cyl_between('Chest', (0.42,-0.5,1.22), (0.55,-0.52,1.05), 0.04, mat_gold, name+'_katanaGrip')
    # Cabeza: casco kabuto con cuernos
    sphere('Head', (0,0,1.86), 0.26, mat_skin, name+'_face')
    sphere('Head', (0,0,1.97), 0.33, mat_armor, name+'_kabuto', squash=(1,1,0.8))
    cyl_between('Head', (-0.28,0,2.15), (-0.5,0,2.45), 0.04, mat_gold, name+'_hornL')
    cyl_between('Head', (0.28,0,2.15), (0.5,0,2.45), 0.04, mat_gold, name+'_hornR')
    box('Head', (0,0.26,1.9), (0.3,0.06,0.06), mat_glow, name+'_visor')
    sphere('Head', (0,0,2.22), 0.09, mat_dark, name+'_topknot')
    # Piernas con suneate
    cyl_between('L_Thigh', (-0.3,0,0.82), (-0.38,0,0.42), 0.15, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.38,0,0.4), (-0.4,0,0.05), 0.13, mat_armor, name+'_shinL')
    sphere('L_Shin', (-0.4,0.07,0.03), 0.17, mat_dark, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.3,0,0.82), (0.38,0,0.42), 0.15, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.38,0,0.4), (0.4,0,0.05), 0.13, mat_armor, name+'_shinR')
    sphere('R_Shin', (0.4,0.07,0.03), 0.17, mat_dark, name+'_footR', squash=(1,1.4,0.55))

def build_gladiator(name):
    clear_scene()
    build_armature()
    mat_bronze = make_mat(name+'_bronze', (0.62,0.42,0.13), metallic=0.85, roughness=0.3)
    mat_leather = make_mat(name+'_leather', (0.3,0.18,0.09), metallic=0.1, roughness=0.75)
    mat_skin = make_mat(name+'_skin', (0.72,0.48,0.32), metallic=0.05, roughness=0.65)
    mat_red = make_mat(name+'_red', (0.7,0.08,0.08), metallic=0.1, roughness=0.6)
    mat_glow = make_mat(name+'_glow', (1.0,0.55,0.1), metallic=0.0, roughness=0.4, emissive=(1.0,0.55,0.1), strength=3.5)
    mat_steel = make_mat(name+'_steel', (0.65,0.7,0.78), metallic=0.95, roughness=0.18)
    # Torso musculoso grande
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.46, mat_leather, name+'_pelvis')
    cyl_between('Chest', (0,0,1.02), (0,0,1.62), 0.58, mat_bronze, name+'_chest')
    sphere('Chest', (0,0,1.05), 0.55, mat_bronze, name+'_chestBot')
    sphere('Chest', (0,0,1.62), 0.57, mat_bronze, name+'_chestTop')
    cyl_between('Chest', (0,0,0.9), (0,0,1.04), 0.52, mat_leather, name+'_belt')
    sphere('Chest', (0,0.5,1.45), 0.13, mat_glow, name+'_sun')
    # Falda de cuero (ptera)
    for i, ang in enumerate([0, 0.9, 1.8, 2.7, 3.6, 4.5, 5.4]):
        x = 0.44 * math.cos(ang); y = 0.44 * math.sin(ang)
        cyl_between('Spine', (x, y, 0.95), (x*1.25, y*1.25, 0.55), 0.09, mat_leather, name+f'_skirt{i}')
    # Casco con cresta roja
    sphere('Head', (0,0,1.86), 0.26, mat_skin, name+'_face')
    sphere('Head', (0,0,1.98), 0.33, mat_bronze, name+'_helmet', squash=(1,1,0.85))
    box('Head', (0,0,2.32), (0.07,0.5,0.35), mat_red, name+'_crest')
    box('Head', (0,0.24,1.88), (0.3,0.06,0.06), mat_glow, name+'_visor')
    # Brazos: izquierdo con escudo redondo, derecho con gladio
    sphere('L_UpperArm', (-0.36,0,1.54), 0.24, mat_bronze, name+'_shL')
    sphere('R_UpperArm', (0.36,0,1.54), 0.24, mat_bronze, name+'_shR')
    cyl_between('L_UpperArm', (-0.32,0,1.48), (-0.9,0,1.1), 0.16, mat_skin, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.9,0,1.1), (-1.28,0,0.8), 0.14, mat_skin, name+'_foreL')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.08, location=(-1.32,0.05,0.78), vertices=24)
    o = bpy.context.active_object; o.name = name+'_shield'; o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((1,0,0)).to_track_quat('Z', 'Y')
    o.data.materials.append(mat_bronze); assign(o, 'L_ForeArm')
    sphere('L_ForeArm', (-1.32,0.14,0.78), 0.09, mat_red, name+'_shieldBoss')
    cyl_between('R_UpperArm', (0.32,0,1.48), (0.9,0,1.1), 0.16, mat_skin, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.9,0,1.1), (1.28,0,0.8), 0.14, mat_skin, name+'_foreR')
    sphere('R_ForeArm', (1.32,0,0.75), 0.17, mat_skin, name+'_fistR')
    cyl_between('R_ForeArm', (1.34,0,0.72), (1.62,0,0.55), 0.035, mat_steel, name+'_gladio')
    box('R_ForeArm', (1.3,0,0.76), (0.09,0.05,0.12), mat_leather, name+'_gladioGrip')
    # Piernas
    cyl_between('L_Thigh', (-0.32,0,0.82), (-0.4,0,0.42), 0.18, mat_skin, name+'_thighL')
    cyl_between('L_Shin', (-0.4,0,0.4), (-0.42,0,0.05), 0.15, mat_bronze, name+'_shinL')
    sphere('L_Shin', (-0.42,0.08,0.03), 0.19, mat_leather, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.32,0,0.82), (0.4,0,0.42), 0.18, mat_skin, name+'_thighR')
    cyl_between('R_Shin', (0.4,0,0.4), (0.42,0,0.05), 0.15, mat_bronze, name+'_shinR')
    sphere('R_Shin', (0.42,0.08,0.03), 0.19, mat_leather, name+'_footR', squash=(1,1.4,0.55))

def build_titan2(name):
    # MECH PESADO: torso enorme, puños gigantes, mochila con cañones
    clear_scene(); build_armature()
    mat_body = make_mat(name+'_body', (0.13,0.32,0.85), metallic=0.8, roughness=0.25)
    mat_dark = make_mat(name+'_dark', (0.05,0.07,0.12), metallic=0.6, roughness=0.45)
    mat_steel = make_mat(name+'_steel', (0.62,0.68,0.78), metallic=0.95, roughness=0.15)
    mat_glow = make_mat(name+'_glow', (0.25,0.8,1.0), metallic=0.0, roughness=0.4, emissive=(0.25,0.8,1.0), strength=4.5)
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.55, mat_body, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.62), 0.64, mat_body, name+'_chest')
    sphere('Chest', (0,0,1.05), 0.6, mat_body, name+'_chestBot')
    sphere('Chest', (0,0,1.62), 0.62, mat_body, name+'_chestTop')
    box('Chest', (0,0.5,1.4), (0.5,0.1,0.4), mat_dark, name+'_plate')
    sphere('Chest', (0,0.58,1.42), 0.17, mat_glow, name+'_core')
    cyl_between('Chest', (-0.3,-0.55,1.1), (-0.3,-0.55,1.7), 0.13, mat_steel, name+'_cannonL')
    cyl_between('Chest', (0.3,-0.55,1.1), (0.3,-0.55,1.7), 0.13, mat_steel, name+'_cannonR')
    sphere('Head', (0,0,1.9), 0.36, mat_body, name+'_HEAD')
    box('Head', (0,0.32,1.92), (0.44,0.1,0.13), mat_glow, name+'_visor')
    cyl_between('Head', (-0.18,0,2.2), (-0.26,0,2.6), 0.03, mat_steel, name+'_antL')
    cyl_between('Head', (0.18,0,2.2), (0.26,0,2.6), 0.03, mat_steel, name+'_antR')
    sphere('L_UpperArm', (-0.45,0,1.55), 0.3, mat_steel, name+'_shL')
    sphere('R_UpperArm', (0.45,0,1.55), 0.3, mat_steel, name+'_shR')
    cyl_between('L_UpperArm', (-0.42,0,1.5), (-1.02,0,1.08), 0.2, mat_body, name+'_bicepsL')
    cyl_between('L_ForeArm', (-1.02,0,1.08), (-1.42,0,0.78), 0.18, mat_body, name+'_foreL')
    sphere('L_ForeArm', (-1.5,0,0.72), 0.28, mat_dark, name+'_fistL')
    cyl_between('R_UpperArm', (0.42,0,1.5), (1.02,0,1.08), 0.2, mat_body, name+'_bicepsR')
    cyl_between('R_ForeArm', (1.02,0,1.08), (1.42,0,0.78), 0.18, mat_body, name+'_foreR')
    sphere('R_ForeArm', (1.5,0,0.72), 0.28, mat_dark, name+'_fistR')
    cyl_between('L_Thigh', (-0.36,0,0.82), (-0.46,0,0.4), 0.24, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.46,0,0.4), (-0.48,0,0.05), 0.2, mat_dark, name+'_shinL')
    sphere('L_Shin', (-0.48,0.09,0.03), 0.24, mat_steel, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.36,0,0.82), (0.46,0,0.4), 0.24, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.46,0,0.4), (0.48,0,0.05), 0.2, mat_dark, name+'_shinR')
    sphere('R_Shin', (0.48,0.09,0.03), 0.24, mat_steel, name+'_footR', squash=(1,1.4,0.55))

def build_volt2(name):
    # BOT VELOZ: esbelto, aletas, cuchillas en los brazos, piernas largas
    clear_scene(); build_armature()
    mat_body = make_mat(name+'_body', (0.85,0.2,0.18), metallic=0.7, roughness=0.2)
    mat_dark = make_mat(name+'_dark', (0.08,0.05,0.08), metallic=0.5, roughness=0.5)
    mat_steel = make_mat(name+'_steel', (0.7,0.72,0.8), metallic=0.95, roughness=0.12)
    mat_glow = make_mat(name+'_glow', (1.0,0.5,0.05), metallic=0.0, roughness=0.4, emissive=(1.0,0.5,0.05), strength=4.5)
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.36, mat_body, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.6), 0.4, mat_body, name+'_chest')
    sphere('Chest', (0,0,1.6), 0.42, mat_body, name+'_chestTop')
    sphere('Chest', (0,0.36,1.42), 0.12, mat_glow, name+'_core')
    # Aletas dorsales
    box('Chest', (-0.14,-0.4,1.75), (0.04,0.5,0.55), mat_dark, name+'_finL')
    box('Chest', (0.14,-0.4,1.75), (0.04,0.5,0.55), mat_dark, name+'_finR')
    sphere('Head', (0,0,1.9), 0.3, mat_body, name+'_HEAD')
    box('Head', (0,0.26,1.92), (0.38,0.08,0.1), mat_glow, name+'_visor')
    box('Head', (0,-0.1,2.2), (0.3,0.34,0.06), mat_dark, name+'_mohawk')
    cyl_between('L_UpperArm', (-0.28,0,1.5), (-0.85,0,1.12), 0.11, mat_body, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.85,0,1.12), (-1.22,0,0.82), 0.09, mat_dark, name+'_foreL')
    box('L_ForeArm', (-1.32,0,0.78), (0.3,0.03,0.14), mat_steel, name+'_bladeL')
    cyl_between('R_UpperArm', (0.28,0,1.5), (0.85,0,1.12), 0.11, mat_body, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.85,0,1.12), (1.22,0,0.82), 0.09, mat_dark, name+'_foreR')
    box('R_ForeArm', (1.32,0,0.78), (0.3,0.03,0.14), mat_steel, name+'_bladeR')
    cyl_between('L_Thigh', (-0.24,0,0.82), (-0.3,0,0.42), 0.11, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.3,0,0.42), (-0.32,0,0.05), 0.09, mat_dark, name+'_shinL')
    sphere('L_Shin', (-0.32,0.07,0.03), 0.14, mat_body, name+'_footL', squash=(1,1.5,0.5))
    cyl_between('R_Thigh', (0.24,0,0.82), (0.3,0,0.42), 0.11, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.3,0,0.42), (0.32,0,0.05), 0.09, mat_dark, name+'_shinR')
    sphere('R_Shin', (0.32,0.07,0.03), 0.14, mat_body, name+'_footR', squash=(1,1.5,0.5))

def build_soldier2(name):
    # GUARDIA ANCESTRAL: armadura de piedra/bronce, casco hoplita, lanza
    clear_scene(); build_armature()
    mat_stone = make_mat(name+'_stone', (0.55,0.5,0.42), metallic=0.35, roughness=0.8)
    mat_bronze = make_mat(name+'_bronze', (0.7,0.48,0.16), metallic=0.85, roughness=0.3)
    mat_dark = make_mat(name+'_dark', (0.15,0.12,0.08), metallic=0.3, roughness=0.7)
    mat_glow = make_mat(name+'_glow', (0.4,0.9,0.6), metallic=0.0, roughness=0.4, emissive=(0.4,0.9,0.6), strength=3.0)
    mat_steel = make_mat(name+'_steel', (0.6,0.62,0.68), metallic=0.9, roughness=0.25)
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.42, mat_dark, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.6), 0.52, mat_stone, name+'_chest')
    sphere('Chest', (0,0,1.6), 0.52, mat_stone, name+'_chestTop')
    box('Chest', (0,0.44,1.35), (0.34,0.08,0.36), mat_bronze, name+'_plate')
    cylinder = cyl_between('Chest', (0,0,0.92), (0,0,1.04), 0.48, mat_bronze, name+'_belt')
    sphere('Head', (0,0,1.9), 0.3, mat_bronze, name+'_HEAD')
    box('Head', (0,0.26,1.92), (0.34,0.07,0.1), mat_glow, name+'_visor')
    box('Head', (0,-0.05,2.28), (0.06,0.44,0.3), mat_dark, name+'_crest')
    sphere('L_UpperArm', (-0.34,0,1.54), 0.2, mat_bronze, name+'_shL')
    sphere('R_UpperArm', (0.34,0,1.54), 0.2, mat_bronze, name+'_shR')
    cyl_between('L_UpperArm', (-0.3,0,1.5), (-0.88,0,1.1), 0.13, mat_stone, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.88,0,1.1), (-1.26,0,0.8), 0.11, mat_stone, name+'_foreL')
    sphere('L_ForeArm', (-1.3,0,0.75), 0.15, mat_dark, name+'_fistL')
    bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.07, location=(-1.3,0.08,0.78), vertices=20)
    o = bpy.context.active_object; o.name = name+'_shield'; o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((1,0,0)).to_track_quat('Z', 'Y')
    o.data.materials.append(mat_bronze); assign(o, 'L_ForeArm')
    cyl_between('R_UpperArm', (0.3,0,1.5), (0.88,0,1.1), 0.13, mat_stone, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.88,0,1.1), (1.26,0,0.8), 0.11, mat_stone, name+'_foreR')
    sphere('R_ForeArm', (1.3,0,0.75), 0.15, mat_dark, name+'_fistR')
    cyl_between('R_ForeArm', (1.32,0,0.72), (1.35,0,1.9), 0.03, mat_dark, name+'_spear')
    sphere('R_ForeArm', (1.35,0,2.0), 0.09, mat_steel, name+'_spearTip')
    cyl_between('L_Thigh', (-0.3,0,0.82), (-0.38,0,0.42), 0.15, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.38,0,0.4), (-0.4,0,0.05), 0.13, mat_stone, name+'_shinL')
    sphere('L_Shin', (-0.4,0.07,0.03), 0.17, mat_bronze, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.3,0,0.82), (0.38,0,0.42), 0.15, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.38,0,0.4), (0.4,0,0.05), 0.13, mat_stone, name+'_shinR')
    sphere('R_Shin', (0.4,0.07,0.03), 0.17, mat_bronze, name+'_footR', squash=(1,1.4,0.55))

def build_ninja2(name):
    # BOT SEGADOR: 4 brazos, guadaña, capucha metálica
    clear_scene(); build_armature()
    mat_body = make_mat(name+'_body', (0.1,0.1,0.16), metallic=0.6, roughness=0.35)
    mat_dark = make_mat(name+'_dark', (0.03,0.03,0.06), metallic=0.4, roughness=0.6)
    mat_steel = make_mat(name+'_steel', (0.72,0.75,0.82), metallic=0.95, roughness=0.12)
    mat_glow = make_mat(name+'_glow', (0.9,0.1,0.9), metallic=0.0, roughness=0.4, emissive=(0.9,0.1,0.9), strength=4.0)
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.38, mat_body, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.6), 0.44, mat_body, name+'_chest')
    sphere('Chest', (0,0,1.6), 0.44, mat_body, name+'_chestTop')
    sphere('Chest', (0,0.4,1.45), 0.1, mat_glow, name+'_core')
    sphere('Head', (0,0,1.9), 0.32, mat_dark, name+'_HEAD')
    sphere('Head', (0,0,1.98), 0.36, mat_body, name+'_hood', squash=(1,1,1.1))
    box('Head', (0,0.28,1.92), (0.34,0.06,0.08), mat_glow, name+'_eyes')
    cyl_between('L_UpperArm', (-0.3,0,1.52), (-0.88,0,1.12), 0.12, mat_body, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.88,0,1.12), (-1.26,0,0.82), 0.1, mat_body, name+'_foreL')
    sphere('L_ForeArm', (-1.3,0,0.76), 0.14, mat_dark, name+'_fistL')
    cyl_between('R_UpperArm', (0.3,0,1.52), (0.88,0,1.12), 0.12, mat_body, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.88,0,1.12), (1.26,0,0.82), 0.1, mat_body, name+'_foreR')
    sphere('R_ForeArm', (1.3,0,0.76), 0.14, mat_dark, name+'_fistR')
    # Brazos extra fijos en el pecho (4 brazos)
    cyl_between('Chest', (-0.4,0.1,1.3), (-1.0,0.3,1.05), 0.08, mat_dark, name+'_extraL')
    cyl_between('Chest', (0.4,0.1,1.3), (1.0,0.3,1.05), 0.08, mat_dark, name+'_extraR')
    sphere('Chest', (-1.06,0.32,1.02), 0.11, mat_steel, name+'_clawL')
    sphere('Chest', (1.06,0.32,1.02), 0.11, mat_steel, name+'_clawR')
    # Guadaña en el puño derecho
    cyl_between('R_ForeArm', (1.32,0,0.72), (1.38,0,1.95), 0.028, mat_dark, name+'_scythe')
    box('R_ForeArm', (1.62,0,1.95), (0.55,0.04,0.12), mat_steel, name+'_scytheBlade')
    cyl_between('L_Thigh', (-0.28,0,0.82), (-0.36,0,0.42), 0.14, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.36,0,0.42), (-0.38,0,0.05), 0.12, mat_dark, name+'_shinL')
    sphere('L_Shin', (-0.38,0.07,0.03), 0.16, mat_body, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.28,0,0.82), (0.36,0,0.42), 0.14, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.36,0,0.42), (0.38,0,0.05), 0.12, mat_dark, name+'_shinR')
    sphere('R_Shin', (0.38,0.07,0.03), 0.16, mat_body, name+'_footR', squash=(1,1.4,0.55))

def build_samurai2(name):
    # RONIN DEMONIO: hombrera gigante, cuernos enormes, falda de placas
    clear_scene(); build_armature()
    mat_armor = make_mat(name+'_armor', (0.25,0.05,0.12), metallic=0.6, roughness=0.3)
    mat_gold = make_mat(name+'_gold', (0.9,0.65,0.15), metallic=0.9, roughness=0.2)
    mat_dark = make_mat(name+'_dark', (0.05,0.04,0.08), metallic=0.4, roughness=0.6)
    mat_glow = make_mat(name+'_glow', (1.0,0.2,0.2), metallic=0.0, roughness=0.4, emissive=(1.0,0.2,0.2), strength=4.0)
    mat_steel = make_mat(name+'_steel', (0.68,0.72,0.8), metallic=0.95, roughness=0.15)
    cyl_between('Spine', (0,0,0.55), (0,0,1.05), 0.46, mat_dark, name+'_pelvis')
    cyl_between('Chest', (0,0,1.05), (0,0,1.62), 0.56, mat_armor, name+'_chest')
    sphere('Chest', (0,0,1.62), 0.55, mat_armor, name+'_chestTop')
    sphere('Chest', (0,0.48,1.45), 0.13, mat_glow, name+'_core')
    box('Chest', (0,0.46,1.2), (0.4,0.07,0.4), mat_gold, name+'_plate')
    for i, ang in enumerate([0.4, 1.5, 2.6, 3.7, 4.8, 5.9]):
        x = 0.48 * math.cos(ang); y = 0.48 * math.sin(ang)
        box('Spine', (x, y, 0.8), (0.3,0.06,0.5), mat_armor, name+f'_skirt{i}')
    sphere('Head', (0,0,1.92), 0.34, mat_dark, name+'_HEAD')
    sphere('Head', (0,0,2.04), 0.38, mat_armor, name+'_kabuto', squash=(1,1,0.75))
    cyl_between('Head', (-0.3,0,2.25), (-0.75,0,2.75), 0.05, mat_gold, name+'_hornL')
    cyl_between('Head', (0.3,0,2.25), (0.75,0,2.75), 0.05, mat_gold, name+'_hornR')
    box('Head', (0,0.3,1.94), (0.36,0.06,0.08), mat_glow, name+'_eyes')
    sphere('L_UpperArm', (-0.4,0,1.58), 0.34, mat_armor, name+'_sodeL', squash=(1.4,1,0.7))
    sphere('R_UpperArm', (0.4,0,1.58), 0.42, mat_gold, name+'_sodeR', squash=(1.5,1,0.75))
    cyl_between('L_UpperArm', (-0.34,0,1.52), (-0.92,0,1.1), 0.14, mat_dark, name+'_bicepsL')
    cyl_between('L_ForeArm', (-0.92,0,1.1), (-1.3,0,0.8), 0.12, mat_dark, name+'_foreL')
    sphere('L_ForeArm', (-1.34,0,0.75), 0.16, mat_dark, name+'_fistL')
    cyl_between('R_UpperArm', (0.34,0,1.52), (0.92,0,1.1), 0.14, mat_dark, name+'_bicepsR')
    cyl_between('R_ForeArm', (0.92,0,1.1), (1.3,0,0.8), 0.12, mat_dark, name+'_foreR')
    sphere('R_ForeArm', (1.34,0,0.75), 0.16, mat_dark, name+'_fistR')
    cyl_between('Chest', (-0.5,-0.5,1.9), (0.55,-0.55,1.1), 0.04, mat_dark, name+'_odachi')
    cyl_between('L_Thigh', (-0.32,0,0.82), (-0.4,0,0.42), 0.16, mat_dark, name+'_thighL')
    cyl_between('L_Shin', (-0.4,0,0.4), (-0.42,0,0.05), 0.14, mat_armor, name+'_shinL')
    sphere('L_Shin', (-0.42,0.08,0.03), 0.18, mat_dark, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.32,0,0.82), (0.4,0,0.42), 0.16, mat_dark, name+'_thighR')
    cyl_between('R_Shin', (0.4,0,0.4), (0.42,0,0.05), 0.14, mat_armor, name+'_shinR')
    sphere('R_Shin', (0.42,0.08,0.03), 0.18, mat_dark, name+'_footR', squash=(1,1.4,0.55))

def build_gladiator2(name):
    # COLOSO DE PIEDRA: escala gigante, grietas de lava, cadenas
    clear_scene(); build_armature()
    mat_stone = make_mat(name+'_stone', (0.32,0.3,0.28), metallic=0.2, roughness=0.95)
    mat_lava = make_mat(name+'_lava', (1.0,0.35,0.05), metallic=0.0, roughness=0.5, emissive=(1.0,0.35,0.05), strength=3.5)
    mat_dark = make_mat(name+'_dark', (0.1,0.1,0.1), metallic=0.3, roughness=0.8)
    mat_steel = make_mat(name+'_steel', (0.5,0.52,0.58), metallic=0.9, roughness=0.3)
    cyl_between('Spine', (0,0,0.55), (0,0,1.08), 0.62, mat_stone, name+'_pelvis')
    cyl_between('Chest', (0,0,1.08), (0,0,1.72), 0.72, mat_stone, name+'_chest')
    sphere('Chest', (0,0,1.08), 0.68, mat_stone, name+'_chestBot')
    sphere('Chest', (0,0,1.72), 0.7, mat_stone, name+'_chestTop')
    # Grietas de lava en el pecho
    box('Chest', (-0.2,0.62,1.3), (0.08,0.06,0.5), mat_lava, name+'_crack1')
    box('Chest', (0.25,0.6,1.5), (0.06,0.06,0.35), mat_lava, name+'_crack2')
    box('Chest', (0,0.65,1.05), (0.5,0.06,0.08), mat_lava, name+'_crack3')
    sphere('Head', (0,0,2.02), 0.4, mat_stone, name+'_HEAD')
    box('Head', (0,0.36,2.04), (0.4,0.08,0.12), mat_lava, name+'_eyes')
    cyl_between('Head', (-0.2,0,2.38), (-0.3,0,2.7), 0.04, mat_dark, name+'_hornL')
    cyl_between('Head', (0.2,0,2.38), (0.3,0,2.7), 0.04, mat_dark, name+'_hornR')
    sphere('L_UpperArm', (-0.5,0,1.68), 0.36, mat_stone, name+'_shL')
    sphere('R_UpperArm', (0.5,0,1.68), 0.36, mat_stone, name+'_shR')
    cyl_between('L_UpperArm', (-0.48,0,1.62), (-1.15,0,1.15), 0.24, mat_stone, name+'_bicepsL')
    cyl_between('L_ForeArm', (-1.15,0,1.15), (-1.6,0,0.82), 0.2, mat_stone, name+'_foreL')
    sphere('L_ForeArm', (-1.68,0,0.76), 0.3, mat_dark, name+'_fistL')
    cyl_between('R_UpperArm', (0.48,0,1.62), (1.15,0,1.15), 0.24, mat_stone, name+'_bicepsR')
    cyl_between('R_ForeArm', (1.15,0,1.15), (1.6,0,0.82), 0.2, mat_stone, name+'_foreR')
    sphere('R_ForeArm', (1.68,0,0.76), 0.3, mat_dark, name+'_fistR')
    cyl_between('R_ForeArm', (1.72,0,0.72), (2.05,0,0.5), 0.05, mat_steel, name+'_chain')
    cyl_between('L_Thigh', (-0.42,0,0.82), (-0.54,0,0.4), 0.28, mat_stone, name+'_thighL')
    cyl_between('L_Shin', (-0.54,0,0.4), (-0.56,0,0.05), 0.22, mat_stone, name+'_shinL')
    sphere('L_Shin', (-0.56,0.1,0.03), 0.28, mat_dark, name+'_footL', squash=(1,1.4,0.55))
    cyl_between('R_Thigh', (0.42,0,0.82), (0.54,0,0.4), 0.28, mat_stone, name+'_thighR')
    cyl_between('R_Shin', (0.54,0,0.4), (0.56,0,0.05), 0.22, mat_stone, name+'_shinR')
    sphere('R_Shin', (0.56,0.1,0.03), 0.28, mat_dark, name+'_footR', squash=(1,1.4,0.55))

def main():
    out = 'C:/c/Users/USUARIO/ai-robot-fight/assets/models'
    # ── NUEVOS DISEÑOS 3D (v2): siluetas robóticas/antiguas ──
    build_titan2('titan')
    make_actions()
    export_glb(out + '/titan.glb')
    build_volt2('volt')
    make_actions()
    export_glb(out + '/volt.glb')
    build_soldier2('soldier')
    make_actions()
    export_glb(out + '/soldier.glb')
    build_ninja2('ninja')
    make_actions()
    export_glb(out + '/ninja.glb')
    build_samurai2('samurai')
    make_actions()
    export_glb(out + '/samurai.glb')
    build_gladiator2('gladiator')
    make_actions()
    export_glb(out + '/gladiator.glb')
    print('DONE glTF export v2')

main()
