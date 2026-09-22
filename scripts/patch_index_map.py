import json
from pathlib import Path

def generate_patched_html():
    index_path = Path("dashboard/templates/index.html")
    content = index_path.read_text(encoding="utf-8")
    
    paths_data = json.loads(Path("dashboard/static/world_paths.json").read_text(encoding="utf-8"))
    land_d = paths_data["land"]
    
    # 1. Add d3.v7.min.js and topojson.min.js in head if not present
    if "d3.v7.min.js" not in content:
        script_tags = """    <!-- Chart.js for high density telemetry charts -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- D3 & TopoJSON for High-Precision Tactical Geo-Threat Vector Map -->
    <script src="/static/d3.v7.min.js"></script>
    <script src="/static/topojson.min.js"></script>"""
        content = content.replace(
            """    <!-- Chart.js for high density telemetry charts -->\n    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>""",
            script_tags
        )

    # 2. Add styles for high-fidelity map
    map_styles = """        /* High-Definition Tactical World Map Styles */
        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(100%); }
        }
        .animate-scanline {
            animation: scanline 7s linear infinite;
        }
        @keyframes dashAttack {
            to { stroke-dashoffset: -100; }
        }
        .attack-trajectory {
            stroke-dasharray: 6, 4;
            animation: dashAttack 2.5s linear infinite;
        }
        .country-path {
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            cursor: crosshair;
        }
        .country-path:hover {
            filter: brightness(1.7) drop-shadow(0 0 6px rgba(56, 189, 248, 0.6));
            stroke: #38bdf8 !important;
            stroke-width: 1.2px !important;
        }
        .hud-corner {
            stroke: #38bdf8;
            stroke-width: 1.5;
            fill: none;
            opacity: 0.8;
        }
        .graticule-line {
            stroke: #1e293b;
            stroke-width: 0.6;
            stroke-dasharray: 2, 4;
            fill: none;
        }"""
    if "/* High-Definition Tactical World Map Styles */" not in content:
        content = content.replace(
            "    </style>",
            f"{map_styles}\n    </style>"
        )

    # 3. High-definition SVG World Threat Vector Map Replacement
    new_map_html = f'''                        <!-- Left: High-Precision Tactical Interactive Vector Map -->
                        <div class="lg:col-span-2 soc-panel rounded p-3 flex flex-col justify-between bg-slate-950/90 min-h-[460px] relative overflow-hidden border border-slate-800 shadow-2xl">
                            <!-- Top HUD Status & Controls -->
                            <div class="text-[11px] font-mono text-slate-400 flex flex-wrap items-center justify-between gap-2 mb-2 border-b border-slate-800/80 pb-2 z-10">
                                <div class="flex items-center gap-2">
                                    <span class="text-sky-400 font-bold tracking-wider">WORLD THREAT VECTOR MAP</span>
                                    <span class="text-[10px] px-2 py-0.5 rounded bg-sky-950/80 text-sky-300 border border-sky-800/60 font-mono">
                                        WGS84 EQUIRECTANGULAR // 110M FIDELITY
                                    </span>
                                </div>
                                <div class="flex items-center gap-2">
                                    <div class="inline-flex rounded p-0.5 bg-slate-900 border border-slate-800 text-[10px]" id="map-filter-group">
                                        <button onclick="filterMapVectors('all')" class="px-2 py-0.5 rounded bg-sky-600 text-white font-bold" id="btn-filter-all">ALL VECTORS</button>
                                        <button onclick="filterMapVectors('critical')" class="px-2 py-0.5 text-slate-400 hover:text-white" id="btn-filter-critical">CRITICAL ONLY</button>
                                        <button onclick="filterMapVectors('blocked')" class="px-2 py-0.5 text-slate-400 hover:text-white" id="btn-filter-blocked">BLOCKED</button>
                                    </div>
                                    <span class="text-emerald-400 font-bold flex items-center gap-1.5 text-[11px] pl-2 border-l border-slate-800">
                                        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                                        ACTIVE GEO PROBE
                                    </span>
                                </div>
                            </div>

                            <!-- Styled High-Resolution SVG Map Container -->
                            <div class="flex-1 flex items-center justify-center relative my-1 overflow-hidden rounded bg-[#090d16] border border-slate-900" id="world-map-svg-container">
                                <!-- Tactical Scanline Radar Effect -->
                                <div class="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-sky-500/[0.04] to-transparent animate-scanline z-0"></div>

                                <svg id="world-threat-map-svg" viewBox="0 0 1000 500" class="w-full h-full select-none relative z-10">
                                    <defs>
                                        <!-- Glow Filter for Missiles & Nodes -->
                                        <filter id="hud-glow" x="-50%" y="-50%" width="200%" height="200%">
                                            <feGaussianBlur stdDeviation="3" result="blur" />
                                            <feMerge>
                                                <feMergeNode in="blur" />
                                                <feMergeNode in="SourceGraphic" />
                                            </feMerge>
                                        </filter>
                                        <filter id="core-glow" x="-50%" y="-50%" width="200%" height="200%">
                                            <feGaussianBlur stdDeviation="5" result="blur" />
                                            <feMerge>
                                                <feMergeNode in="blur" />
                                                <feMergeNode in="blur" />
                                                <feMergeNode in="SourceGraphic" />
                                            </feMerge>
                                        </filter>
                                        <!-- Linear Gradients for Ballistic Attack Vectors -->
                                        <linearGradient id="grad-ru" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stop-color="#ef4444" stop-opacity="0.9" />
                                            <stop offset="100%" stop-color="#f87171" stop-opacity="0.4" />
                                        </linearGradient>
                                        <linearGradient id="grad-cn" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stop-color="#f97316" stop-opacity="0.9" />
                                            <stop offset="100%" stop-color="#fb923c" stop-opacity="0.4" />
                                        </linearGradient>
                                        <linearGradient id="grad-us" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stop-color="#eab308" stop-opacity="0.9" />
                                            <stop offset="100%" stop-color="#facc15" stop-opacity="0.4" />
                                        </linearGradient>
                                        <linearGradient id="grad-nl" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stop-color="#a855f7" stop-opacity="0.9" />
                                            <stop offset="100%" stop-color="#c084fc" stop-opacity="0.4" />
                                        </linearGradient>
                                        <linearGradient id="grad-ir" x1="0%" y1="0%" x2="100%" y2="100%">
                                            <stop offset="0%" stop-color="#f43f5e" stop-opacity="0.9" />
                                            <stop offset="100%" stop-color="#fb7185" stop-opacity="0.4" />
                                        </linearGradient>
                                    </defs>

                                    <!-- 1. Tactical Military Graticules (Lat/Lon Grid) -->
                                    <g id="map-graticules">
                                        <!-- Latitude Lines -->
                                        <line x1="0" y1="83" x2="1000" y2="83" class="graticule-line" />
                                        <line x1="0" y1="167" x2="1000" y2="167" class="graticule-line" />
                                        <line x1="0" y1="250" x2="1000" y2="250" stroke="#334155" stroke-width="0.8" stroke-dasharray="4,4" /> <!-- Equator -->
                                        <line x1="0" y1="333" x2="1000" y2="333" class="graticule-line" />
                                        <line x1="0" y1="417" x2="1000" y2="417" class="graticule-line" />
                                        <!-- Longitude Lines -->
                                        <line x1="167" y1="0" x2="167" y2="500" class="graticule-line" />
                                        <line x1="333" y1="0" x2="333" y2="500" class="graticule-line" />
                                        <line x1="500" y1="0" x2="500" y2="500" stroke="#334155" stroke-width="0.8" stroke-dasharray="4,4" /> <!-- Prime Meridian -->
                                        <line x1="667" y1="0" x2="667" y2="500" class="graticule-line" />
                                        <line x1="833" y1="0" x2="833" y2="500" class="graticule-line" />
                                    </g>

                                    <!-- 2. High-Precision Real Natural Earth Continents Base Layer -->
                                    <path id="world-land-base" fill="#131c2e" stroke="#253550" stroke-width="0.75" d="{land_d}" />

                                    <!-- 3. Dynamic Interactive Country Geometry Layer -->
                                    <g id="map-countries-layer"></g>

                                    <!-- 4. Ballistic Geodesic Attack Vectors (Threat Trajectories) -->
                                    <g id="map-attack-arcs">
                                        <!-- Arc 1: Russia (Moscow 604, 95) -> Korea Target (853, 146) -->
                                        <path id="traj-ru" d="M 604 95 Q 720 20 853 146" fill="none" stroke="url(#grad-ru)" stroke-width="2" class="attack-trajectory vec-critical" />
                                        <!-- Arc 2: China (Beijing 823, 139) -> Korea Target (853, 146) -->
                                        <path id="traj-cn" d="M 823 139 Q 838 118 853 146" fill="none" stroke="url(#grad-cn)" stroke-width="2" class="attack-trajectory vec-critical" />
                                        <!-- Arc 3: United States (Washington DC 286, 142) -> Korea Target (853, 146) -->
                                        <path id="traj-us" d="M 286 142 Q 570 -20 853 146" fill="none" stroke="url(#grad-us)" stroke-width="1.8" class="attack-trajectory vec-all" />
                                        <!-- Arc 4: Netherlands C2 (Amsterdam 514, 104) -> Korea Target (853, 146) -->
                                        <path id="traj-nl" d="M 514 104 Q 680 15 853 146" fill="none" stroke="url(#grad-nl)" stroke-width="1.8" class="attack-trajectory vec-blocked" />
                                        <!-- Arc 5: Iran (Tehran 643, 151) -> Korea Target (853, 146) -->
                                        <path id="traj-ir" d="M 643 151 Q 750 80 853 146" fill="none" stroke="url(#grad-ir)" stroke-width="1.8" class="attack-trajectory vec-blocked" />

                                        <!-- Continuous Glowing Missile Particles (SVG animateMotion) -->
                                        <circle r="3.5" fill="#ef4444" filter="url(#hud-glow)">
                                            <animateMotion dur="2.4s" repeatCount="indefinite" path="M 604 95 Q 720 20 853 146" />
                                        </circle>
                                        <circle r="3.5" fill="#f97316" filter="url(#hud-glow)">
                                            <animateMotion dur="1.8s" repeatCount="indefinite" path="M 823 139 Q 838 118 853 146" />
                                        </circle>
                                        <circle r="3" fill="#eab308" filter="url(#hud-glow)">
                                            <animateMotion dur="3.6s" repeatCount="indefinite" path="M 286 142 Q 570 -20 853 146" />
                                        </circle>
                                        <circle r="3" fill="#a855f7" filter="url(#hud-glow)">
                                            <animateMotion dur="3.0s" repeatCount="indefinite" path="M 514 104 Q 680 15 853 146" />
                                        </circle>
                                        <circle r="3" fill="#f43f5e" filter="url(#hud-glow)">
                                            <animateMotion dur="2.8s" repeatCount="indefinite" path="M 643 151 Q 750 80 853 146" />
                                        </circle>
                                    </g>

                                    <!-- 5. Threat Origin Ground Nodes -->
                                    <g id="map-threat-nodes">
                                        <!-- Russia (Moscow: 604, 95) -->
                                        <g class="cursor-pointer" onclick="focusCountryThreat('Russia')">
                                            <circle cx="604" cy="95" r="8" fill="#ef4444" opacity="0.25" class="animate-ping" />
                                            <circle cx="604" cy="95" r="5" fill="#ef4444" stroke="#7f1d1d" stroke-width="1.5" filter="url(#hud-glow)" />
                                            <text x="595" y="86" fill="#fca5a5" font-size="9" font-family="JetBrains Mono" font-weight="bold">RU [28]</text>
                                        </g>
                                        <!-- China (Beijing: 823, 139) -->
                                        <g class="cursor-pointer" onclick="focusCountryThreat('China')">
                                            <circle cx="823" cy="139" r="8" fill="#f97316" opacity="0.25" class="animate-ping" />
                                            <circle cx="823" cy="139" r="5" fill="#f97316" stroke="#9a3412" stroke-width="1.5" filter="url(#hud-glow)" />
                                            <text x="815" y="130" fill="#fdba74" font-size="9" font-family="JetBrains Mono" font-weight="bold">CN [19]</text>
                                        </g>
                                        <!-- USA (Washington DC: 286, 142) -->
                                        <g class="cursor-pointer" onclick="focusCountryThreat('United States')">
                                            <circle cx="286" cy="142" r="7" fill="#eab308" opacity="0.2" class="animate-ping" />
                                            <circle cx="286" cy="142" r="4.5" fill="#eab308" stroke="#854d0e" stroke-width="1.5" />
                                            <text x="276" y="133" fill="#fde047" font-size="9" font-family="JetBrains Mono" font-weight="bold">US [12]</text>
                                        </g>
                                        <!-- Netherlands (Europe C2: 514, 104) -->
                                        <g class="cursor-pointer" onclick="focusCountryThreat('Netherlands')">
                                            <circle cx="514" cy="104" r="7" fill="#a855f7" opacity="0.2" class="animate-ping" />
                                            <circle cx="514" cy="104" r="4.5" fill="#a855f7" stroke="#581c87" stroke-width="1.5" />
                                            <text x="505" y="96" fill="#d8b4fe" font-size="9" font-family="JetBrains Mono" font-weight="bold">NL [8]</text>
                                        </g>
                                        <!-- Iran (Tehran: 643, 151) -->
                                        <g class="cursor-pointer" onclick="focusCountryThreat('Iran')">
                                            <circle cx="643" cy="151" r="7" fill="#f43f5e" opacity="0.2" class="animate-ping" />
                                            <circle cx="643" cy="151" r="4.5" fill="#f43f5e" stroke="#881337" stroke-width="1.5" />
                                            <text x="635" y="143" fill="#fda4af" font-size="9" font-family="JetBrains Mono" font-weight="bold">IR [5]</text>
                                        </g>
                                    </g>

                                    <!-- 6. Target Center Defense Node (Seoul, South Korea: 853, 146) -->
                                    <g id="map-target-node">
                                        <!-- Outer Rotating Reticle -->
                                        <circle cx="853" cy="146" r="16" fill="none" stroke="#38bdf8" stroke-width="1.2" stroke-dasharray="3,3" opacity="0.8" />
                                        <circle cx="853" cy="146" r="24" fill="none" stroke="#0284c7" stroke-width="0.8" opacity="0.4" class="animate-ping" />
                                        <!-- Crosshairs -->
                                        <line x1="833" y1="146" x2="845" y2="146" stroke="#38bdf8" stroke-width="1.5" />
                                        <line x1="861" y1="146" x2="873" y2="146" stroke="#38bdf8" stroke-width="1.5" />
                                        <line x1="853" y1="126" x2="853" y2="138" stroke="#38bdf8" stroke-width="1.5" />
                                        <line x1="853" y1="154" x2="853" y2="166" stroke="#38bdf8" stroke-width="1.5" />
                                        <!-- Center Core -->
                                        <circle cx="853" cy="146" r="5" fill="#38bdf8" stroke="#0369a1" stroke-width="2" filter="url(#core-glow)" />
                                    </g>

                                    <!-- 7. Tactical Corner HUD Brackets -->
                                    <path d="M 15 35 L 15 15 L 35 15" class="hud-corner" />
                                    <path d="M 985 35 L 985 15 L 965 15" class="hud-corner" />
                                    <path d="M 15 465 L 15 485 L 35 485" class="hud-corner" />
                                    <path d="M 985 465 L 985 485 L 965 485" class="hud-corner" />
                                </svg>

                                <!-- Interactive Floating Map Tooltip -->
                                <div id="map-tooltip" class="hidden absolute z-30 pointer-events-none bg-slate-900/95 border border-sky-500/60 rounded px-2.5 py-1.5 shadow-2xl text-[11px] font-mono text-slate-200"></div>

                                <!-- Target Center Info Badge (Preserved & Enhanced) -->
                                <div class="absolute bottom-2 left-2 text-[10px] font-mono text-slate-300 bg-slate-900/95 px-2.5 py-1 rounded border border-slate-700/80 shadow-lg flex items-center gap-2">
                                    <span class="w-2 h-2 rounded-full bg-sky-400 animate-pulse"></span>
                                    <span>Target Center: <b class="text-sky-400">10.77.30.20 (Zone-Victim)</b></span>
                                    <span class="text-slate-500">|</span>
                                    <span class="text-emerald-400">IDS Protection Active</span>
                                </div>

                                <!-- Threat Legend Badge -->
                                <div class="absolute bottom-2 right-2 text-[10px] font-mono text-slate-400 bg-slate-900/95 px-2.5 py-1 rounded border border-slate-800 shadow-lg hidden md:flex items-center gap-3">
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-red-500"></span> RU (92.8% Drop)</span>
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-orange-500"></span> CN (88.5% Drop)</span>
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-amber-500"></span> US (85.7% Drop)</span>
                                    <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full bg-sky-400"></span> Target (KR)</span>
                                </div>
                            </div>
                        </div>'''

    # Target chunk to replace
    start_tag = "<!-- Left: High-Precision Tactical Interactive Vector Map -->"
    if start_tag not in content:
        start_tag = "<!-- Left: SVG Interactive Vector Map representation -->"
    end_tag = "<!-- Right: Country Threat Statistics Table -->"
    
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    if start_idx == -1 or end_idx == -1:
        print("Could not find start/end tags for map replacement")
        return False
        
    content = content[:start_idx] + new_map_html + "\n\n                        " + content[end_idx:]

    # 4. Add JavaScript for interactive map logic
    js_map_code = """
        // -------------------------------------------------------------
        // High-Precision World Threat Map Interactive Engine
        // -------------------------------------------------------------
        let worldPathsCache = null;
        let countryThreatMap = {
            'Russia': { attacks: 28, blocked: 26, rate: '92.8%', sev: 'CRITICAL', color: '#450a0a', stroke: '#dc2626', flag: '🇷🇺' },
            'China': { attacks: 19, blocked: 17, rate: '88.5%', sev: 'CRITICAL', color: '#431407', stroke: '#ea580c', flag: '🇨🇳' },
            'United States of America': { attacks: 12, blocked: 10, rate: '85.7%', sev: 'HIGH', color: '#451a03', stroke: '#d97706', flag: '🇺🇸' },
            'United States': { attacks: 12, blocked: 10, rate: '85.7%', sev: 'HIGH', color: '#451a03', stroke: '#d97706', flag: '🇺🇸' },
            'Netherlands': { attacks: 8, blocked: 8, rate: '100.0%', sev: 'HIGH', color: '#2e1065', stroke: '#9333ea', flag: '🇳🇱' },
            'Iran': { attacks: 5, blocked: 4, rate: '80.0%', sev: 'MEDIUM', color: '#3b0764', stroke: '#a855f7', flag: '🇮🇷' },
            'North Korea': { attacks: 6, blocked: 6, rate: '100.0%', sev: 'CRITICAL', color: '#4c0519', stroke: '#e11d48', flag: '🇰🇵' },
            'South Korea': { attacks: 0, blocked: 0, rate: 'PROTECTED', sev: 'TARGET', color: '#0369a1', stroke: '#38bdf8', flag: '🇰🇷' }
        };

        async function initWorldThreatMap() {
            try {
                if (!worldPathsCache) {
                    const res = await fetch('/static/world_paths.json');
                    if (res.ok) {
                        worldPathsCache = await res.json();
                    }
                }
                if (!worldPathsCache || !worldPathsCache.countries) return;

                const layer = document.getElementById('map-countries-layer');
                if (!layer) return;
                layer.innerHTML = '';

                worldPathsCache.countries.forEach(c => {
                    const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    pathEl.setAttribute('d', c.d);
                    pathEl.setAttribute('class', 'country-path');
                    pathEl.setAttribute('data-id', c.id);
                    pathEl.setAttribute('data-name', c.name);

                    // Threat coloration
                    const threat = countryThreatMap[c.name];
                    if (threat) {
                        pathEl.setAttribute('fill', threat.color);
                        pathEl.setAttribute('stroke', threat.stroke);
                        pathEl.setAttribute('stroke-width', c.name === 'South Korea' ? '1.8' : '0.9');
                    } else {
                        pathEl.setAttribute('fill', '#131c2e');
                        pathEl.setAttribute('stroke', '#22324a');
                        pathEl.setAttribute('stroke-width', '0.5');
                    }

                    // Hover tooltip events
                    pathEl.addEventListener('mouseenter', (e) => showMapCountryTooltip(e, c.name, threat));
                    pathEl.addEventListener('mousemove', (e) => updateMapTooltipPosition(e));
                    pathEl.addEventListener('mouseleave', hideMapCountryTooltip);

                    layer.appendChild(pathEl);
                });
            } catch (err) {
                console.warn('World map country layer initialization fallback:', err);
            }
        }

        function showMapCountryTooltip(event, countryName, threat) {
            const tooltip = document.getElementById('map-tooltip');
            if (!tooltip) return;
            const info = threat || { attacks: 0, blocked: 0, rate: '0.0%', sev: 'NORMAL', flag: '🌐' };
            tooltip.innerHTML = `
                <div class="flex items-center gap-1.5 font-bold text-white border-b border-slate-700/80 pb-1 mb-1">
                    <span>${info.flag}</span>
                    <span>${countryName}</span>
                    <span class="text-[9px] px-1.5 py-0.2 rounded ${info.sev === 'CRITICAL' ? 'bg-red-950 text-red-300' : (info.sev === 'HIGH' ? 'bg-orange-950 text-orange-300' : 'bg-slate-800 text-slate-300')} ml-auto">${info.sev}</span>
                </div>
                <div class="space-y-0.5 text-slate-300 text-[10px]">
                    <div>탐지 공격: <b class="text-sky-400">${info.attacks}건</b></div>
                    <div>방화벽 차단: <b class="text-purple-400">${info.blocked}건</b> (${info.rate})</div>
                    <div>대상 자산: <span class="text-emerald-400">10.77.30.20 (Zone-Victim)</span></div>
                </div>
            `;
            tooltip.classList.remove('hidden');
            updateMapTooltipPosition(event);
        }

        function updateMapTooltipPosition(event) {
            const tooltip = document.getElementById('map-tooltip');
            const container = document.getElementById('world-map-svg-container');
            if (!tooltip || !container) return;
            const rect = container.getBoundingClientRect();
            let x = event.clientX - rect.left + 15;
            let y = event.clientY - rect.top + 15;
            if (x + 180 > rect.width) x = event.clientX - rect.left - 190;
            if (y + 90 > rect.height) y = event.clientY - rect.top - 95;
            tooltip.style.left = `${Math.max(5, x)}px`;
            tooltip.style.top = `${Math.max(5, y)}px`;
        }

        function hideMapCountryTooltip() {
            const tooltip = document.getElementById('map-tooltip');
            if (tooltip) tooltip.classList.add('hidden');
        }

        function focusCountryThreat(countryName) {
            showToast(`국가 관제 포커스: ${countryName}`, 'sky');
            const rows = document.querySelectorAll('#geo-threats-tbody tr');
            rows.forEach(r => {
                if (r.textContent.includes(countryName)) {
                    r.classList.add('bg-sky-950/60');
                    setTimeout(() => r.classList.remove('bg-sky-950/60'), 2500);
                }
            });
        }

        function filterMapVectors(mode) {
            const buttons = ['all', 'critical', 'blocked'];
            buttons.forEach(b => {
                const btn = document.getElementById(`btn-filter-${b}`);
                if (btn) {
                    if (b === mode) {
                        btn.className = 'px-2 py-0.5 rounded bg-sky-600 text-white font-bold';
                    } else {
                        btn.className = 'px-2 py-0.5 text-slate-400 hover:text-white';
                    }
                }
            });

            const trajectories = document.querySelectorAll('.attack-trajectory');
            trajectories.forEach(t => {
                if (mode === 'all') {
                    t.style.display = 'block';
                } else if (mode === 'critical') {
                    t.style.display = t.classList.contains('vec-critical') ? 'block' : 'none';
                } else if (mode === 'blocked') {
                    t.style.display = t.classList.contains('vec-blocked') ? 'block' : 'none';
                }
            });
            showToast(`공격 벡터 필터 적용: ${mode.toUpperCase()}`, 'sky');
        }
    """

    if "function initWorldThreatMap()" not in content:
        content = content.replace(
            "async function fetchGeoThreats() {",
            f"{js_map_code}\n\n        async function fetchGeoThreats() {{"
        )

    # Call initWorldThreatMap in DOMContentLoaded
    if "initWorldThreatMap();" not in content:
        content = content.replace(
            "switchView('dashboard', 'overview');",
            "switchView('dashboard', 'overview');\n            initWorldThreatMap();"
        )

    index_path.write_text(content, encoding="utf-8")
    print(f"Successfully patched {index_path} with high-fidelity World Threat Vector Map!")
    return True

if __name__ == "__main__":
    generate_patched_html()
