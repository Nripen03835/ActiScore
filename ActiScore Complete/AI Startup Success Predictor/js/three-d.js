// Three.js 3D visualization
let scene, camera, renderer, controls;
let isRotating = false;
let animationId;

function init3DVisualization() {
    // Set up the scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f2f5);
    
    // Set up the camera
    const container = document.getElementById('three-d-scene');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 15;
    camera.position.y = 10;
    
    // Set up the renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    container.appendChild(renderer.domElement);
    
    // Add orbit controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    
    // Add lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 20, 15);
    scene.add(directionalLight);
    
    // Add a simple initial visualization
    createInitialVisualization();
    
    // Handle window resize
    window.addEventListener('resize', onWindowResize);
    
    // Set up control buttons
    document.getElementById('rotate-btn').addEventListener('click', toggleRotation);
    document.getElementById('reset-view-btn').addEventListener('click', resetView);
    
    // Start animation loop
    animate();
}

function createInitialVisualization() {
    // Clear existing objects
    while(scene.children.length > 0) { 
        scene.remove(scene.children[0]); 
    }
    
    // Add a simple placeholder until data is available
    const geometry = new THREE.BoxGeometry(5, 5, 5);
    const material = new THREE.MeshPhongMaterial({ 
        color: 0x4361ee,
        transparent: true,
        opacity: 0.7
    });
    const cube = new THREE.Mesh(geometry, material);
    scene.add(cube);
    
    // Add grid helper
    const gridHelper = new THREE.GridHelper(20, 20);
    scene.add(gridHelper);
    
    // Add axes helper
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
}

function update3DVisualization(prediction) {
    // Clear existing objects
    while(scene.children.length > 0) { 
        scene.remove(scene.children[0]); 
    }
    
    // Create a 3D bar chart based on prediction data
    create3DBarChart(prediction);
    
    // Add lighting (again, since we cleared the scene)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 20, 15);
    scene.add(directionalLight);
}

function create3DBarChart(prediction) {
    const forecast = prediction.forecast;
    const barWidth = 0.6;
    const gap = 0.2;
    
    // Create groups for different data types
    const revenueGroup = new THREE.Group();
    const profitGroup = new THREE.Group();
    const lossGroup = new THREE.Group();
    
    // Normalize data for 3D visualization
    const maxValue = Math.max(
        ...forecast.revenue,
        ...forecast.profit,
        ...forecast.loss
    );
    
    // Create bars for each month
    for (let i = 0; i < forecast.months.length; i++) {
        const xPos = i * (barWidth + gap) - (forecast.months.length * (barWidth + gap)) / 2;
        
        // Revenue bars (blue)
        if (forecast.revenue[i] > 0) {
            const revenueHeight = (forecast.revenue[i] / maxValue) * 10;
            const revenueGeometry = new THREE.BoxGeometry(barWidth, revenueHeight, barWidth);
            const revenueMaterial = new THREE.MeshPhongMaterial({ color: 0x4361ee });
            const revenueBar = new THREE.Mesh(revenueGeometry, revenueMaterial);
            revenueBar.position.set(xPos, revenueHeight / 2, 0);
            revenueGroup.add(revenueBar);
        }
        
        // Profit bars (green) - positioned behind revenue
        if (forecast.profit[i] > 0) {
            const profitHeight = (forecast.profit[i] / maxValue) * 10;
            const profitGeometry = new THREE.BoxGeometry(barWidth, profitHeight, barWidth);
            const profitMaterial = new THREE.MeshPhongMaterial({ color: 0x4cc9f0 });
            const profitBar = new THREE.Mesh(profitGeometry, profitMaterial);
            profitBar.position.set(xPos, profitHeight / 2, -barWidth - 0.1);
            profitGroup.add(profitBar);
        }
        
        // Loss bars (red) - positioned in front of revenue
        if (forecast.loss[i] > 0) {
            const lossHeight = (forecast.loss[i] / maxValue) * 10;
            const lossGeometry = new THREE.BoxGeometry(barWidth, lossHeight, barWidth);
            const lossMaterial = new THREE.MeshPhongMaterial({ color: 0xf72585 });
            const lossBar = new THREE.Mesh(lossGeometry, lossMaterial);
            lossBar.position.set(xPos, lossHeight / 2, barWidth + 0.1);
            lossGroup.add(lossBar);
        }
    }
    
    // Add groups to scene
    scene.add(revenueGroup);
    scene.add(profitGroup);
    scene.add(lossGroup);
    
    // Add grid and axes
    const gridHelper = new THREE.GridHelper(20, 20);
    scene.add(gridHelper);
    
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);
}

function toggleRotation() {
    isRotating = !isRotating;
    const button = document.getElementById('rotate-btn');
    button.textContent = isRotating ? 'Stop Rotation' : 'Rotate';
}

function resetView() {
    controls.reset();
    camera.position.z = 15;
    camera.position.y = 10;
}

function onWindowResize() {
    const container = document.getElementById('three-d-scene');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

function animate() {
    animationId = requestAnimationFrame(animate);
    
    if (isRotating) {
        scene.rotation.y += 0.005;
    }
    
    controls.update();
    renderer.render(scene, camera);
}

// Initialize 3D visualization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    init3DVisualization();
});