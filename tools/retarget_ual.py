#!/usr/bin/env python3
"""F1: retarget UAL (Rigify DEF, T-pose) -> rig Mixamo HD (A-pose) + clips autorados.

Uso (Git Bash, raiz del repo):
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background \
      --factory-startup --offline-mode --python tools/retarget_ual.py -- --name ninja
  (--name ninja|soldier|ronin|all)

Metodo de retarget VERIFICADO empiricamente (ver tools/shots/cmp_*):
  pose_tgt_world_rot = pose_src_world_rot   (copia de orientacion mundo)
  La formula delta-desde-rest local del brief producia golpes LATERALES porque
  las rest poses difieren (HD=A brazos abajo, UAL=T brazos horizontales); la
  copia mundo iguala la pose absoluta de la fuente (jab al frente, sin torsion).
  Hips: traslacion escalada por altura_tgt/altura_src; Walk/Run in-place
  (se resta el drift horizontal acumulado, se conserva el bob vertical).

Solo toca assets/ y tools/. No modifica index.html ni archivos del juego.
"""
import bpy, sys, math, argparse
from mathutils import Matrix, Vector

ROOT = "C:/Users/USUARIO/Documents/Qoder/2026-11-12/b95e9f4b/pelea-IA-VS"
UAL = ROOT + "/tools/ual/AnimationLibrary_Godot_Standard.gltf"
SHOTS = ROOT + "/tools/shots"
FPS = 30

# UAL(Rigify) -> HD(Mixamo). Dedos omitidos (irrelevantes para combate).
MAP = {
 'DEF-hips':'Hips','DEF-spine.001':'Spine','DEF-spine.002':'Spine1','DEF-spine.003':'Spine2',
 'DEF-neck':'Neck','DEF-head':'Head','DEF-shoulder.L':'LeftShoulder','DEF-upper_arm.L':'LeftArm',
 'DEF-forearm.L':'LeftForeArm','DEF-hand.L':'LeftHand','DEF-shoulder.R':'RightShoulder','DEF-upper_arm.R':'RightArm',
 'DEF-forearm.R':'RightForeArm','DEF-hand.R':'RightHand','DEF-thigh.L':'LeftUpLeg','DEF-shin.L':'LeftLeg',
 'DEF-foot.L':'LeftFoot','DEF-toe.L':'LeftToeBase','DEF-thigh.R':'RightUpLeg','DEF-shin.R':'RightLeg',
 'DEF-foot.R':'RightFoot','DEF-toe.R':'RightToeBase',
}
REV = {v:k for k,v in MAP.items()}

# canon <- fuente UAL (11)
UAL_CLIPS = {
 'Idle2':'Idle_Loop','Punch1':'Punch_Jab','Punch2':'Punch_Cross','SwordAttack':'Sword_Attack',
 'Special_Cast':'Spell_Simple_Shoot','HitHigh':'Hit_Head','HitLow':'Hit_Chest',
 'JumpStart':'Jump_Start','JumpLoop':'Jump_Loop','JumpLand':'Jump_Land','Roll':'Roll',
}
# canon <- fuente Rodin (4, ya en rig Mixamo)
RODIN_CLIPS = {'Idle':'human_000014','Walk':'human_000029','Run':'human_000040','KO':'human_000069'}
LOOPS = {'Idle','Idle2','Walk','Run','Block'}
CANON = list(RODIN_CLIPS)+list(UAL_CLIPS)+['Kick','Uppercut','Hammer_Overhead','Block','Knockdown','Getup','Victory']


def log(*a): print("[retarget]", *a, flush=True)


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def topo(arm):
    depth = {}
    def d(n):
        if n in depth: return depth[n]
        b = arm.data.bones[n]
        depth[n] = 0 if not b.parent else d(b.parent.name)+1
        return depth[n]
    for b in arm.data.bones: d(b.name)
    return sorted([b.name for b in arm.data.bones], key=lambda n: depth[n])


