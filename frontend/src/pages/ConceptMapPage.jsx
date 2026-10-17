import React, { useState, useEffect, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  MarkerType,
  ReactFlowProvider,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useNavigate } from 'react-router-dom';
import { masteryService } from '../services/learningService';
import ConceptNode from '../components/ConceptNode';
import ConceptDetailModal from '../components/ConceptDetailModal';
import {
  Sparkles,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Search,
  Layers,
  BookOpen,
} from 'lucide-react';

const nodeTypes = {
  conceptNode: ConceptNode,
};

function ConceptGraphCanvas({
  rawNodes,
  rawEdges,
  courses,
  onNodeClick,
  loading,
  onRefresh,
}) {
  const { zoomIn, zoomOut, fitView, setCenter } = useReactFlow();
  const [selectedCourse, setSelectedCourse] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter nodes according to selected course and search query
  const filteredNodes = useMemo(() => {
    let result = rawNodes;
    if (selectedCourse !== 'ALL') {
      result = result.filter(
        (n) =>
          n.data?.course_title === selectedCourse ||
          String(n.data?.course_id) === String(selectedCourse)
      );
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.map((n) => {
        const matches = n.data?.name?.toLowerCase().includes(q) ||
          n.data?.module_title?.toLowerCase().includes(q);
        return {
          ...n,
          style: {
            opacity: matches ? 1 : 0.25,
            transition: 'opacity 0.2s ease',
          },
        };
      });
    } else {
      result = result.map((n) => ({
        ...n,
        style: { opacity: 1, transition: 'opacity 0.2s ease' },
      }));
    }
    return result;
  }, [rawNodes, selectedCourse, searchQuery]);

  // Keep only edges that connect visible nodes
  const filteredEdges = useMemo(() => {
    const visibleIds = new Set(filteredNodes.map((n) => n.id));
    return rawEdges.filter(
      (e) => visibleIds.has(e.source) && visibleIds.has(e.target)
    );
  }, [rawEdges, filteredNodes]);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    setNodes(filteredNodes);
    setEdges(filteredEdges);
  }, [filteredNodes, filteredEdges, setNodes, setEdges]);

  // Auto-fit view when course filter changes
  useEffect(() => {
    if (!loading && nodes.length > 0) {
      const timer = setTimeout(() => {
        fitView({ padding: 0.25, duration: 600 });
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [selectedCourse, loading, fitView]);

  // Focus single search result if exact/unique match
  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      const match = rawNodes.find((n) =>
        n.data?.name?.toLowerCase().includes(searchQuery.toLowerCase().trim())
      );
      if (match) {
        setCenter(match.position.x + 69, match.position.y + 69, {
          zoom: 1.3,
          duration: 600,
        });
      }
    }
  };

  const miniMapNodeColor = (node) => {
    const status = node.data?.status;
    if (status === 'STRONG') return '#10b981';
    if (status === 'DEVELOPING') return '#3b82f6';
    if (status === 'WEAK') return '#f59e0b';
    return '#94a3b8';
  };

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: '#f8fafc',
        borderRadius: '16px',
        border: '1px solid #e2e8f0',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Top Controls Overlay Ribbon */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          right: '12px',
          zIndex: 10,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '10px',
          pointerEvents: 'none',
        }}
      >
        {/* Course Filter Tabs (Interactive) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)',
            padding: '6px',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
            border: '1px solid #e2e8f0',
            pointerEvents: 'auto',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '0 8px',
              color: '#64748b',
              fontSize: '11px',
              fontWeight: 700,
              textTransform: 'uppercase',
            }}
          >
            <BookOpen size={14} /> Curriculum:
          </div>

          <button
            type="button"
            onClick={() => setSelectedCourse('ALL')}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: 'none',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              backgroundColor: selectedCourse === 'ALL' ? '#4f46e5' : 'transparent',
              color: selectedCourse === 'ALL' ? '#ffffff' : '#475569',
              transition: 'all 0.15s ease',
            }}
          >
            All Concepts ({rawNodes.length})
          </button>

          {courses.map((c) => {
            const count = rawNodes.filter(
              (n) =>
                n.data?.course_title === c.title ||
                String(n.data?.course_id) === String(c.id)
            ).length;
            const isSelected = selectedCourse === c.title || selectedCourse === String(c.id);

            return (
              <button
                key={c.id}
                type="button"
                onClick={() => setSelectedCourse(c.title)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '8px',
                  border: 'none',
                  fontSize: '12px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  backgroundColor: isSelected ? '#4f46e5' : 'transparent',
                  color: isSelected ? '#ffffff' : '#475569',
                  transition: 'all 0.15s ease',
                }}
              >
                {c.title} ({count})
              </button>
            );
          })}
        </div>

        {/* Search & Zoom Actions Toolbar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(8px)',
            padding: '6px 10px',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(15, 23, 42, 0.08)',
            border: '1px solid #e2e8f0',
            pointerEvents: 'auto',
          }}
        >
          {/* Quick Search */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: '#f1f5f9',
              padding: '4px 10px',
              borderRadius: '8px',
            }}
          >
            <Search size={14} color="#64748b" />
            <input
              type="text"
              placeholder="Find concept... (Press Enter)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              style={{
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: '12px',
                color: '#0f172a',
                width: '140px',
              }}
            />
          </div>

          <div style={{ width: '1px', height: '20px', backgroundColor: '#e2e8f0' }} />

          {/* Explicit Zoom Controls */}
          <button
            type="button"
            title="Zoom In"
            onClick={() => zoomIn({ duration: 300 })}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              backgroundColor: '#ffffff',
              color: '#334155',
              cursor: 'pointer',
              transition: 'background-color 0.15s',
            }}
          >
            <ZoomIn size={16} />
          </button>

          <button
            type="button"
            title="Zoom Out"
            onClick={() => zoomOut({ duration: 300 })}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              backgroundColor: '#ffffff',
              color: '#334155',
              cursor: 'pointer',
              transition: 'background-color 0.15s',
            }}
          >
            <ZoomOut size={16} />
          </button>

          <button
            type="button"
            title="Fit View & Center"
            onClick={() => fitView({ padding: 0.25, duration: 500 })}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '6px 10px',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              backgroundColor: '#ffffff',
              color: '#334155',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'background-color 0.15s',
            }}
          >
            <Maximize2 size={14} /> Fit All
          </button>
        </div>
      </div>

      {/* Canvas View */}
      {loading ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            gap: '12px',
            color: '#64748b',
            fontSize: '14px',
          }}
        >
          <RefreshCw size={24} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
          Constructing concept mastery graph...
        </div>
      ) : (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.25 }}
          minZoom={0.2}
          maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#cbd5e1" gap={24} size={1.2} />
          <Controls showInteractive={false} position="bottom-left" />
          <MiniMap
            nodeColor={miniMapNodeColor}
            nodeStrokeWidth={2}
            nodeBorderRadius={4}
            maskColor="rgba(241, 245, 249, 0.75)"
            style={{
              height: 110,
              width: 150,
              borderRadius: '12px',
              overflow: 'hidden',
              boxShadow: '0 4px 12px rgba(15, 23, 42, 0.1)',
              border: '1px solid #e2e8f0',
            }}
            position="bottom-right"
          />
        </ReactFlow>
      )}
    </div>
  );
}

