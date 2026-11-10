"""교회 동산 테마 (배너 SVG)."""

CHURCH_BANNER = """
<svg viewBox="0 0 1200 300" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice"
     style="width:100%;height:240px;display:block;border-radius:22px;">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFD9A8"/>
      <stop offset="0.55" stop-color="#FFEBCB"/>
      <stop offset="1" stop-color="#FFF6E4"/>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#FFF4C2"/>
      <stop offset="0.6" stop-color="#FFD27A" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#FFB45C" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="hillBack" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B9D58C"/><stop offset="1" stop-color="#9CC173"/>
    </linearGradient>
    <linearGradient id="hillFront" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#9BC46A"/><stop offset="1" stop-color="#7BAA4E"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#FFE7A0" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#FFE7A0" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="300" fill="url(#sky)"/>
  <circle cx="930" cy="95" r="90" fill="url(#sun)"/>
  <circle cx="930" cy="95" r="34" fill="#FFF1B8"/>

  <!-- 구름 -->
  <g fill="#FFFFFF" opacity="0.85">
    <ellipse cx="190" cy="70" rx="55" ry="16"/><ellipse cx="225" cy="60" rx="35" ry="16"/>
    <ellipse cx="640" cy="50" rx="45" ry="12"/><ellipse cx="670" cy="43" rx="28" ry="12"/>
  </g>

  <!-- 새 -->
  <g fill="none" stroke="#8A6B4E" stroke-width="2" stroke-linecap="round">
    <path d="M760 105 q7 -7 14 0 q7 -7 14 0"/>
    <path d="M795 88 q5 -5 10 0 q5 -5 10 0"/>
  </g>

  <!-- 뒷 동산 -->
  <path d="M0 230 C 200 170, 380 190, 560 215 S 950 160, 1200 205 L1200 300 L0 300 Z" fill="url(#hillBack)"/>
  <!-- 앞 동산 (교회가 있는 언덕) -->
  <path d="M0 270 C 180 250, 330 175, 520 160 C 700 150, 820 230, 1200 255 L1200 300 L0 300 Z" fill="url(#hillFront)"/>

  <!-- 오솔길 -->
  <path d="M470 300 C 490 260, 520 220, 530 196 L548 196 C 548 225, 545 262, 560 300 Z" fill="#E8CFA0" opacity="0.9"/>

  <!-- 교회 -->
  <circle cx="540" cy="120" r="85" fill="url(#glow)"/>
  <g transform="translate(490,60)">
    <!-- 첨탑 -->
    <rect x="38" y="40" width="24" height="60" fill="#FFFDF7" stroke="#C9B79C" stroke-width="1.5"/>
    <polygon points="34,42 50,10 66,42" fill="#B5563C"/>
    <rect x="48.5" y="-14" width="3" height="26" fill="#8A5A3B"/>
    <rect x="41" y="-6" width="18" height="3" fill="#8A5A3B"/>
    <circle cx="50" cy="60" r="6" fill="#F2C46B" stroke="#C9B79C"/>
    <!-- 본당 -->
    <polygon points="0,92 50,62 100,92" fill="#C2603F"/>
    <rect x="6" y="90" width="88" height="48" fill="#FFFDF7" stroke="#C9B79C" stroke-width="1.5"/>
    <path d="M42 138 V116 a8 8 0 0 1 16 0 V138 Z" fill="#9C6B45"/>
    <path d="M16 112 a6 6 0 0 1 12 0 V124 H16 Z" fill="#F7CF7A"/>
    <path d="M72 112 a6 6 0 0 1 12 0 V124 H72 Z" fill="#F7CF7A"/>
  </g>

  <!-- 나무 -->
  <g>
    <rect x="378" y="190" width="6" height="18" fill="#8A6B4E"/><circle cx="381" cy="182" r="16" fill="#6E9E45"/>
    <rect x="660" y="182" width="6" height="18" fill="#8A6B4E"/><circle cx="663" cy="172" r="19" fill="#6A9A42"/>
    <rect x="695" y="194" width="5" height="14" fill="#8A6B4E"/><circle cx="697" cy="187" r="12" fill="#7FAE52"/>
  </g>

  <!-- 꽃 -->
  <g>
    <circle cx="300" cy="258" r="3.5" fill="#FFFFFF"/><circle cx="320" cy="250" r="3.5" fill="#F7B8C4"/>
    <circle cx="760" cy="262" r="3.5" fill="#FFE07A"/><circle cx="790" cy="270" r="3.5" fill="#FFFFFF"/>
    <circle cx="850" cy="268" r="3.5" fill="#F7B8C4"/><circle cx="240" cy="272" r="3.5" fill="#FFE07A"/>
  </g>
</svg>
"""