class Rig:
    def __init__(self, hd_arm, hd_mesh, ual_arm):
        self.hd = hd_arm; self.mesh = hd_mesh; self.ual = ual_arm
        self.order = topo(hd_arm)
        self.obj_rot_inv = hd_arm.matrix_world.to_3x3().inverted()
        self.rest_rel = {b.name: (b.parent.matrix_local.inverted() @ b.matrix_local) if b.parent else None
                         for b in hd_arm.data.bones}
        for pb in hd_arm.pose.bones: pb.rotation_mode = 'QUATERNION'
        self.rest_tgt = self.rest_world(hd_arm)
        self.rest_src = self.rest_world(ual_arm) if ual_arm else None
        self.height = self.mesh_height()

    def rest_world(self, arm):
        arm.data.pose_position = 'REST'; bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); ev = arm.evaluated_get(dg)
        out = {b.name: (ev.matrix_world @ ev.pose.bones[b.name].matrix).copy() for b in arm.data.bones}
        arm.data.pose_position = 'POSE'; bpy.context.view_layer.update()
        return out

    def mesh_height(self):
        mn = 1e9; mx = -1e9
        for v in self.mesh.data.vertices:
            w = self.mesh.matrix_world @ v.co
            mn = min(mn, w.z); mx = max(mx, w.z)
        return mx-mn

    def set_world_rot(self, t, dwr, hips_delta=None):
        pb = self.hd.pose.bones[t]; b = self.hd.data.bones[t]
        base = (self.hd.pose.bones[b.parent.name].matrix @ self.rest_rel[t]) if b.parent else b.matrix_local.copy()
        M = (self.obj_rot_inv @ dwr).to_4x4()
        M.translation = base.translation + (hips_delta or Vector((0,0,0)))
        pb.matrix = M

    def clear_pose(self):
        for pb in self.hd.pose.bones: pb.matrix_basis = Matrix.Identity(4)


def normalize(rig):
    """Escala uniforme a altura 2.0, apply a armature+mesh (de-parent/re-parent)."""
    s = 2.0/rig.height
    hd, mesh = rig.hd, rig.mesh
    mw = mesh.matrix_world.copy()
    mesh.parent = None; mesh.matrix_world = mw
    hd.scale = (s,s,s); mesh.scale = (s,s,s)
    bpy.ops.object.select_all(action='DESELECT')
    hd.select_set(True); mesh.select_set(True)
    bpy.context.view_layer.objects.active = hd
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mesh.parent = hd; mesh.matrix_parent_inverse = hd.matrix_world.inverted()
    log("normalized scale", round(s,4), "-> height 2.0")


def hips_traj(rig, src_arm, action, bones_hips):
    src_arm.animation_data.action = action
    f0,f1 = action.frame_range
    pts = []
    for f in range(int(f0), int(f1)+1):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = src_arm.evaluated_get(dg)
        pts.append((ev.matrix_world @ ev.pose.bones[bones_hips].matrix).translation.copy())
    return pts


def bake(rig, src_arm, action, tgt_name, mapping, de_drift=False, hips_scale=1.0, hips_bone_src=None):
    """Re-bake a 30fps sobre el rig HD. mapping: src->tgt. world-copy rotations."""
    f0,f1 = action.frame_range
    src_arm.animation_data.action = action
    new = bpy.data.actions.new(tgt_name)
    rig.hd.animation_data.action = new
    rig.clear_pose()
    hb_src = hips_bone_src or ('DEF-hips' if src_arm is rig.ual else 'Hips')
    traj = hips_traj(rig, src_arm, action, hb_src) if de_drift else None
    if de_drift:
        n = len(traj)
        slope = Vector(((traj[-1].x-traj[0].x)/max(1,n-1), (traj[-1].y-traj[0].y)/max(1,n-1), 0))
        base_xy = Vector((traj[0].x, traj[0].y, 0))
    rest_hips_src = rig.rest_src[hb_src].translation if src_arm is rig.ual else rig.rest_tgt['Hips'].translation
    for i,f in enumerate(range(int(f0), int(f1)+1)):
        bpy.context.scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get(); ev = src_arm.evaluated_get(dg)
        sw = {}
        for s,t in mapping.items():
            pb = ev.pose.bones.get(s)
            if pb: sw[t] = (ev.matrix_world @ pb.matrix).copy()
        if 'Hips' not in sw: continue
        if de_drift:
            p = traj[i]
            d = Vector((p.x-base_xy.x-slope.x*i, p.y-base_xy.y-slope.y*i, p.z-traj[0].z))
        else:
            d = sw['Hips'].translation - rest_hips_src
        hips_delta = rig.obj_rot_inv @ (d*hips_scale)
        for t in rig.order:
            if t not in sw: continue
            rig.set_world_rot(t, sw[t].to_3x3(), hips_delta if t=='Hips' else None)
        for t in rig.order:
            if t not in sw: continue
            pb = rig.hd.pose.bones[t]
            pb.keyframe_insert('rotation_quaternion', frame=f)
            if t=='Hips': pb.keyframe_insert('location', frame=f)
    rig.hd.animation_data.action = None
    return new