export default function ConceptMapPage() {
  const navigate = useNavigate();
  const [rawNodes, setRawNodes] = useState([]);
  const [rawEdges, setRawEdges] = useState([]);
  const [courses, setCourses] = useState([]);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = await masteryService.getConceptGraph();
      // Configure edges with smoothstep routing and directional arrows
      const styledEdges = (data.edges || []).map((e) => ({
        ...e,
        type: 'smoothstep',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 16,
          height: 16,
          color: '#6366f1',
        },
        style: {
          stroke: '#6366f1',
          strokeWidth: 2,
        },
      }));
      setRawNodes(data.nodes || []);
      setRawEdges(styledEdges);
      setCourses(data.courses || []);
    } catch (err) {
      console.error('Failed to load concept graph:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  const onNodeClick = async (event, node) => {
    try {
      const detail = await masteryService.getConceptDetail(node.data.id);
      setSelectedConcept(detail);
    } catch (err) {
      console.error('Failed to load concept detail:', err);
    }
  };

  const handleStartPractice = (conceptId) => {
    navigate('/student/learning', { state: { conceptId } });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)', gap: '12px' }}>
      {/* Top Header Card */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#ffffff',
          padding: '14px 20px',
          borderRadius: '12px',
          border: '1px solid #e5e7eb',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#111827', margin: 0 }}>
              Knowledge Tracing & Prerequisite Graph
            </h2>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: '#e0e7ff',
                color: '#4338ca',
                padding: '2px 8px',
                borderRadius: '12px',
              }}
            >
              Directed Acyclic Graph (DAG)
            </span>
          </div>
          <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
            Interactive 2D concept map. Click any square node to inspect mastery, prerequisites, and launch adaptive practice.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {/* Status Legend */}
          <div style={{ display: 'flex', gap: '14px', fontSize: '12px', color: '#4b5563' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '3px', backgroundColor: '#10b981' }} />
              Mastered (≥80%)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '3px', backgroundColor: '#3b82f6' }} />
              Learning (50-79%)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '3px', backgroundColor: '#f59e0b' }} />
              Review (&lt;50%)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '10px', height: '10px', borderRadius: '3px', backgroundColor: '#94a3b8' }} />
              Locked
            </div>
          </div>

          <button
            onClick={loadGraph}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              backgroundColor: '#f8fafc',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 700,
              color: '#334155',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {/* Main Flow Canvas with ReactFlowProvider for Zoom and Pan controls */}
      <ReactFlowProvider>
        <ConceptGraphCanvas
          rawNodes={rawNodes}
          rawEdges={rawEdges}
          courses={courses}
          onNodeClick={onNodeClick}
          loading={loading}
          onRefresh={loadGraph}
        />
      </ReactFlowProvider>

      {/* Slide-out Concept Drawer */}
      <ConceptDetailModal
        concept={selectedConcept}
        onClose={() => setSelectedConcept(null)}
        onStartPractice={handleStartPractice}
      />
    </div>
  );
}
