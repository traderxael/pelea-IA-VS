import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
for (const path of process.argv.slice(2)) {
  const doc = await io.read(path);
  const root = doc.getRoot();
  let tris = 0;
  for (const m of root.listMeshes()) {
    for (const p of m.listPrimitives()) {
      const idx = p.getIndices();
      tris += (idx ? idx.getCount() : p.getAttribute('POSITION').getCount()) / 3;
    }
  }
  const anims = root.listAnimations().map((a) => ({
    name: a.getName(),
    channels: a.listChannels().length,
  }));
  const mats = root.listMaterials().map((m) => ({
    name: m.getName(),
    base: m.getBaseColorFactor(),
    tex: !!m.getBaseColorTexture(),
  }));
  const skins = root.listSkins().map((s) => s.listJoints().length);
  const joints = root.listSkins()[0] ? root.listSkins()[0].listJoints().map((j) => j.getName()) : [];
  console.log(JSON.stringify({
    path,
    tris: Math.round(tris),
    anims,
    skins,
    matCount: mats.length,
    mats: mats.slice(0, 8),
    texCount: root.listTextures().length,
    joints: joints.slice(0, 60),
  }));
}