# ---------------- procedural clips (world-space deltas sobre rest) ----------------
def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)

def author(rig, name, keys, hips_keys=None):
    """keys: list of (frame, {bone:(axis,deg)}). hips_keys: list of (frame, Vector world delta)."""
    new = bpy.data.actions.new(name)
    rig.hd.animation_data.action = new
    rig.clear_pose()
    frames = sorted(set([k[0] for k in keys] + ([h[0] for h in hips_keys] if hips_keys else [])))
    kd = {f: dict(b) for f,b in keys}
    hd = dict(hips_keys or [])
    for f in frames:
        rig.clear_pose()
        # hips first (root), then topo
        hdelta = hd.get(f, Vector((0,0,0)))
        for t in rig.order:
            spec = kd.get(f, {}).get(t)
            if t=='Hips':
                dwr = (rot(*spec) if spec else Matrix.Identity(3)) @ rig.rest_tgt[t].to_3x3()
                rig.set_world_rot(t, dwr, rig.obj_rot_inv @ hdelta)
            elif spec:
                dwr = rot(*spec) @ rig.rest_tgt[t].to_3x3()
                rig.set_world_rot(t, dwr)
        for t in rig.order:
            pb = rig.hd.pose.bones[t]
            pb.keyframe_insert('rotation_quaternion', frame=f)
            if t=='Hips': pb.keyframe_insert('location', frame=f)
    rig.hd.animation_data.action = None
    return new

X=(1,0,0); Y=(0,1,0); Z=(0,0,1)

