import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const canvas = document.getElementById("viewer");
const overlay = document.getElementById("overlay");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1e1e1e);

const camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.01, 1000);
camera.position.set(3, 3, 3);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(window.devicePixelRatio || 1);
renderer.setSize(window.innerWidth, window.innerHeight);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const VISTA_INICIAL = {
  posicion: new THREE.Vector3(3, 3, 3),
  objetivo: new THREE.Vector3(0, 0, 0),
};
controls.target.copy(VISTA_INICIAL.objetivo);

scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.2));
const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
dirLight.position.set(5, 10, 7);
scene.add(dirLight);
scene.add(new THREE.GridHelper(10, 20, 0x555555, 0x333333));

let modeloActual = null;
const marcadores = new Map(); // id -> THREE.Mesh
let modoAgregar = false;

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

// --- Navegación: zoom, rotación (órbita) y desplazamiento (pan) ---
// Se manipula la cámara directamente en vez de usar los métodos internos
// (privados) de OrbitControls, así el mismo código sirve tanto para los
// botones de Qt como para el teclado.
const ZOOM_FACTOR = 0.85;
const ZOOM_MIN = 0.2;
const ZOOM_MAX = 100;
const ROTATE_STEP = 0.12; // radianes
const PAN_STEP = 0.6; // fracción de la distancia a la cámara

function zoomStep(factor) {
  const offset = camera.position.clone().sub(controls.target);
  const distancia = THREE.MathUtils.clamp(offset.length() * factor, ZOOM_MIN, ZOOM_MAX);
  offset.setLength(distancia);
  camera.position.copy(controls.target).add(offset);
  controls.update();
}

function orbitStep(deltaTheta, deltaPhi) {
  const offset = camera.position.clone().sub(controls.target);
  const spherical = new THREE.Spherical().setFromVector3(offset);
  spherical.theta += deltaTheta;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi + deltaPhi, 0.01, Math.PI - 0.01);
  offset.setFromSpherical(spherical);
  camera.position.copy(controls.target).add(offset);
  controls.update();
}

function panStep(dx, dy) {
  const distancia = camera.position.distanceTo(controls.target);
  const paso = distancia * PAN_STEP * 0.1;
  const derecha = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion).multiplyScalar(dx * paso);
  const arriba = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion).multiplyScalar(dy * paso);
  camera.position.add(derecha).add(arriba);
  controls.target.add(derecha).add(arriba);
  controls.update();
}

function resetView() {
  camera.position.copy(VISTA_INICIAL.posicion);
  controls.target.copy(VISTA_INICIAL.objetivo);
  camera.lookAt(controls.target);
  controls.update();
}

function alPresionarTecla(event) {
  switch (event.key) {
    case "ArrowLeft":
      orbitStep(-ROTATE_STEP, 0);
      break;
    case "ArrowRight":
      orbitStep(ROTATE_STEP, 0);
      break;
    case "ArrowUp":
      orbitStep(0, -ROTATE_STEP);
      break;
    case "ArrowDown":
      orbitStep(0, ROTATE_STEP);
      break;
    case "w":
    case "W":
      panStep(0, 1);
      break;
    case "s":
    case "S":
      panStep(0, -1);
      break;
    case "a":
    case "A":
      panStep(-1, 0);
      break;
    case "d":
    case "D":
      panStep(1, 0);
      break;
    case "+":
    case "=":
      zoomStep(ZOOM_FACTOR);
      break;
    case "-":
    case "_":
      zoomStep(1 / ZOOM_FACTOR);
      break;
    case "r":
    case "R":
    case "Home":
      resetView();
      break;
    default:
      return;
  }
  event.preventDefault();
}

window.addEventListener("keydown", alPresionarTecla);

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function cargarModelo(url) {
  overlay.textContent = "Cargando modelo...";
  const loader = new GLTFLoader();
  loader.load(
    url,
    (gltf) => {
      if (modeloActual) {
        scene.remove(modeloActual);
      }
      modeloActual = gltf.scene;
      scene.add(modeloActual);
      overlay.textContent =
        "Arrastrar: orbitar. Rueda: zoom. Clic sobre un pin: ver detalle. " +
        "Teclado: flechas rotan, WASD desplaza, +/- zoom, R restablece vista.";
      if (window.bridge) {
        window.bridge.modelo_cargado();
      }
    },
    undefined,
    (error) => {
      overlay.textContent = "Error al cargar el modelo: " + (error && error.message ? error.message : error);
    }
  );
}

function crearEsferaMarcador() {
  const geometry = new THREE.SphereGeometry(0.06, 16, 16);
  const material = new THREE.MeshStandardMaterial({ color: 0xff5533 });
  return new THREE.Mesh(geometry, material);
}

function agregarMarcador(id, x, y, z, etiqueta) {
  const mesh = crearEsferaMarcador();
  mesh.position.set(x, y, z);
  mesh.userData.marcadorId = id;
  mesh.userData.etiqueta = etiqueta;
  scene.add(mesh);
  marcadores.set(id, mesh);
}

function eliminarMarcador(id) {
  const mesh = marcadores.get(id);
  if (mesh) {
    scene.remove(mesh);
    marcadores.delete(id);
  }
}

function limpiarMarcadores() {
  for (const mesh of marcadores.values()) {
    scene.remove(mesh);
  }
  marcadores.clear();
}

function setModoAgregar(activo) {
  modoAgregar = activo;
  overlay.textContent = activo
    ? "Modo agregar marcador: clic sobre el modelo para colocar un pin."
    : "Modo navegación.";
}

function alClicEnCanvas(event) {
  const rect = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const marcadorMeshes = Array.from(marcadores.values());
  const hitsMarcadores = raycaster.intersectObjects(marcadorMeshes, false);
  if (hitsMarcadores.length > 0) {
    const id = hitsMarcadores[0].object.userData.marcadorId;
    if (window.bridge) {
      window.bridge.marcador_click(id);
    }
    return;
  }

  if (modoAgregar && modeloActual) {
    const hits = raycaster.intersectObject(modeloActual, true);
    if (hits.length > 0) {
      const punto = hits[0].point;
      if (window.bridge) {
        window.bridge.solicitar_nuevo_marcador(punto.x, punto.y, punto.z);
      }
    }
  }
}

canvas.addEventListener("click", alClicEnCanvas);

// Expuesto para depuración/inspección (las variables del módulo no son
// visibles desde fuera; esto permite consultarlas, ej. con devtools remotos).
window.__viewer3d = { camera, controls, scene };

new QWebChannel(qt.webChannelTransport, (channel) => {
  window.bridge = channel.objects.bridge;
  window.bridge.cargar_modelo.connect(cargarModelo);
  window.bridge.agregar_marcador.connect(agregarMarcador);
  window.bridge.eliminar_marcador.connect(eliminarMarcador);
  window.bridge.limpiar_marcadores.connect(limpiarMarcadores);
  window.bridge.establecer_modo_agregar.connect(setModoAgregar);
  window.bridge.orbit_step.connect(orbitStep);
  window.bridge.pan_step.connect(panStep);
  window.bridge.zoom_step.connect(zoomStep);
  window.bridge.resetear_vista.connect(resetView);
});
