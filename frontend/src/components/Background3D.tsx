import { useEffect, useRef } from 'react'
import * as THREE from 'three'

const NODE_COUNT = 180
const CONNECTION_DIST = 3.5
const SPEED = 0.00035

export default function Background3D() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current!
    const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(window.innerWidth, window.innerHeight)

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 100)
    camera.position.z = 12

    // ── Nodes ──────────────────────────────────────────────────────────────
    const nodeGeom = new THREE.SphereGeometry(0.04, 8, 8)
    const nodeMat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, transparent: true, opacity: 0.7 })

    const positions: THREE.Vector3[] = []
    const velocities: THREE.Vector3[] = []
    const meshes: THREE.Mesh[] = []

    for (let i = 0; i < NODE_COUNT; i++) {
      const pos = new THREE.Vector3(
        (Math.random() - 0.5) * 20,
        (Math.random() - 0.5) * 12,
        (Math.random() - 0.5) * 8
      )
      const vel = new THREE.Vector3(
        (Math.random() - 0.5) * 0.008,
        (Math.random() - 0.5) * 0.008,
        (Math.random() - 0.5) * 0.004
      )
      positions.push(pos)
      velocities.push(vel)

      const m = new THREE.Mesh(nodeGeom, nodeMat.clone())
      m.position.copy(pos)
      scene.add(m)
      meshes.push(m)
    }

    // ── Lines (connections) ────────────────────────────────────────────────
    const lineGroup = new THREE.Group()
    scene.add(lineGroup)

    function rebuildLines() {
      while (lineGroup.children.length) lineGroup.remove(lineGroup.children[0])
      for (let i = 0; i < NODE_COUNT; i++) {
        for (let j = i + 1; j < NODE_COUNT; j++) {
          const dist = positions[i].distanceTo(positions[j])
          if (dist < CONNECTION_DIST) {
            const opacity = (1 - dist / CONNECTION_DIST) * 0.25
            const geom = new THREE.BufferGeometry().setFromPoints([positions[i], positions[j]])
            const mat = new THREE.LineBasicMaterial({
              color: i % 3 === 0 ? 0xff1a1a : 0x00d4ff,
              transparent: true,
              opacity,
            })
            lineGroup.add(new THREE.Line(geom, mat))
          }
        }
      }
    }

    // ── Ambient particles ─────────────────────────────────────────────────
    const partGeom = new THREE.BufferGeometry()
    const partPositions = new Float32Array(600 * 3)
    for (let i = 0; i < 600 * 3; i++) partPositions[i] = (Math.random() - 0.5) * 30
    partGeom.setAttribute('position', new THREE.BufferAttribute(partPositions, 3))
    const partMat = new THREE.PointsMaterial({ color: 0xff1a1a, size: 0.03, transparent: true, opacity: 0.25 })
    scene.add(new THREE.Points(partGeom, partMat))

    let frameCount = 0
    let raf: number
    const REBUILD_INTERVAL = 12

    const animate = () => {
      raf = requestAnimationFrame(animate)
      frameCount++

      // Update positions
      for (let i = 0; i < NODE_COUNT; i++) {
        positions[i].add(velocities[i])
        meshes[i].position.copy(positions[i])

        // Bounce off boundaries
        if (Math.abs(positions[i].x) > 10) velocities[i].x *= -1
        if (Math.abs(positions[i].y) > 6)  velocities[i].y *= -1
        if (Math.abs(positions[i].z) > 4)  velocities[i].z *= -1
      }

      // Rebuild connections every N frames for performance
      if (frameCount % REBUILD_INTERVAL === 0) rebuildLines()

      // Slow camera drift
      camera.position.x = Math.sin(Date.now() * SPEED) * 1.5
      camera.position.y = Math.cos(Date.now() * SPEED * 0.7) * 0.8
      camera.lookAt(scene.position)

      renderer.render(scene, camera)
    }

    rebuildLines()
    animate()

    const handleResize = () => {
      renderer.setSize(window.innerWidth, window.innerHeight)
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
    }
    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', handleResize)
      renderer.dispose()
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{ background: 'radial-gradient(ellipse at 50% 50%, #0a0a20 0%, #050510 70%)' }}
    />
  )
}