def procedural(rig):
    out = {}
    # Kick roundhouse 24f strike f12
    out['Kick'] = author(rig,'Kick',[
        (1,{}),
        (6,{'RightUpLeg':(X,25),'Spine':(Z,-15),'RightLeg':(X,30)}),
        (12,{'RightUpLeg':(X,-70),'RightLeg':(X,-25),'Spine':(Z,25),'Spine1':(Z,15),'LeftArm':(X,-20)}),
        (18,{'RightUpLeg':(X,-20),'RightLeg':(X,20),'Spine':(Z,8)}),
        (24,{}),
    ],[(1,Vector((0,0,0))),(6,Vector((0,0,-0.03))),(12,Vector((0,0,0.06))),(18,Vector((0,0,0))),(24,Vector((0,0,0)))])
    # Uppercut 20f
    out['Uppercut'] = author(rig,'Uppercut',[
        (1,{}),
        (6,{'RightArm':(X,20),'RightForeArm':(X,40),'Spine':(X,10)}),
        (10,{'RightArm':(X,-130),'RightForeArm':(X,-20),'Spine':(X,-10),'Spine1':(X,-8)}),
        (16,{'RightArm':(X,-40),'RightForeArm':(X,20)}),
        (20,{}),
    ],[(1,Vector((0,0,0))),(6,Vector((0,0,-0.06))),(10,Vector((0,0,0.12))),(16,Vector((0,0,0.03))),(20,Vector((0,0,0)))])
    # Hammer_Overhead 28f strike f18
    out['Hammer_Overhead'] = author(rig,'Hammer_Overhead',[
        (1,{}),
        (10,{'LeftArm':(X,-170),'RightArm':(X,-170),'LeftForeArm':(X,-20),'RightForeArm':(X,-20),'Spine':(X,-10)}),
        (18,{'LeftArm':(X,-60),'RightArm':(X,-60),'LeftForeArm':(X,-10),'RightForeArm':(X,-10),'Spine':(X,25),'Spine1':(X,15)}),
        (28,{}),
    ],[(1,Vector((0,0,0))),(10,Vector((0,0,0.05))),(18,Vector((0,0,-0.08))),(28,Vector((0,0,0)))])
    # Block loop 30f
    out['Block'] = author(rig,'Block',[
        (1,{'LeftArm':(X,-45),'RightArm':(X,-45),'LeftForeArm':(X,-95),'RightForeArm':(X,-95),'Spine':(X,6)}),
        (15,{'LeftArm':(X,-48),'RightArm':(X,-48),'LeftForeArm':(X,-98),'RightForeArm':(X,-98),'Spine':(X,8)}),
        (30,{'LeftArm':(X,-45),'RightArm':(X,-45),'LeftForeArm':(X,-95),'RightForeArm':(X,-95),'Spine':(X,6)}),
    ],[(1,Vector((0,0,-0.02))),(15,Vector((0,0,0.0))),(30,Vector((0,0,-0.02)))])
    # Knockdown 20f (cae al suelo)
    out['Knockdown'] = author(rig,'Knockdown',[
        (1,{}),
        (8,{'Hips':(X,40),'Spine':(X,20),'LeftUpLeg':(X,-30),'RightUpLeg':(X,-30),'LeftLeg':(X,40),'RightLeg':(X,40)}),
        (20,{'Hips':(X,85),'Spine':(X,25),'Spine1':(X,15),'LeftUpLeg':(X,-60),'RightUpLeg':(X,-50),'LeftLeg':(X,70),'RightLeg':(X,60),'LeftArm':(X,-40),'RightArm':(X,-40)}),
    ],[(1,Vector((0,0,0))),(8,Vector((0,0.1,-0.35))),(20,Vector((0,0.25,-0.78)))])
    # Getup 24f (suelo -> idle)
    out['Getup'] = author(rig,'Getup',[
        (1,{'Hips':(X,85),'Spine':(X,25),'Spine1':(X,15),'LeftUpLeg':(X,-60),'RightUpLeg':(X,-50),'LeftLeg':(X,70),'RightLeg':(X,60),'LeftArm':(X,-40),'RightArm':(X,-40)}),
        (12,{'Hips':(X,40),'Spine':(X,30),'LeftUpLeg':(X,-50),'RightUpLeg':(X,-40),'LeftLeg':(X,60),'RightLeg':(X,50)}),
        (24,{}),
    ],[(1,Vector((0,0.25,-0.78))),(12,Vector((0,0.1,-0.35))),(24,Vector((0,0,0)))])
    # Victory 30f brazos arriba
    out['Victory'] = author(rig,'Victory',[
        (1,{}),
        (10,{'LeftArm':(X,-160),'RightArm':(X,-160),'LeftForeArm':(X,-15),'RightForeArm':(X,-15),'Spine':(X,-6)}),
        (20,{'LeftArm':(X,-165),'RightArm':(X,-165),'LeftForeArm':(X,-10),'RightForeArm':(X,-10),'Spine':(X,-8)}),
        (30,{'LeftArm':(X,-160),'RightArm':(X,-160),'LeftForeArm':(X,-15),'RightForeArm':(X,-15),'Spine':(X,-6)}),
    ],[(1,Vector((0,0,0))),(10,Vector((0,0,0.04))),(20,Vector((0,0,0.07))),(30,Vector((0,0,0.04)))])
    return out


def push_nla(rig, actions):
    ad = rig.hd.animation_data
    ad.action = None
    for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
    for name in CANON:
        act = actions[name]
        tr = ad.nla_tracks.new(); tr.name = name
        f0,f1 = act.frame_range
        st = tr.strips.new(name, int(f0), act)
        st.action_frame_start = f0; st.action_frame_end = f1
        st.frame_start = f0; st.frame_end = f1
    log("NLA tracks:", len(ad.nla_tracks))


def export_glb(rig, path):
    bpy.ops.object.select_all(action='DESELECT')
    rig.hd.select_set(True); rig.mesh.select_set(True)
    bpy.context.view_layer.objects.active = rig.hd
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True,
        export_animation_mode='NLA_TRACKS', export_nla_strips=True,
        export_skins=True, export_yup=True, export_apply=False,
        export_animations=True, export_force_sampling=True,
        export_def_bones=False, export_image_format='AUTO',
    )
    log("exported", path)


