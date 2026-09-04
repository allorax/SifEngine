import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Box, RotateCcw, Play, Pause, Activity, Eye, Info, CheckCircle2, X } from 'lucide-react';

import { API_BASE } from '../config';

const CLUSTER_COLORS = [
  '#2563eb', // Royal Blue
  '#16a34a', // Emerald
  '#d97706', // Amber
  '#7c3aed', // Purple
  '#dc2626', // Crimson
  '#0284c7', // Sky Blue
  '#db2777', // Pink
  '#65a30d', // Lime
  '#64748b'  // Gray
];

export default function Cluster3DWindow() {
  const mountRef = useRef(null);
  const [data, setData] = useState({ points: [], centroids: [], total_points: 0 });
  const [loading, setLoading] = useState(true);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [activeClusterFilter, setActiveClusterFilter] = useState('ALL');
  
  // Auto-rotate state AND Ref for instant pause/play in animation loop
  const [autoRotate, setAutoRotate] = useState(true);
  const autoRotateRef = useRef(autoRotate);

  const [showCentroids, setShowCentroids] = useState(true);

  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const pointsMeshRef = useRef(null);
  const centroidsGroupRef = useRef(null);
  const reqIdRef = useRef(null);

  const isDraggingRef = useRef(false);
  const previousMousePositionRef = useRef({ x: 0, y: 0 });
  const cameraAngleRef = useRef({ theta: 0.8, phi: 0.6, radius: 35 });

  // Keep autoRotateRef in sync with state
  useEffect(() => {
    autoRotateRef.current = autoRotate;
  }, [autoRotate]);

  useEffect(() => {
    fetch3DEmbeddings();
  }, []);

  const fetch3DEmbeddings = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/clusters/3d-embeddings?max_points=2500`);
      if (!res.ok) throw new Error('Failed to fetch 3D map');
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error('3D fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (loading || !data.points || data.points.length === 0 || !mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight || 520;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#f8fafc');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    cameraRef.current = camera;
    updateCameraPosition();

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    rendererRef.current = renderer;

    mountRef.current.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x2563eb, 0.6);
    dirLight.position.set(20, 30, 20);
    scene.add(dirLight);

    const grid = new THREE.GridHelper(40, 20, 0xcbd5e1, 0xe2e8f0);
    grid.position.y = -12;
    scene.add(grid);

    buildPointCloud(scene);
    buildCentroids(scene);

    const animate = () => {
      reqIdRef.current = requestAnimationFrame(animate);

      // Check autoRotateRef.current dynamically so clicking Pause works instantly
      if (autoRotateRef.current && !isDraggingRef.current) {
        cameraAngleRef.current.theta += 0.0025;
        updateCameraPosition();
      }

      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!mountRef.current || !renderer || !camera) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight || 520;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (reqIdRef.current) cancelAnimationFrame(reqIdRef.current);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [loading, data]);

  useEffect(() => {
    if (!sceneRef.current || !pointsMeshRef.current) return;
    buildPointCloud(sceneRef.current);
  }, [activeClusterFilter]);

  useEffect(() => {
    if (centroidsGroupRef.current) {
      centroidsGroupRef.current.visible = showCentroids;
    }
  }, [showCentroids]);

  const updateCameraPosition = () => {
    if (!cameraRef.current) return;
    const { theta, phi, radius } = cameraAngleRef.current;
    cameraRef.current.position.x = radius * Math.sin(phi) * Math.sin(theta);
    cameraRef.current.position.y = radius * Math.cos(phi);
    cameraRef.current.position.z = radius * Math.sin(phi) * Math.cos(theta);
    cameraRef.current.lookAt(0, 0, 0);
  };

  const buildPointCloud = (scene) => {
    if (pointsMeshRef.current) {
      scene.remove(pointsMeshRef.current);
    }

    const filteredPoints = activeClusterFilter === 'ALL'
      ? data.points
      : data.points.filter(p => String(p.cluster_id) === String(activeClusterFilter));

    const count = filteredPoints.length;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    filteredPoints.forEach((p, i) => {
      positions[i * 3] = p.x;
      positions[i * 3 + 1] = p.y;
      positions[i * 3 + 2] = p.z;

      const cIndex = p.cluster_id > 0 ? (p.cluster_id - 1) % (CLUSTER_COLORS.length - 1) : CLUSTER_COLORS.length - 1;
      const hex = CLUSTER_COLORS[cIndex];
      const color = new THREE.Color(hex);

      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    });

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.35,
      vertexColors: true,
      transparent: true,
      opacity: 0.9,
      sizeAttenuation: true
    });

    const pointsMesh = new THREE.Points(geometry, material);
    pointsMesh.userData = { pointsList: filteredPoints };
    scene.add(pointsMesh);
    pointsMeshRef.current = pointsMesh;
  };

  const buildCentroids = (scene) => {
    if (centroidsGroupRef.current) scene.remove(centroidsGroupRef.current);

    const group = new THREE.Group();

    data.centroids.forEach((c) => {
      const [cx, cy, cz] = c.centroid;
      const cIndex = c.cluster_id > 0 ? (c.cluster_id - 1) % (CLUSTER_COLORS.length - 1) : CLUSTER_COLORS.length - 1;
      const hex = CLUSTER_COLORS[cIndex];

      const sphereGeo = new THREE.SphereGeometry(0.7, 16, 16);
      const sphereMat = new THREE.MeshBasicMaterial({ color: hex, wireframe: true });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      sphere.position.set(cx, cy, cz);

      group.add(sphere);
    });

    scene.add(group);
    centroidsGroupRef.current = group;
  };

  const handleMouseDown = (e) => {
    isDraggingRef.current = true;
    previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return;

    const deltaX = e.clientX - previousMousePositionRef.current.x;
    const deltaY = e.clientY - previousMousePositionRef.current.y;

    cameraAngleRef.current.theta -= deltaX * 0.004;
    cameraAngleRef.current.phi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraAngleRef.current.phi - deltaY * 0.004));

    updateCameraPosition();
    previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e) => {
    cameraAngleRef.current.radius = Math.max(10, Math.min(80, cameraAngleRef.current.radius + e.deltaY * 0.03));
    updateCameraPosition();
  };

  const handleClick = (e) => {
    if (!mountRef.current || !cameraRef.current || !pointsMeshRef.current) return;

    const rect = mountRef.current.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.params.Points.threshold = 0.6;
    raycaster.setFromCamera(mouse, cameraRef.current);

    const intersects = raycaster.intersectObject(pointsMeshRef.current);

    if (intersects.length > 0) {
      const idx = intersects[0].index;
      const pointsList = pointsMeshRef.current.userData.pointsList;
      if (pointsList && pointsList[idx]) {
        setSelectedPoint(pointsList[idx]);
      }
    }
  };

  const resetCamera = () => {
    cameraAngleRef.current = { theta: 0.8, phi: 0.6, radius: 35 };
    updateCameraPosition();
  };

  if (loading) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem' }}>
        <Activity className="animate-spin" style={{ width: 32, height: 32, color: 'var(--brand)', margin: '0 auto' }} />
        <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Loading 3D safety map...</p>
      </div>
    );
  }

  if (!data.points || data.points.length === 0) {
    return (
      <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem' }}>
        <Box style={{ width: 40, height: 40, color: 'var(--amber)', margin: '0 auto' }} />
        <h3 style={{ marginTop: '1rem', color: 'var(--text-main)' }}>No 3D Hazard Map Coordinates Found</h3>
        <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>
          No vector embeddings found in the database. Please trigger an analysis update from the top menu bar.
        </p>
        <button className="btn-primary" style={{ marginTop: '1.25rem' }} onClick={fetch3DEmbeddings}>
          <RotateCcw style={{ width: 14, height: 14 }} /> Reload 3D Spatial Map
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Feature 5 Banner */}
      <div className="insight-banner">
        <div>
          <div className="title">
            <CheckCircle2 style={{ width: 15, height: 15 }} /> Feature 5: Interactive 3D Spatial Hazard Map
          </div>
          <div className="text">
            Visual spatial mapping of 2,500 workplace safety incidents. Rotate with mouse, zoom, click any point to inspect incident details, or toggle auto-rotation.
          </div>
        </div>
      </div>

      {/* Header & Controls */}
      <div className="glass-panel" style={{ padding: '0.85rem 1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Box style={{ color: 'var(--brand)', width: 22, height: 22 }} />
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.05rem', color: 'var(--text-main)' }}>
                3D Workplace Hazard Map
              </div>
              <p className="subtitle">
                Interactive spatial cluster mapping
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <select
              value={activeClusterFilter}
              onChange={(e) => setActiveClusterFilter(e.target.value)}
              className="filter-select"
            >
              <option value="ALL">Show All Categories ({data.total_points} incidents)</option>
              {data.centroids.map(c => (
                <option key={c.cluster_id} value={c.cluster_id}>
                  {c.cluster_label} ({c.report_count} incidents)
                </option>
              ))}
            </select>

            {/* Auto-rotate button (FIXED BUG) */}
            <button className="btn-secondary" onClick={() => setAutoRotate(!autoRotate)}>
              {autoRotate ? <Pause style={{ width: 14, height: 14 }} /> : <Play style={{ width: 14, height: 14 }} />}
              {autoRotate ? 'Pause Rotation' : 'Auto Rotate'}
            </button>

            <button className="btn-secondary" onClick={() => setShowCentroids(!showCentroids)}>
              <Eye style={{ width: 14, height: 14 }} />
              {showCentroids ? 'Hide Indicators' : 'Show Indicators'}
            </button>

            <button className="btn-secondary" onClick={resetCamera}>
              <RotateCcw style={{ width: 14, height: 14 }} /> Reset View
            </button>
          </div>
        </div>
      </div>

      {/* 3D Canvas & Inspector Container */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedPoint ? '3fr 1fr' : '1fr', gap: '1.25rem', transition: 'all 0.3s ease' }}>
        {/* Canvas */}
        <div
          className="glass-panel"
          style={{ padding: 0, overflow: 'hidden', position: 'relative', height: 520, cursor: 'grab' }}
        >
          <div
            ref={mountRef}
            style={{ width: '100%', height: '100%' }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onWheel={handleWheel}
            onClick={handleClick}
          />

          <div style={{ position: 'absolute', bottom: 12, left: 16, background: 'rgba(255, 255, 255, 0.9)', padding: '0.45rem 0.85rem', borderRadius: 6, fontSize: '0.78rem', color: '#1e293b', border: '1px solid #e2e8f0', boxShadow: 'var(--shadow-sm)', pointerEvents: 'none', fontWeight: 500 }}>
            🖱️ <b>Drag mouse</b> to rotate | <b>Scroll</b> to zoom | <b>Click point</b> to inspect incident
          </div>

          <div style={{ position: 'absolute', top: 12, right: 16, background: 'rgba(255, 255, 255, 0.95)', padding: '0.65rem 0.85rem', borderRadius: 8, border: '1px solid #e2e8f0', boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 220, overflowY: 'auto' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 700 }}>
              HAZARD COLOR LEGEND
            </div>
            {data.centroids.map((c, i) => (
              <div key={c.cluster_id} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.78rem', color: '#334155', fontWeight: 500 }}>
                <span style={{ width: 9, height: 9, borderRadius: '50%', backgroundColor: CLUSTER_COLORS[i % CLUSTER_COLORS.length] }} />
                <span>{c.cluster_label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Inspector Panel */}
        {selectedPoint && (
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', maxHeight: 520 }}>
            <div className="panel-header">
              <div className="panel-title">
                <Info /> Incident Inspector
              </div>
              <button className="btn-secondary" style={{ padding: '0.2rem 0.5rem' }} onClick={() => setSelectedPoint(null)}>
                <X style={{ width: 14, height: 14 }} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>HAZARD CATEGORY</div>
                <div style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--brand)' }}>{selectedPoint.cluster_label}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>REPORT ID</div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-main)', fontWeight: 700 }}>#{selectedPoint.id}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>THREAT LEVEL</div>
                  <span className="risk-badge risk-high" style={{ fontSize: '0.75rem' }}>{selectedPoint.risk_score.toFixed(1)} /100</span>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>COMPANY EMPLOYER</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontWeight: 600 }}>{selectedPoint.employer}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>LOCATION</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-main)' }}>{selectedPoint.state}</div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>INCIDENT TYPE</div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{selectedPoint.event}</div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700, marginBottom: 4 }}>INCIDENT DESCRIPTION</div>
                <div style={{ fontSize: '0.82rem', color: '#1e293b', lineHeight: 1.45, background: '#f8fafc', padding: '0.75rem', borderRadius: 6, border: '1px solid #f1f5f9' }}>
                  "{selectedPoint.description}"
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
