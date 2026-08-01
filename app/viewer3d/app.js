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
        "Arrastrar: orbitar. Rueda: zoom. Clic izquierdo sobre un pin: ver detalle.";
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

new QWebChannel(qt.webChannelTransport, (channel) => {
  window.bridge = channel.objects.bridge;
  window.bridge.cargar_modelo.connect(cargarModelo);
  window.bridge.agregar_marcador.connect(agregarMarcador);
  window.bridge.eliminar_marcador.connect(eliminarMarcador);
  window.bridge.limpiar_marcadores.connect(limpiarMarcadores);
  window.bridge.establecer_modo_agregar.connect(setModoAgregar);
});
