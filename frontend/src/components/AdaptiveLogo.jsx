import React from 'react';

/**
 * Realistic modern emblem for AdaptIQ:
 * High-tech rounded squircle with gradient depth, tactile bevel highlights,
 * and an adaptive intelligence chevron synapse forming the iconic "A" mark.
 */
export default function AdaptiveLogo({ size = 36, light = false }) {
  const id = React.useId().replace(/:/g, '');

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{
        filter: light
          ? 'drop-shadow(0 4px 14px rgba(99, 102, 241, 0.4))'
          : 'drop-shadow(0 2px 8px rgba(79, 70, 229, 0.25))',
        flexShrink: 0,
        display: 'inline-block',
        verticalAlign: 'middle'
      }}
    >
      <defs>
        {/* Background container gradient */}
        <linearGradient id={`bgGrad_${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#4338ca" />
          <stop offset="50%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>

        {/* Luminous intelligence node gradient */}
        <linearGradient id={`glowGrad_${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="60%" stopColor="#818cf8" />
          <stop offset="100%" stopColor="#c084fc" />
        </linearGradient>

        {/* Gloss highlight gradient */}
        <linearGradient id={`glossGrad_${id}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>

        {/* Surface light & depth */}
        <radialGradient id={`coreLight_${id}`} cx="50%" cy="25%" r="75%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#000000" stopOpacity="0.28" />
        </radialGradient>
      </defs>

      {/* Rounded Squircle Container Base */}
      <rect
        x="2"
        y="2"
        width="44"
        height="44"
        rx="12"
        fill={`url(#bgGrad_${id})`}
      />

      {/* Surface Depth Lighting */}
      <rect
        x="2"
        y="2"
        width="44"
        height="44"
        rx="12"
        fill={`url(#coreLight_${id})`}
      />

      {/* Top Gloss Edge Highlight */}
      <path
        d="M3 14C3 8 8 3 14 3H34C40 3 45 8 45 14V17C35 15 20 18 3 24V14Z"
        fill={`url(#glossGrad_${id})`}
      />

      {/* Subtle Outer Rim */}
      <rect
        x="2.5"
        y="2.5"
        width="43"
        height="43"
        rx="11.5"
        stroke="#ffffff"
        strokeOpacity="0.25"
        strokeWidth="1"
      />

      {/* Stylized Adaptive Learning Chevron - Left Ascent */}
      <path
        d="M13 34 L24 12 L29.5 21.5 L22.5 21.5 L17.5 30.5 L24 30.5 L26 34 L13 34 Z"
        fill="#ffffff"
        fillOpacity="0.95"
      />

      {/* Stylized Adaptive Learning Chevron - Right Loop */}
      <path
        d="M24 12 L35 34 L28 34 L25.5 29.5 L30 20.5 L24 12 Z"
        fill={`url(#glowGrad_${id})`}
      />

      {/* Glowing Intelligent Core Synapse */}
      <circle cx="24" cy="21.5" r="3.2" fill="#38bdf8" />
      <circle cx="24" cy="21.5" r="1.4" fill="#ffffff" />
    </svg>
  );
}