def previews(rig, actions):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'TEXTURE'
    sc.render.resolution_x = 480; sc.render.resolution_y = 480
    if sc.world is None: sc.world = bpy.data.worlds.new('W')
    sc.world.color = (0.05,0.05,0.08)
    camd = bpy.data.cameras.new('PC'); cam = bpy.data.objects.new('PC',camd)
    sc.collection.objects.link(cam); sc.camera = cam; camd.lens = 50
    rig.hd.hide_render = False; rig.mesh.hide_render = False
    def shoot(action, frame, loc, label):
        rig.hd.animation_data.action = action
        sc.frame_set(frame); bpy.context.view_layer.update()
        cam.location = Vector(loc); d = Vector((0,0,0.0))-cam.location
        cam.rotation_euler = d.to_track_quat('-Z','Y').to_euler()
        sc.render.filepath = SHOTS+"/"+label+".png"
        bpy.ops.render.render(write_still=True)
    n = rig.hd.name
    shoot(actions['Idle'], 40, (0,-5,0), "retarget_%s_idle_front"%NAME)
    shoot(actions['Punch1'], 10, (5,0,0), "retarget_%s_punch_side"%NAME)
    shoot(actions['Kick'], 12, (5,0,0), "retarget_%s_kick_side"%NAME)
    shoot(actions['Kick'], 12, (0,-5,0), "retarget_%s_kick_front"%NAME)
    shoot(actions['Walk'], 20, (5,0,0), "retarget_%s_walk_side"%NAME)
    shoot(actions['Block'], 15, (0,-5,0), "retarget_%s_block_front"%NAME)
    shoot(actions['Knockdown'], 20, (5,0,0), "retarget_%s_knockdown_side"%NAME)
    shoot(actions['Victory'], 20, (0,-5,0), "retarget_%s_victory_front"%NAME)
    rig.hd.animation_data.action = None
    log("previews done")


def build(name):
    global NAME
    NAME = name
    clear()
    bpy.ops.import_scene.gltf(filepath=ROOT+"/models/hd_rigged/%s.glb"%name)
    hd_arm = next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    hd_mesh = next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name=='model')
    bpy.ops.import_scene.gltf(filepath=UAL)
    ual_arm = next(o for o in bpy.context.scene.objects if o.type=='ARMATURE' and o.name!=hd_arm.name)
    for o in bpy.context.scene.objects:
        if o not in (hd_arm, hd_mesh):
            o.hide_render = True
    hd_arm.animation_data_clear(); hd_arm.animation_data_create()
    ual_arm.animation_data_create()
    rig = Rig(hd_arm, hd_mesh, ual_arm)
    normalize(rig)
    rig = Rig(hd_arm, hd_mesh, ual_arm)   # re-capture rest at final scale
    # fuente duplicada para re-bake de Rodin (evita conflicto misma-objeto accion)
    hd_src = hd_arm.copy(); hd_src.data = hd_arm.data.copy()
    bpy.context.scene.collection.objects.link(hd_src)
    hd_src.animation_data_create(); hd_src.hide_render = True
    actions = {}
    # Rodin: re-bake desde copia (identity) + in-place Walk/Run
    for canon, src in RODIN_CLIPS.items():
        act = bpy.data.actions.get(src)
        actions[canon] = bake(rig, hd_src, act, canon, {b:b for b in rig.order},
                              de_drift=(canon in ('Walk','Run')), hips_scale=1.0, hips_bone_src='Hips')
        log("rodin", canon, "<-", src)
    # UAL retarget
    hs = 2.0/1.83
    for canon, src in UAL_CLIPS.items():
        act = bpy.data.actions.get(src)
        if not act:
            log("MISSING UAL", src); continue
        actions[canon] = bake(rig, ual_arm, act, canon, MAP, de_drift=False, hips_scale=hs)
        log("ual", canon, "<-", src)
    # procedural
    actions.update(procedural(rig))
    log("procedural done")
    missing = [c for c in CANON if c not in actions]
    if missing: log("MISSING CANON", missing)
    push_nla(rig, actions)
    out = ROOT+"/tools/_work_%s.glb"%name
    export_glb(rig, out)
    previews(rig, actions)
    log("BUILD_OK", name, "clips", len(actions))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', default='ninja', choices=['ninja','soldier','ronin','all'])
    args = ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    names = ['ninja','soldier','ronin'] if args.name=='all' else [args.name]
    for n in names:
        build(n)
    print("ALL_DONE", flush=True)