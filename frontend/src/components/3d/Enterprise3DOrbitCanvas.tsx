import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { CustomerAssessment } from '../../types/simulator';

export type AstrolabePreset = 'PERSPECTIVE' | 'RADAR' | 'DANGER_ZONE';

export interface PlaybookManeuvers {
  execSponsor: boolean;    // +15%
  architect: boolean;      // +25%
  discount: boolean;       // +20%
  featureFreeze: boolean;  // +20%
}

interface Enterprise3DOrbitCanvasProps {
  assessments: CustomerAssessment[];
  selectedCustomerId?: string;
  onSelectCustomer: (assessment: CustomerAssessment) => void;
  playbookIntensity: number; // 0 - 100
  maneuvers?: PlaybookManeuvers;
  astrolabePreset?: AstrolabePreset;
  onPresetChange?: (preset: AstrolabePreset) => void;
  className?: string;
}

export const Enterprise3DOrbitCanvas: React.FC<Enterprise3DOrbitCanvasProps> = ({
  assessments,
  selectedCustomerId,
  onSelectCustomer,
  playbookIntensity,
  maneuvers = { execSponsor: false, architect: false, discount: false, featureFreeze: false },
  astrolabePreset = 'PERSPECTIVE',
  onPresetChange,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // HUD & Telemetry
  const [hoveredAssessment, setHoveredAssessment] = useState<CustomerAssessment | null>(null);
  const [fps, setFps] = useState<number>(60);
  const [orbitStats, setOrbitStats] = useState<{ yaw: number; pitch: number; zoom: number }>({ yaw: 35, pitch: 30, zoom: 36 });

  // Calculate cumulative intervention boost (0 - 100%)
  const maneuverBoost = 
    (maneuvers.execSponsor ? 15 : 0) +
    (maneuvers.architect ? 25 : 0) +
    (maneuvers.discount ? 20 : 0) +
    (maneuvers.featureFreeze ? 20 : 0);

  const totalIntervention = Math.min(100, Math.round(playbookIntensity + maneuverBoost * (1 - playbookIntensity / 100)));

  // Internal Three.js refs
  const threeRef = useRef<{
    scene: THREE.Scene;
    camera: THREE.PerspectiveCamera;
    renderer: THREE.WebGLRenderer;
    accountNodes: Map<string, { group: THREE.Group; baseRadius: number; currentRadius: number; angle: number; speed: number; mesh: THREE.Mesh; halo: THREE.Mesh; assessment: CustomerAssessment }>;
    tractorBeams: THREE.Line[];
    singularityMesh: THREE.Mesh;
    accretionRing: THREE.Mesh;
    targetCamPos: THREE.Vector3;
    targetLookAt: THREE.Vector3;
    currentLookAt: THREE.Vector3;
    sphericalCoords: { radius: number; theta: number; phi: number };
    isDragging: boolean;
    prevMouse: { x: number; y: number };
    raycaster: THREE.Raycaster;
    mouse: THREE.Vector2;
  } | null>(null);

  // Apply Camera Preset
  const applyPreset = useCallback((preset: AstrolabePreset) => {
    if (!threeRef.current) return;
    const { sphericalCoords, targetLookAt } = threeRef.current;

    if (preset === 'PERSPECTIVE') {
      sphericalCoords.radius = 38;
      sphericalCoords.theta = Math.PI / 4;
      sphericalCoords.phi = Math.PI / 3;
      targetLookAt.set(0, 0, 0);
    } else if (preset === 'RADAR') {
      sphericalCoords.radius = 42;
      sphericalCoords.theta = 0.01;
      sphericalCoords.phi = 0.25; // steep top-down overhead radar angle
      targetLookAt.set(0, 0, 0);
    } else if (preset === 'DANGER_ZONE') {
      sphericalCoords.radius = 18;
      sphericalCoords.theta = Math.PI / 3;
      sphericalCoords.phi = Math.PI / 2.5;
      targetLookAt.set(0, 0, 0);
    }
  }, []);

  useEffect(() => {
    applyPreset(astrolabePreset);
  }, [astrolabePreset, applyPreset]);

  // Main Three.js Lifecycle
  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    let width = container.clientWidth || 800;
    let height = container.clientHeight || 540;

    // 1. Scene with warm luxury French walnut & bronze atmosphere
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1c1917); // Stone-900 / deep warm walnut
    scene.fog = new THREE.FogExp2(0x1c1917, 0.012);

    // 2. Camera setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    const sphericalCoords = { radius: 38, theta: Math.PI / 4, phi: Math.PI / 3 };
    camera.position.set(
      sphericalCoords.radius * Math.sin(sphericalCoords.phi) * Math.sin(sphericalCoords.theta),
      sphericalCoords.radius * Math.cos(sphericalCoords.phi),
      sphericalCoords.radius * Math.sin(sphericalCoords.phi) * Math.cos(sphericalCoords.theta)
    );
    const targetLookAt = new THREE.Vector3(0, 0, 0);
    const currentLookAt = new THREE.Vector3(0, 0, 0);
    const targetCamPos = camera.position.clone();
    camera.lookAt(targetLookAt);

    // 3. WebGL Renderer with High Performance & Tone Mapping
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.35;

    // 4. Luxury Warm Studio Lighting
    const ambientLight = new THREE.AmbientLight(0xfef3c7, 0.45); // Warm amber ambient
    scene.add(ambientLight);

    const goldKeyLight = new THREE.DirectionalLight(0xfbbf24, 1.4); // Golden key
    goldKeyLight.position.set(25, 40, 25);
    scene.add(goldKeyLight);

    const bronzeFillLight = new THREE.PointLight(0xd97706, 2.0, 70);
    bronzeFillLight.position.set(-20, -10, -20);
    scene.add(bronzeFillLight);

    const emeraldSafeLight = new THREE.PointLight(0x10b981, 1.5, 60);
    emeraldSafeLight.position.set(20, 15, -20);
    scene.add(emeraldSafeLight);

    // 5. Concentric Astrolabe Brass / Gold Risk Rings with Precision Guide Rails
    const R_SAFE = 24.0;
    const R_WATCHLIST = 16.0;
    const R_DANGER = 8.0;

    const createRing = (radius: number, color: number, opacity: number) => {
      // 1. Semi-transparent illuminated orbital ribbon
      const ringGeo = new THREE.RingGeometry(radius - 0.14, radius + 0.14, 128);
      const ringMat = new THREE.MeshBasicMaterial({
        color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: opacity * 0.75,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = Math.PI / 2;
      scene.add(ringMesh);

      // 2. Precision Central Orbital Guide Rail Wire Loop
      const circlePoints: THREE.Vector3[] = [];
      const segments = 128;
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        circlePoints.push(new THREE.Vector3(Math.cos(theta) * radius, 0, Math.sin(theta) * radius));
      }
      const railGeo = new THREE.BufferGeometry().setFromPoints(circlePoints);
      const railMat = new THREE.LineBasicMaterial({
        color,
        transparent: true,
        opacity: Math.min(1.0, opacity + 0.35),
      });
      const railLine = new THREE.Line(railGeo, railMat);
      scene.add(railLine);

      // 3. Fine perimeter celestial tick marks
      const ticksCount = 64;
      const tickGeo = new THREE.BufferGeometry();
      const points: THREE.Vector3[] = [];
      for (let i = 0; i < ticksCount; i++) {
        const a = (i / ticksCount) * Math.PI * 2;
        const r1 = radius - 0.35;
        const r2 = radius + 0.35;
        points.push(new THREE.Vector3(Math.cos(a) * r1, 0, Math.sin(a) * r1));
        points.push(new THREE.Vector3(Math.cos(a) * r2, 0, Math.sin(a) * r2));
      }
      tickGeo.setFromPoints(points);
      const tickMat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: opacity * 0.45 });
      const tickLines = new THREE.LineSegments(tickGeo, tickMat);
      scene.add(tickLines);

      return ringMesh;
    };

    // Safe Outer Gold Ring (Radius 24) - Risk < 35
    createRing(R_SAFE, 0x10b981, 0.45);
    // Neutral Mid Brass Ring (Radius 16) - Risk 36-50
    createRing(R_WATCHLIST, 0xd97706, 0.45);
    // Danger Inner Ruby Ring (Radius 8) - Risk > 50
    createRing(R_DANGER, 0xdc2626, 0.7);

    // Subtle Ground Astrolabe Radial Lines
    const radialLinesGeo = new THREE.BufferGeometry();
    const radialPoints: THREE.Vector3[] = [];
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      radialPoints.push(new THREE.Vector3(Math.cos(a) * 8, 0, Math.sin(a) * 8));
      radialPoints.push(new THREE.Vector3(Math.cos(a) * 26, 0, Math.sin(a) * 26));
    }
    radialLinesGeo.setFromPoints(radialPoints);
    const radialMat = new THREE.LineBasicMaterial({ color: 0x78716c, transparent: true, opacity: 0.15 });
    scene.add(new THREE.LineSegments(radialLinesGeo, radialMat));

    // 6. Central Churn Singularity / Executive Emitter Beacon
    const singularityGeo = new THREE.SphereGeometry(2.4, 32, 32);
    const singularityMat = new THREE.MeshPhysicalMaterial({
      color: 0x292524,
      emissive: 0xdc2626,
      emissiveIntensity: 0.45,
      roughness: 0.2,
      metalness: 0.8,
      transparent: true,
      opacity: 0.9,
    });
    const singularityMesh = new THREE.Mesh(singularityGeo, singularityMat);
    scene.add(singularityMesh);

    // Accretion Disk / Beacon Ring
    const accretionGeo = new THREE.RingGeometry(3.0, 3.8, 48);
    const accretionMat = new THREE.MeshBasicMaterial({
      color: 0xd97706,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.7,
    });
    const accretionRing = new THREE.Mesh(accretionGeo, accretionMat);
    accretionRing.rotation.x = Math.PI / 2;
    scene.add(accretionRing);

    // 7. Celestial Account Spheres (30 Enterprise Accounts)
    const accountNodes = new Map<string, {
      group: THREE.Group;
      baseRadius: number;
      currentRadius: number;
      angle: number;
      speed: number;
      mesh: THREE.Mesh;
      halo: THREE.Mesh;
      assessment: CustomerAssessment;
    }>();

    // Group assessments by risk tier so accounts lock cleanly to their respective orbit line
    const lowRiskAccounts = assessments.filter((a) => a.risk_level === 'Low' || a.risk_score < 35);
    const medRiskAccounts = assessments.filter(
      (a) => (a.risk_level === 'Medium' || (a.risk_score >= 35 && a.risk_score <= 50)) && !lowRiskAccounts.includes(a)
    );
    const highRiskAccounts = assessments.filter(
      (a) => !lowRiskAccounts.includes(a) && !medRiskAccounts.includes(a)
    );

    assessments.forEach((assessment) => {
      const group = new THREE.Group();
      group.userData = { id: assessment.customer.customer_id, assessment };

      // Determine exact orbit track radius based on risk tier:
      // High Risk -> Event Horizon Ruby Ring (R_DANGER = 8)
      // Medium Risk -> Watchlist Brass Ring (R_WATCHLIST = 16)
      // Low Risk -> Safe Outer Gold Ring (R_SAFE = 24)
      const isHigh = highRiskAccounts.includes(assessment);
      const isMed = medRiskAccounts.includes(assessment);
      const baseRadius = isHigh ? R_DANGER : isMed ? R_WATCHLIST : R_SAFE;

      // Evenly distribute accounts along their respective orbit ring
      let tierIndex = 0;
      let tierTotal = 1;
      if (isHigh) {
        tierIndex = Math.max(0, highRiskAccounts.indexOf(assessment));
        tierTotal = highRiskAccounts.length || 1;
      } else if (isMed) {
        tierIndex = Math.max(0, medRiskAccounts.indexOf(assessment));
        tierTotal = medRiskAccounts.length || 1;
      } else {
        tierIndex = Math.max(0, lowRiskAccounts.indexOf(assessment));
        tierTotal = lowRiskAccounts.length || 1;
      }

      // Exact angle on the orbit track circle with phase offset to avoid overlap
      const angle = (tierIndex / tierTotal) * Math.PI * 2 + (isMed ? 0.45 : isHigh ? 0.9 : 0);
      const speed = 0.002 + ((tierIndex % 4) * 0.0004);

      // Celestial sphere size proportional to ARR ($80k -> 0.7, $1.4M -> 1.7)
      const arr = assessment.contract?.annual_contract_value || 120000;
      const sphereRadius = Math.max(0.7, Math.min(1.7, 0.7 + (arr / 1_500_000) * 1.0));

      // Color determined by baseline risk
      const colorHex = isHigh ? 0xdc2626 : isMed ? 0xd97706 : 0x10b981;

      // Celestial sphere mesh
      const sphereGeo = new THREE.SphereGeometry(sphereRadius, 24, 24);
      const sphereMat = new THREE.MeshPhysicalMaterial({
        color: colorHex,
        emissive: colorHex,
        emissiveIntensity: isHigh ? 0.45 : 0.2,
        roughness: 0.25,
        metalness: 0.75,
        transparent: true,
        opacity: 0.9,
      });
      const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
      group.add(sphereMesh);

      // Atmospheric Shield / Ring
      const shieldGeo = new THREE.RingGeometry(sphereRadius * 1.25, sphereRadius * 1.38, 32);
      const shieldMat = new THREE.MeshBasicMaterial({
        color: colorHex,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.5,
      });
      const shieldMesh = new THREE.Mesh(shieldGeo, shieldMat);
      shieldMesh.rotation.x = Math.PI / 2;
      group.add(shieldMesh);

      // Selection Halo
      const haloGeo = new THREE.RingGeometry(sphereRadius * 1.6, sphereRadius * 1.8, 32);
      const haloMat = new THREE.MeshBasicMaterial({
        color: 0xf59e0b,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: assessment.customer.customer_id === selectedCustomerId ? 0.9 : 0.0,
      });
      const halo = new THREE.Mesh(haloGeo, haloMat);
      halo.name = 'selectionHalo';
      halo.rotation.x = Math.PI / 2;
      group.add(halo);

      // Initial positioning - exactly on the orbit track line (Y = 0)
      group.position.set(
        Math.cos(angle) * baseRadius,
        0,
        Math.sin(angle) * baseRadius
      );

      scene.add(group);
      accountNodes.set(assessment.customer.customer_id, {
        group,
        baseRadius,
        currentRadius: baseRadius,
        angle,
        speed,
        mesh: sphereMesh,
        halo,
        assessment,
      });
    });

    // 8. Interactive Mouse Orbit & Raycaster
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2(-999, -999);
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouse = { x: e.clientX, y: e.clientY };
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      if (isDragging) {
        const dx = e.clientX - prevMouse.x;
        const dy = e.clientY - prevMouse.y;

        sphericalCoords.theta -= dx * 0.005;
        sphericalCoords.phi = Math.max(0.1, Math.min(Math.PI / 2 - 0.05, sphericalCoords.phi - dy * 0.005));
        prevMouse = { x: e.clientX, y: e.clientY };

        if (onPresetChange) onPresetChange('PERSPECTIVE');
      }
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      sphericalCoords.radius = Math.max(14, Math.min(65, sphericalCoords.radius + e.deltaY * 0.035));
      if (onPresetChange) onPresetChange('PERSPECTIVE');
    };

    const onClick = () => {
      raycaster.setFromCamera(mouse, camera);
      const objects: THREE.Object3D[] = [];
      accountNodes.forEach((node) => objects.push(node.mesh));

      const intersects = raycaster.intersectObjects(objects, false);
      if (intersects.length > 0) {
        const hit = intersects[0].object;
        let parent: THREE.Object3D | null = hit;
        while (parent && !parent.userData?.id) {
          parent = parent.parent;
        }
        if (parent && parent.userData?.assessment) {
          onSelectCustomer(parent.userData.assessment);
        }
      }
    };

    canvas.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    canvas.addEventListener('wheel', onWheel, { passive: false });
    canvas.addEventListener('click', onClick);

    // Resize Observer
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      width = container.clientWidth;
      height = container.clientHeight || 540;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // Save refs
    threeRef.current = {
      scene,
      camera,
      renderer,
      accountNodes,
      tractorBeams: [],
      singularityMesh,
      accretionRing,
      targetCamPos,
      targetLookAt,
      currentLookAt,
      sphericalCoords,
      isDragging,
      prevMouse,
      raycaster,
      mouse,
    };

    // 9. Kinetic Render Loop with Spring Physics
    let frameCount = 0;
    let fpsTimer = performance.now();
    let startTime = performance.now();
    let lastFrameTime = performance.now();

    const animate = () => {
      const now = performance.now();
      const delta = Math.min((now - lastFrameTime) / 1000, 0.1);
      lastFrameTime = now;
      const time = (now - startTime) / 1000;

      // FPS counter
      frameCount++;
      if (now - fpsTimer >= 1000) {
        setFps(frameCount);
        frameCount = 0;
        fpsTimer = now;
      }

      // Smooth Camera Spring Easing
      targetCamPos.set(
        sphericalCoords.radius * Math.sin(sphericalCoords.phi) * Math.sin(sphericalCoords.theta),
        sphericalCoords.radius * Math.cos(sphericalCoords.phi),
        sphericalCoords.radius * Math.sin(sphericalCoords.phi) * Math.cos(sphericalCoords.theta)
      );
      camera.position.lerp(targetCamPos, 0.08);
      currentLookAt.lerp(targetLookAt, 0.08);
      camera.lookAt(currentLookAt);

      // Update telemetry
      const yawDeg = Math.round((sphericalCoords.theta * 180) / Math.PI) % 360;
      const pitchDeg = Math.round((sphericalCoords.phi * 180) / Math.PI);
      const zoomVal = Math.round(sphericalCoords.radius);
      setOrbitStats({ yaw: yawDeg, pitch: pitchDeg, zoom: zoomVal });

      // Rotate Singularity & Accretion Ring
      singularityMesh.rotation.y += delta * 0.4;
      accretionRing.rotation.z += delta * 0.6;

      // Kinetic Turnaround Physics: Pull accounts outward toward Safe Gold Orbit
      // Target radius shifts cleanly between the 3 discrete orbital track lines
      accountNodes.forEach((node) => {
        node.angle += node.speed;

        // Baseline orbit tracks:
        // High Risk starts locked on R_DANGER (8.0)
        // Medium Risk starts locked on R_WATCHLIST (16.0)
        // Low Risk starts locked on R_SAFE (24.0)
        let targetRadius = node.baseRadius;

        if (node.assessment.risk_level === 'High' || node.assessment.risk_score > 50) {
          if (totalIntervention >= 65) {
            targetRadius = R_SAFE; // Rescued cleanly onto Outer Gold Orbit line (24.0)
          } else if (totalIntervention >= 30) {
            targetRadius = R_WATCHLIST; // Stabilized cleanly onto Mid Watchlist Brass line (16.0)
          } else if (totalIntervention > 0) {
            // Smooth transitional negative gravity pull between tracks
            targetRadius = R_DANGER + (totalIntervention / 30) * (R_WATCHLIST - R_DANGER);
          } else {
            targetRadius = R_DANGER; // Exactly on Event Horizon Ruby line (8.0)
          }
        } else if (node.assessment.risk_level === 'Medium' || (node.assessment.risk_score > 35 && node.assessment.risk_score <= 50)) {
          if (totalIntervention >= 45) {
            targetRadius = R_SAFE; // Rescued cleanly onto Outer Gold Orbit line (24.0)
          } else if (totalIntervention > 0) {
            targetRadius = R_WATCHLIST + (totalIntervention / 45) * (R_SAFE - R_WATCHLIST);
          } else {
            targetRadius = R_WATCHLIST; // Exactly on Mid Watchlist Brass line (16.0)
          }
        } else {
          targetRadius = R_SAFE; // Exactly on Outer Gold Orbit line (24.0)
        }

        // Spring interpolation for smooth physical tractor-beam pull
        node.currentRadius = THREE.MathUtils.lerp(node.currentRadius, targetRadius, 0.05);

        // Position nodes precisely on the plane of the orbit track lines
        node.group.position.x = Math.cos(node.angle) * node.currentRadius;
        node.group.position.z = Math.sin(node.angle) * node.currentRadius;
        node.group.position.y = 0; // Exactly on the orbital ring plane!

        // Color transition: as account reaches outer orbit, shift to emerald!
        const mat = node.mesh.material as THREE.MeshPhysicalMaterial;
        if (node.currentRadius >= 20.0) {
          mat.color.setHex(0x10b981);
          mat.emissive.setHex(0x10b981);
        } else if (node.currentRadius >= 12.0) {
          mat.color.setHex(0xd97706);
          mat.emissive.setHex(0xd97706);
        } else {
          mat.color.setHex(0xdc2626);
          mat.emissive.setHex(0xdc2626);
        }

        // Selection Halo animation
        const isSelected = node.assessment.customer.customer_id === selectedCustomerId;
        node.halo.visible = isSelected;
        if (isSelected) {
          node.halo.rotation.z -= delta * 1.2;
          const s = 1.0 + Math.sin(time * 5) * 0.08;
          node.halo.scale.set(s, s, s);
        }
      });

      // Raycasting for Hover Dossier Card
      raycaster.setFromCamera(mouse, camera);
      const objects: THREE.Object3D[] = [];
      accountNodes.forEach((node) => objects.push(node.mesh));

      const intersects = raycaster.intersectObjects(objects, false);
      let foundAssessment: CustomerAssessment | null = null;
      if (intersects.length > 0) {
        let parent: THREE.Object3D | null = intersects[0].object;
        while (parent && !parent.userData?.id) {
          parent = parent.parent;
        }
        if (parent && parent.userData?.assessment) {
          foundAssessment = parent.userData.assessment;
        }
      }
      setHoveredAssessment(foundAssessment);

      renderer.render(scene, camera);
    };

    renderer.setAnimationLoop(animate);

    // Pause on Tab Hidden (ui-ux-pro-max battery safeguard)
    const onVisibilityChange = () => {
      if (document.hidden) {
        renderer.setAnimationLoop(null);
      } else {
        lastFrameTime = performance.now();
        renderer.setAnimationLoop(animate);
      }
    };
    document.addEventListener('visibilitychange', onVisibilityChange);

    // Cleanup
    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      renderer.setAnimationLoop(null);
      resizeObserver.disconnect();

      canvas.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      canvas.removeEventListener('wheel', onWheel);
      canvas.removeEventListener('click', onClick);

      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh || obj instanceof THREE.Line || obj instanceof THREE.LineSegments) {
          obj.geometry?.dispose();
          if (Array.isArray(obj.material)) {
            obj.material.forEach((m) => m.dispose());
          } else {
            obj.material?.dispose();
          }
        }
      });
      renderer.dispose();
    };
  }, [assessments, selectedCustomerId, onSelectCustomer, onPresetChange, totalIntervention]);

  return (
    <div ref={containerRef} className={`relative w-full h-[540px] bg-[#1c1917] rounded-3xl overflow-hidden border border-[#d6c8ad]/60 shadow-2xl ${className}`}>
      {/* 3D Canvas */}
      <canvas ref={canvasRef} className="w-full h-full block cursor-grab active:cursor-grabbing select-none" />

      {/* Top Left: Luxury Astrolabe Telemetry Badge */}
      <div className="absolute top-4 left-4 flex items-center gap-2 pointer-events-none font-mono text-[11px]">
        <div className="px-3 py-1.5 rounded-full bg-[#292524]/90 border border-amber-900/60 text-amber-200 flex items-center gap-2 backdrop-blur-md shadow-lg">
          <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
          <span className="font-bold tracking-wider uppercase text-amber-400">DECISION ORBIT ASTROLABE</span>
          <span className="text-stone-600">|</span>
          <span>YAW: {orbitStats.yaw}°</span>
          <span>PITCH: {orbitStats.pitch}°</span>
          <span>DIST: {orbitStats.zoom}m</span>
        </div>
        <div className="px-2.5 py-1.5 rounded-full bg-[#292524]/90 border border-emerald-900/60 text-emerald-400 font-bold backdrop-blur-md">
          {fps} FPS
        </div>
      </div>

      {/* Top Right: Astrolabe Camera Presets */}
      <div className="absolute top-4 right-4 flex items-center gap-1.5 bg-[#292524]/90 border border-amber-900/60 p-1 rounded-2xl backdrop-blur-md shadow-lg">
        <button
          onClick={() => {
            applyPreset('PERSPECTIVE');
            if (onPresetChange) onPresetChange('PERSPECTIVE');
          }}
          className={`px-3 py-1 rounded-xl text-[11px] font-mono font-semibold transition-all cursor-pointer ${
            astrolabePreset === 'PERSPECTIVE'
              ? 'bg-amber-600 text-white shadow-[0_2px_10px_rgba(217,119,6,0.4)]'
              : 'text-stone-400 hover:text-white hover:bg-stone-800'
          }`}
        >
          Perspective 3D
        </button>
        <button
          onClick={() => {
            applyPreset('RADAR');
            if (onPresetChange) onPresetChange('RADAR');
          }}
          className={`px-3 py-1 rounded-xl text-[11px] font-mono font-semibold transition-all cursor-pointer ${
            astrolabePreset === 'RADAR'
              ? 'bg-amber-600 text-white shadow-[0_2px_10px_rgba(217,119,6,0.4)]'
              : 'text-stone-400 hover:text-white hover:bg-stone-800'
          }`}
        >
          Executive Radar
        </button>
        <button
          onClick={() => {
            applyPreset('DANGER_ZONE');
            if (onPresetChange) onPresetChange('DANGER_ZONE');
          }}
          className={`px-3 py-1 rounded-xl text-[11px] font-mono font-semibold transition-all cursor-pointer ${
            astrolabePreset === 'DANGER_ZONE'
              ? 'bg-rose-600 text-white shadow-[0_2px_10px_rgba(220,38,38,0.4)]'
              : 'text-stone-400 hover:text-white hover:bg-stone-800'
          }`}
        >
          Danger Zone
        </button>
      </div>

      {/* Bottom Left: Interactive Hover Caliper HUD Dossier */}
      {hoveredAssessment && (
        <div className="absolute bottom-4 left-4 p-4 rounded-2xl bg-[#292524]/95 border border-amber-500/50 shadow-2xl backdrop-blur-md pointer-events-none max-w-sm animate-in fade-in duration-150 space-y-2 font-sans text-xs">
          <div className="flex items-center justify-between gap-3 border-b border-stone-700 pb-2">
            <div>
              <div className="font-bold text-amber-300 font-display text-sm">
                {hoveredAssessment.customer.customer_name}
              </div>
              <div className="text-[11px] text-stone-400 font-mono">
                {hoveredAssessment.customer.industry} • {hoveredAssessment.customer.segment}
              </div>
            </div>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-bold ${
              hoveredAssessment.risk_level === 'Low' ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50' :
              hoveredAssessment.risk_level === 'Medium' ? 'bg-amber-900/60 text-amber-300 border border-amber-700/50' :
              'bg-rose-900/60 text-rose-300 border border-rose-700/50'
            }`}>
              {hoveredAssessment.risk_level.toUpperCase()} RISK
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-stone-300 font-mono text-[11px]">
            <div>
              <div className="text-[10px] text-stone-500 uppercase">Annual Revenue</div>
              <div className="font-bold text-white text-xs">
                ${(hoveredAssessment.contract?.annual_contract_value || 0).toLocaleString()} ARR
              </div>
            </div>
            <div>
              <div className="text-[10px] text-stone-500 uppercase">Health Score</div>
              <div className={`font-bold text-xs ${
                (100 - hoveredAssessment.risk_score) >= 70 ? 'text-emerald-400' :
                (100 - hoveredAssessment.risk_score) >= 50 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {Math.max(10, 100 - hoveredAssessment.risk_score)}/100
              </div>
            </div>
          </div>

          {hoveredAssessment.factors && hoveredAssessment.factors.length > 0 && (
            <div className="text-[11px] text-rose-300 bg-rose-950/40 p-2 rounded-lg border border-rose-900/40 font-mono">
              ⚠️ Trigger: {hoveredAssessment.factors[0].name} ({hoveredAssessment.factors[0].points} pts)
            </div>
          )}

          <div className="text-[10px] text-amber-400 font-mono pt-1 flex items-center justify-between">
            <span>Click to select account in scenario lab</span>
            <span>→</span>
          </div>
        </div>
      )}

      {/* Bottom Right: Astrolabe Ring Legend */}
      <div className="absolute bottom-4 right-4 flex items-center gap-3 p-2.5 rounded-2xl bg-[#292524]/90 border border-stone-800 text-[10px] font-mono text-stone-300 backdrop-blur-md shadow-lg pointer-events-none">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
          <span>Safe Orbit (R&gt;18)</span>
        </div>
        <div className="w-px h-3 bg-stone-700" />
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>Watchlist (12-18)</span>
        </div>
        <div className="w-px h-3 bg-stone-700" />
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
          <span>Event Horizon (R&lt;12)</span>
        </div>
      </div>
    </div>
  );
};
