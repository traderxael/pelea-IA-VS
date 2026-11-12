import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, prune, simplify, textureCompress } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import sharp from 'sharp';

const [, , input, output] = process.argv;
if (!input || !output) {
  console.error('usage: node rig-optimize.mjs input.glb output.glb');
  process.exit(2);
}

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const document = await io.read(input);
const root = document.getRoot();

// Three.js only supports 4 bone influences per vertex; the rigger emitted two
// sets (JOINTS_0/1). Keep the four strongest and renormalize so skinning is
// identical in the browser.
function mergeWeights(primitive) {
  const j0 = primitive.getAttribute('JOINTS_0');
  const w0 = primitive.getAttribute('WEIGHTS_0');
  const j1 = primitive.getAttribute('JOINTS_1');
  const w1 = primitive.getAttribute('WEIGHTS_1');
  if (!j0 || !w0) return;
  const count = j0.getCount();
  const J0 = j0.getArray();
  const W0 = w0.getArray();
  const J1 = j1 ? j1.getArray() : null;
  const W1 = w1 ? w1.getArray() : null;
  const outJ = new Uint16Array(count * 4);
  const outW = new Float32Array(count * 4);
  for (let i = 0; i < count; i++) {
    const pairs = [];
    for (let k = 0; k < 4; k++) {
      const weight = W0[i * 4 + k];
      if (weight > 0) pairs.push([J0[i * 4 + k], weight]);
    }
    if (J1 && W1) {
      for (let k = 0; k < 4; k++) {
        const weight = W1[i * 4 + k];
        if (weight > 0) pairs.push([J1[i * 4 + k], weight]);
      }
    }
    pairs.sort((a, b) => b[1] - a[1]);
    const top = pairs.slice(0, 4);
    let sum = 0;
    for (const pair of top) sum += pair[1];
    if (sum <= 0) sum = 1;
    for (let k = 0; k < 4; k++) {
      const pair = top[k];
      outJ[i * 4 + k] = pair ? pair[0] : 0;
      outW[i * 4 + k] = pair ? pair[1] / sum : 0;
    }
  }
  primitive.setAttribute('JOINTS_0', document.createAccessor().setType('VEC4').setArray(outJ));
  primitive.setAttribute('WEIGHTS_0', document.createAccessor().setType('VEC4').setArray(outW));
  if (j1) primitive.setAttribute('JOINTS_1', null);
  if (w1) primitive.setAttribute('WEIGHTS_1', null);
}

for (const mesh of root.listMeshes()) {
  for (const primitive of mesh.listPrimitives()) mergeWeights(primitive);
}

let triangles = 0;
for (const mesh of root.listMeshes()) {
  for (const primitive of mesh.listPrimitives()) {
    const indices = primitive.getIndices();
    triangles += (indices ? indices.getCount() : primitive.getAttribute('POSITION').getCount()) / 3;
  }
}
console.log('input triangles:', Math.round(triangles));

await MeshoptSimplifier.ready;
await document.transform(
  dedup(),
  simplify({ simplifier: MeshoptSimplifier, ratio: 0.05, error: 0.005, lockBorder: false }),
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [1024, 1024] }),
  prune()
);

await io.write(output, document);
console.log('wrote', output);
