// SUPERR SELECTOR — IPL 2027 AUCTION STRATEGY ANALYTICS
// Unified Dashboard Controller, Column Sorting, Player Dossier & Charts

(function () {
  const data = window.INITIAL_DATA || {
    batters: [],
    bowlers: [],
    overall: [],
    allrounders: [],
    allPlayers: [],
    dataQuality: {}
  };

  const modalBackdrop = document.getElementById('playerModal');
  const modalClose = document.getElementById('modalClose');

  let battingChart = null;
  let bowlingChart = null;

  const sortState = {
    batters: { key: 'rank', asc: true },
    bowlers: { key: 'rank', asc: true },
    overall: { key: 'rank', asc: true }
  };

  const KATEX_DELIMITERS = [
    { left: '$$', right: '$$', display: true },
    { left: '$', right: '$', display: false }
  ];

  function renderMath(el) {
    if (window.renderMathInElement && el) {
      window.renderMathInElement(el, { delimiters: KATEX_DELIMITERS });
    }
  }

  function applyModeVisibility() {
    const privateContent = document.getElementById('privateWorkspaceContent');
    const dqSection = document.getElementById('section-data-quality');
    const headerPills = document.getElementById('privateHeaderPills');
    const dlBox = document.getElementById('privateDownloads');
    const jumpBar = document.getElementById('privateJumpBar');
    const modeBadge = document.getElementById('appModeBadge');
    const errBanner = document.getElementById('localErrorBanner');

    if (data.error) {
      if (modeBadge) modeBadge.style.display = 'none';
      if (errBanner) {
        errBanner.style.display = 'block';
        errBanner.innerHTML = `<strong>OFFICIAL COMPETITION DATA ERROR:</strong> ${data.error}`;
      }
      if (privateContent) privateContent.style.display = 'none';
      if (dqSection) dqSection.style.display = 'none';
      if (headerPills) headerPills.style.display = 'none';
      if (dlBox) dlBox.style.display = 'none';
      if (jumpBar) jumpBar.style.display = 'none';
      return false;
    }

    if (errBanner) errBanner.style.display = 'none';
    if (privateContent) privateContent.style.display = 'block';
    if (dqSection) dqSection.style.display = 'block';
    if (headerPills) headerPills.style.display = 'flex';
    if (jumpBar) jumpBar.style.display = 'flex';

    if (data.reportsDownloadEnabled === false) {
      if (dlBox) dlBox.style.display = 'none';
      if (modeBadge) modeBadge.style.display = 'inline-block';
    } else {
      if (dlBox) dlBox.style.display = 'flex';
      if (modeBadge) modeBadge.style.display = 'none';
    }
    return true;
  }

  // ==========================================
  // 1. OVERVIEW KPIs & SPOTLIGHT CARDS
  // ==========================================
  function hydrateOverview() {
    const dq = data.dataQuality || {};

    if (dq.screened_active_universe !== undefined) {
      const pill = document.getElementById('pillUniverse');
      const kpi = document.getElementById('kpiScreened');
      const sub = document.getElementById('kpiQualifiedSub');
      if (pill) pill.textContent = `${dq.screened_active_universe} Active Candidates`;
      if (kpi) kpi.textContent = dq.screened_active_universe;
      if (sub) sub.textContent = `${dq.qualified_batters ?? 0} batters · ${dq.qualified_bowlers ?? 0} bowlers · ${dq.qualified_allrounders ?? 0} dual`;
      const uTab = document.querySelector('.pill-tab[data-tab="universe"]');
      if (uTab) uTab.textContent = `Screened Candidate Pool (${dq.screened_active_universe})`;
      const uOpt = document.querySelector('#universeFilter option[value="ALL"]');
      if (uOpt) uOpt.textContent = `All Screened Candidates (${dq.screened_active_universe})`;
    }
    if (dq.active_matches !== undefined) {
      const pillM = document.getElementById('pillMatches');
      const kpiM = document.getElementById('kpiMatches');
      const abSub = document.getElementById('kpiAbandonedSub');
      if (pillM) pillM.textContent = `${dq.active_matches} Played Matches`;
      if (kpiM) kpiM.textContent = `${dq.active_matches} / ${dq.scheduled_matches ?? dq.active_matches}`;
      if (abSub && dq.abandoned_washouts !== undefined) {
        abSub.textContent = `${dq.abandoned_washouts} scheduled fixtures abandoned (rain)`;
      }
    }
    if (dq.total_deliveries !== undefined) {
      const pillD = document.getElementById('pillDeliveries');
      const kpiD = document.getElementById('kpiDeliveries');
      const formattedD = Number(dq.total_deliveries).toLocaleString();
      if (pillD) pillD.textContent = `${formattedD} Deliveries`;
      if (kpiD) kpiD.textContent = formattedD;
    }
    if (dq.qualified_batters !== undefined) {
      const batBadge = document.getElementById('batCohortBadge');
      if (batBadge) batBadge.textContent = `BRS Cohort: N = ${dq.qualified_batters}`;
    }
    if (dq.qualified_bowlers !== undefined) {
      const bowlBadge = document.getElementById('bowlCohortBadge');
      if (bowlBadge) bowlBadge.textContent = `PRS Cohort: N = ${dq.qualified_bowlers}`;
    }
    if (dq.tau_bat && dq.tau_bowl) {
      const tauEl = document.getElementById('kpiTauSub');
      if (tauEl) tauEl.innerHTML = `&tau;<sub>bat</sub> = ${dq.tau_bat}b &middot; &tau;<sub>bowl</sub> = ${dq.tau_bowl}b`;
    }

    // #1 Overall Spotlight
    const topOv = data.overall[0];
    if (topOv) {
      document.getElementById('spotOvName').textContent = topOv.player_name;
      document.getElementById('spotOvRole').innerHTML = `${topOv.primary_role} · Overall: <strong>${Number(topOv.overall_reliability_score).toFixed(1)}</strong>`;
      document.getElementById('spotOvStats').innerHTML = `
        <div><div class="stat-metric-label">Z_adj</div><div class="stat-metric-val tabular" style="color:#D6B46A;">+${Number(topOv.cross_role_z_score).toFixed(2)}</div></div>
        <div><div class="stat-metric-label">Precision</div><div class="stat-metric-val tabular">${Number(topOv.precision_weight || 0).toFixed(2)}</div></div>
        <div><div class="stat-metric-label">Matches</div><div class="stat-metric-val tabular">${Math.round(topOv.matches || 0)}</div></div>
      `;
      document.getElementById('spotOvNote').textContent = topOv.pressure_evidence || topOv.why_ranked || '';
      document.getElementById('spotlightOverallCard').onclick = () => window.inspectPlayer(topOv.player_id, 'overall');
    }

    // #1 Batter Spotlight
    const topBat = data.batters[0];
    if (topBat) {
      document.getElementById('spotBatName').textContent = topBat.player_name;
      document.getElementById('spotBatRole').innerHTML = `${topBat.primary_role} · BRS: <strong>${Number(topBat.reliability_score).toFixed(1)}</strong>`;
      document.getElementById('spotBatStats').innerHTML = `
        <div><div class="stat-metric-label">Pres SR</div><div class="stat-metric-val tabular" style="color:#24C58A;">${Number(topBat.pres_sr).toFixed(1)}</div></div>
        <div><div class="stat-metric-label">Norm SR</div><div class="stat-metric-val tabular">${Number(topBat.norm_sr).toFixed(1)}</div></div>
        <div><div class="stat-metric-label">Δ Uplift</div><div class="stat-metric-val tabular delta-positive">+${Number(topBat.delta_sr).toFixed(1)}</div></div>
      `;
      document.getElementById('spotBatNote').textContent = `${Math.round(topBat.pres_balls_faced)} pressure balls across ${Math.round(topBat.total_matches)} matches. ${topBat.caveats || ''}`;
      document.getElementById('spotlightBatterCard').onclick = () => window.inspectPlayer(topBat.player_id, 'batter');
    }

    // #1 Bowler Spotlight
    const topBowl = data.bowlers[0];
    if (topBowl) {
      document.getElementById('spotBowlName').textContent = topBowl.player_name;
      document.getElementById('spotBowlRole').innerHTML = `${topBowl.primary_role} · PRS: <strong>${Number(topBowl.reliability_score).toFixed(1)}</strong>`;
      document.getElementById('spotBowlStats').innerHTML = `
        <div><div class="stat-metric-label">Pres Econ</div><div class="stat-metric-val tabular" style="color:#24C58A;">${Number(topBowl.pres_economy).toFixed(2)}</div></div>
        <div><div class="stat-metric-label">Norm Econ</div><div class="stat-metric-val tabular">${Number(topBowl.norm_economy).toFixed(2)}</div></div>
        <div><div class="stat-metric-label">Δ Econ</div><div class="stat-metric-val tabular delta-positive">${Number(topBowl.delta_economy).toFixed(2)}</div></div>
      `;
      document.getElementById('spotBowlNote').textContent = `${Math.round(topBowl.pres_legal_balls)} pressure balls (${Math.round(topBowl.pres_wickets)} wkts) across ${Math.round(topBowl.total_matches)} matches. ${topBowl.caveats || ''}`;
      document.getElementById('spotlightBowlerCard').onclick = () => window.inspectPlayer(topBowl.player_id, 'bowler');
    }
  }

  // ==========================================
  // 2. MODAL / PLAYER DOSSIER
  // ==========================================
  function openPlayerProfile(player, type) {
    if (!player) return;

    document.getElementById('modalPlayerName').textContent = player.player_name || '';
    document.getElementById('modalPlayerRole').textContent = `${player.primary_role || 'Eligible Player'} · Rank #${player.rank || '-'} · ID ${player.player_id}`;

    const matrix = document.getElementById('modalStatsMatrix');
    const strategyEl = document.getElementById('modalStrategyText');
    const caveatBox = document.getElementById('modalCaveatContainer');
    const caveatEl = document.getElementById('modalCaveatText');

    if (type === 'batter') {
      matrix.innerHTML = `
        <div class="matrix-card">
          <div class="matrix-label">Pressure Strike Rate</div>
          <div class="matrix-val tabular" style="color:#24C58A;">${Number(player.pres_sr).toFixed(1)}</div>
          <div class="matrix-sub">Normal: ${Number(player.norm_sr).toFixed(1)} (Δ ${Number(player.delta_sr) >= 0 ? '+' : ''}${Number(player.delta_sr).toFixed(1)})</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Sample Exposure</div>
          <div class="matrix-val tabular">${Math.round(player.total_matches)} <span style="font-size:0.75rem; color:#A1A8BC;">matches</span></div>
          <div class="matrix-sub">${Math.round(player.pres_runs)} runs / ${Math.round(player.pres_balls_faced)} pres balls</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Shrunk Pressure SR</div>
          <div class="matrix-val tabular">${Number(player.shrunk_pres_sr || player.pres_sr).toFixed(1)}</div>
          <div class="matrix-sub">Boundary: ${Number(player.pres_boundary_pct).toFixed(1)}% · Dot: ${Number(player.pres_dot_pct).toFixed(1)}%</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">95% Bootstrap CI</div>
          <div class="matrix-val tabular" style="font-size: 0.95rem; color:#D6B46A;">[${Number(player.ci_lower).toFixed(1)}, ${Number(player.ci_upper).toFixed(1)}]</div>
          <div class="matrix-sub">Std Error: ±${Number(player.std_error).toFixed(1)}</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">BRS Reliability</div>
          <div class="matrix-val tabular" style="color:#E84D87;">${Number(player.reliability_score).toFixed(1)} / 100</div>
          <div class="matrix-sub">IPL: ${Math.round(player.ipl_balls_faced || 0)}b · T20I: ${Math.round(player.t20i_balls_faced || 0)}b</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Overall Strike Rate</div>
          <div class="matrix-val tabular">${Number(player.overall_sr).toFixed(1)}</div>
          <div class="matrix-sub">${Math.round(player.total_balls_faced || 0)} career balls in window</div>
        </div>
      `;
      strategyEl.textContent = player.rr_auction_rationale || '';
      caveatEl.textContent = player.caveats || 'Broad multi-season sample.';
      caveatBox.style.display = 'block';
    } else if (type === 'bowler') {
      matrix.innerHTML = `
        <div class="matrix-card">
          <div class="matrix-label">Pressure Economy</div>
          <div class="matrix-val tabular" style="color:#24C58A;">${Number(player.pres_economy).toFixed(2)}</div>
          <div class="matrix-sub">Normal: ${Number(player.norm_economy).toFixed(2)} (Δ ${Number(player.delta_economy) > 0 ? '+' : ''}${Number(player.delta_economy).toFixed(2)})</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Sample Exposure</div>
          <div class="matrix-val tabular">${Math.round(player.total_matches)} <span style="font-size:0.75rem; color:#A1A8BC;">matches</span></div>
          <div class="matrix-sub">${Math.round(player.pres_wickets)} wkts / ${Math.round(player.pres_legal_balls)} pres balls</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Death Economy (16–20)</div>
          <div class="matrix-val tabular">${Number(player.death_economy).toFixed(2)}</div>
          <div class="matrix-sub">Shrunk Pres Econ: ${Number(player.shrunk_pres_economy || player.pres_economy).toFixed(2)}</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">95% Bootstrap CI</div>
          <div class="matrix-val tabular" style="font-size: 0.95rem; color:#D6B46A;">[${Number(player.ci_lower).toFixed(2)}, ${Number(player.ci_upper).toFixed(2)}]</div>
          <div class="matrix-sub">Std Error: ±${Number(player.std_error).toFixed(2)}</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">PRS Reliability</div>
          <div class="matrix-val tabular" style="color:#E84D87;">${Number(player.reliability_score).toFixed(1)} / 100</div>
          <div class="matrix-sub">IPL: ${Math.round(player.ipl_legal_balls || 0)}b · T20I: ${Math.round(player.t20i_legal_balls || 0)}b</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Overall Economy</div>
          <div class="matrix-val tabular">${Number(player.overall_economy).toFixed(2)}</div>
          <div class="matrix-sub">${Number(player.total_overs || 0).toFixed(1)} overs · ${Math.round(player.total_wickets || 0)} wkts</div>
        </div>
      `;
      strategyEl.textContent = player.rr_auction_rationale || '';
      caveatEl.textContent = player.caveats || 'Broad multi-season sample.';
      caveatBox.style.display = 'block';
    } else if (type === 'overall') {
      matrix.innerHTML = `
        <div class="matrix-card">
          <div class="matrix-label">Overall Rating</div>
          <div class="matrix-val tabular" style="color:#24C58A;">${Number(player.overall_reliability_score).toFixed(1)}</div>
          <div class="matrix-sub">Z_adj: +${Number(player.cross_role_z_score).toFixed(2)} SD</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Precision Weight</div>
          <div class="matrix-val tabular" style="color:#D6B46A;">${Number(player.precision_weight || 0).toFixed(3)}</div>
          <div class="matrix-sub">${Math.round(player.matches || 0)} matches · ${Math.round(player.ipl_deliveries || 0)} IPL balls</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Role Scores</div>
          <div class="matrix-val tabular" style="font-size:0.95rem; color:#E84D87;">BRS ${Number(player.batting_brs || 0) > 0 ? Number(player.batting_brs).toFixed(1) : '-'} · PRS ${Number(player.bowling_prs || 0) > 0 ? Number(player.bowling_prs).toFixed(1) : '-'}</div>
          <div class="matrix-sub">${player.pressure_evidence || ''}</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">95% Bootstrap CI</div>
          <div class="matrix-val tabular" style="font-size:0.88rem; color:#D6B46A;">${player.primary_ci_95 || '-'}</div>
          <div class="matrix-sub">Bat: ${player.bat_ci_95 || '-'} · Bowl: ${player.bowl_ci_95 || '-'}</div>
        </div>
      `;
      strategyEl.innerHTML = `<strong>Why Ranked:</strong> ${player.why_ranked || ''}<br><strong>RR Fit:</strong> ${player.rr_role_recommendation || ''} — ${player.squad_building_value || ''}`;
      caveatEl.textContent = player.risks_uncertainties || 'Validated multi-season track record.';
      caveatBox.style.display = 'block';
    } else {
      matrix.innerHTML = `
        <div class="matrix-card">
          <div class="matrix-label">Batting BRS</div>
          <div class="matrix-val tabular" style="color:#E84D87;">${Number(player.batting_brs || 0).toFixed(1)}</div>
          <div class="matrix-sub">Pres SR: ${Number(player.pres_sr || 0).toFixed(1)} (${Math.round(player.pres_balls_faced || 0)}b)</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Bowling PRS</div>
          <div class="matrix-val tabular" style="color:#D6B46A;">${Number(player.bowling_prs || 0).toFixed(1)}</div>
          <div class="matrix-sub">Pres Econ: ${Number(player.pres_economy || 0).toFixed(2)} (${Math.round(player.pres_legal_balls || 0)}b)</div>
        </div>
        <div class="matrix-card">
          <div class="matrix-label">Dual Balance</div>
          <div class="matrix-val tabular" style="color:#24C58A;">${Number(player.allrounder_composite_score || 0).toFixed(1)}</div>
          <div class="matrix-sub">50% BRS + 50% PRS</div>
        </div>
      `;
      strategyEl.textContent = player.rr_strategic_value || '';
      caveatBox.style.display = 'none';
    }

    modalBackdrop.classList.add('open');
  }

  window.inspectPlayer = function (id, type) {
    let p = null;
    if (type === 'batter') p = data.batters.find(x => x.player_id === id);
    else if (type === 'bowler') p = data.bowlers.find(x => x.player_id === id);
    else if (type === 'allrounder') p = (data.allrounders || []).find(x => x.player_id === id);
    else p = data.overall.find(x => x.player_id === id);
    if (p) openPlayerProfile(p, type);
  };

  if (modalClose) {
    modalClose.addEventListener('click', () => modalBackdrop.classList.remove('open'));
  }
  if (modalBackdrop) {
    modalBackdrop.addEventListener('click', (e) => {
      if (e.target === modalBackdrop) modalBackdrop.classList.remove('open');
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalBackdrop.classList.contains('open')) {
      modalBackdrop.classList.remove('open');
    }
  });

  // ==========================================
  // 3. SORTING HELPER & TABLES
  // ==========================================
  function sortRows(rows, key, asc) {
    return [...rows].sort((a, b) => {
      const va = a[key];
      const vb = b[key];
      if (typeof va === 'number' && typeof vb === 'number') {
        return asc ? va - vb : vb - va;
      }
      return asc
        ? String(va || '').localeCompare(String(vb || ''))
        : String(vb || '').localeCompare(String(va || ''));
    });
  }

  function renderBattersTable() {
    const tbody = document.getElementById('battersTableBody');
    if (!tbody) return;
    const { key, asc } = sortState.batters;
    const rows = sortRows(data.batters, key, asc);
    tbody.innerHTML = rows.map(p => {
      const deltaClass = p.delta_sr >= 0 ? 'delta-positive' : 'delta-negative';
      const deltaSign = p.delta_sr >= 0 ? '+' : '';
      return `
        <tr onclick="window.inspectPlayer(${p.player_id}, 'batter')">
          <td><span class="rank-badge ${p.rank <= 3 ? 'top3' : ''}">#${p.rank}</span></td>
          <td>
            <div class="player-name-cell">${p.player_name}</div>
            <div class="player-sub-text">ID: ${p.player_id}</div>
          </td>
          <td><span class="role-pill">${p.primary_role}</span></td>
          <td class="tabular">${Math.round(p.total_matches || 0)}</td>
          <td><span class="score-pill-pink tabular">${Number(p.reliability_score).toFixed(1)}</span></td>
          <td class="tabular" style="font-weight:700; color:#24C58A;">${Number(p.pres_sr).toFixed(1)}</td>
          <td class="tabular">${Number(p.norm_sr).toFixed(1)}</td>
          <td class="tabular ${deltaClass}">${deltaSign}${Number(p.delta_sr).toFixed(1)}</td>
          <td class="tabular">${Math.round(p.pres_balls_faced)}</td>
          <td class="tabular" style="color:#D6B46A; font-size:0.8rem;">[${Number(p.ci_lower).toFixed(1)}, ${Number(p.ci_upper).toFixed(1)}]</td>
          <td style="font-size:0.74rem; color:#A1A8BC; max-width:250px; white-space:normal;">${p.caveats || '-'}</td>
        </tr>
      `;
    }).join('');
  }

  function renderBowlersTable() {
    const tbody = document.getElementById('bowlersTableBody');
    if (!tbody) return;
    const { key, asc } = sortState.bowlers;
    const rows = sortRows(data.bowlers, key, asc);
    tbody.innerHTML = rows.map(p => {
      const deltaClass = p.delta_economy <= 0 ? 'delta-positive' : 'delta-negative';
      const deltaSign = p.delta_economy > 0 ? '+' : '';
      return `
        <tr onclick="window.inspectPlayer(${p.player_id}, 'bowler')">
          <td><span class="rank-badge ${p.rank <= 3 ? 'top3' : ''}">#${p.rank}</span></td>
          <td>
            <div class="player-name-cell">${p.player_name}</div>
            <div class="player-sub-text">ID: ${p.player_id}</div>
          </td>
          <td><span class="role-pill">${p.primary_role}</span></td>
          <td class="tabular">${Math.round(p.total_matches || 0)}</td>
          <td><span class="score-pill-gold tabular">${Number(p.reliability_score).toFixed(1)}</span></td>
          <td class="tabular" style="font-weight:700; color:#24C58A;">${Number(p.pres_economy).toFixed(2)}</td>
          <td class="tabular">${Number(p.norm_economy).toFixed(2)}</td>
          <td class="tabular ${deltaClass}">${deltaSign}${Number(p.delta_economy).toFixed(2)}</td>
          <td class="tabular">${Math.round(p.pres_legal_balls)}</td>
          <td class="tabular">${Math.round(p.pres_wickets)}</td>
          <td class="tabular" style="color:#D6B46A; font-size:0.8rem;">[${Number(p.ci_lower).toFixed(2)}, ${Number(p.ci_upper).toFixed(2)}]</td>
          <td style="font-size:0.74rem; color:#A1A8BC; max-width:250px; white-space:normal;">${p.caveats || '-'}</td>
        </tr>
      `;
    }).join('');
  }

  function renderOverallTable() {
    const tbody = document.getElementById('overallTableBody');
    if (!tbody) return;
    const { key, asc } = sortState.overall;
    const rows = sortRows(data.overall, key, asc);
    tbody.innerHTML = rows.map(p => `
      <tr onclick="window.inspectPlayer(${p.player_id}, 'overall')">
        <td><span class="rank-badge ${p.rank <= 3 ? 'top3' : ''}">#${p.rank}</span></td>
        <td>
          <div class="player-name-cell">${p.player_name}</div>
          <div class="player-sub-text">ID: ${p.player_id} · ${Math.round(p.matches || 0)}m</div>
        </td>
        <td><span class="role-pill">${p.primary_role}</span></td>
        <td><span class="score-pill-gold tabular">${Number(p.overall_reliability_score).toFixed(1)}</span></td>
        <td class="tabular" style="color:#24C58A; font-weight:700;">+${Number(p.cross_role_z_score).toFixed(2)}</td>
        <td class="tabular">${Number(p.precision_weight || 0).toFixed(2)}</td>
        <td class="tabular" style="color:#E84D87;">${Number(p.batting_brs) > 0 ? Number(p.batting_brs).toFixed(1) : '-'}</td>
        <td class="tabular" style="color:#D6B46A;">${Number(p.bowling_prs) > 0 ? Number(p.bowling_prs).toFixed(1) : '-'}</td>
        <td class="tabular" style="color:#D6B46A; font-size:0.78rem; white-space:normal;">${p.primary_ci_95 || '-'}</td>
        <td style="font-size:0.75rem; color:#A1A8BC; max-width:250px; white-space:normal;">${p.rr_role_recommendation || p.rr_strategic_value || ''}</td>
      </tr>
    `).join('');
  }

  function renderAllRoundersTable() {
    const tbody = document.getElementById('allroundersTableBody');
    if (!tbody) return;
    tbody.innerHTML = (data.allrounders || []).map(p => `
      <tr onclick="window.inspectPlayer(${p.player_id}, 'allrounder')">
        <td><span class="rank-badge ${p.rank <= 3 ? 'top3' : ''}">#${p.rank}</span></td>
        <td>
          <div class="player-name-cell">${p.player_name}</div>
          <div class="player-sub-text">ID: ${p.player_id}</div>
        </td>
        <td><span class="role-pill">${p.primary_role}</span></td>
        <td><span class="score-pill-pink tabular">${Number(p.allrounder_composite_score).toFixed(1)}</span></td>
        <td class="tabular" style="color:#E84D87;">${Number(p.batting_brs).toFixed(1)}</td>
        <td class="tabular" style="color:#D6B46A;">${Number(p.bowling_prs).toFixed(1)}</td>
        <td class="tabular" style="font-weight:700; color:#24C58A;">${Number(p.pres_sr).toFixed(1)}</td>
        <td class="tabular" style="font-weight:700; color:#24C58A;">${Number(p.pres_economy).toFixed(2)}</td>
        <td style="font-size:0.75rem; color:#A1A8BC; max-width:260px; white-space:normal;">${p.rr_strategic_value}</td>
      </tr>
    `).join('');
  }

  function renderUniverseTable(filterText = '', filterStatus = 'ALL') {
    const tbody = document.getElementById('universeTableBody');
    if (!tbody) return;
    const items = (data.allPlayers || []).filter(p => {
      const matchText = (p.player_name || '').toLowerCase().includes(filterText.toLowerCase()) ||
                        String(p.player_id).includes(filterText);
      const matchStatus = filterStatus === 'ALL' || p.eligibility_status === filterStatus;
      return matchText && matchStatus;
    });

    tbody.innerHTML = items.slice(0, 120).map(p => `
      <tr>
        <td class="tabular" style="color:#A1A8BC;">#${p.player_id}</td>
        <td><div class="player-name-cell">${p.player_name}</div></td>
        <td><span class="role-pill">${p.role}</span></td>
        <td class="tabular">${p.matches}</td>
        <td class="tabular">${p.balls_faced}</td>
        <td class="tabular">${p.balls_bowled}</td>
        <td><span class="eligibility-tag active">${p.eligibility_status}</span></td>
      </tr>
    `).join('');
  }

  // Sort Click Handlers
  document.querySelectorAll('.sortable-table th[data-sort]').forEach(th => {
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
      const tbl = th.getAttribute('data-table');
      const key = th.getAttribute('data-sort');
      if (sortState[tbl].key === key) {
        sortState[tbl].asc = !sortState[tbl].asc;
      } else {
        sortState[tbl].key = key;
        sortState[tbl].asc = (key === 'rank' || key === 'player_name' || key === 'pres_economy' || key === 'delta_economy');
      }
      if (tbl === 'batters') renderBattersTable();
      if (tbl === 'bowlers') renderBowlersTable();
      if (tbl === 'overall') renderOverallTable();
    });
  });

  // ==========================================
  // 4. DATA QUALITY & VALIDATION SECTION
  // ==========================================
  function renderDataQuality() {
    const grid = document.getElementById('dataQualityGrid');
    if (!grid) return;
    const dq = data.dataQuality || {};
    const val = dq.validation || {};
    const ts = dq.threshold_stability || [];
    const totalDel = Number(dq.total_deliveries || 0).toLocaleString();
    const nComp = dq.competitions ?? '--';
    const dateRange = dq.date_range || 'Configured Window';
    const actM = dq.active_matches ?? '--';
    const schM = dq.scheduled_matches ?? '--';
    const abM = dq.abandoned_washouts ?? 0;
    const qBat = dq.qualified_batters ?? 0;
    const qBowl = dq.qualified_bowlers ?? 0;

    grid.innerHTML = `
      <div class="methodology-pillar">
        <h3 class="pillar-title">Source Inventory &amp; Match Coverage</h3>
        <ul class="dq-list">
          <li><strong>Deliveries Analyzed:</strong> ${totalDel} rows across ${nComp} competitions (${dateRange}).</li>
          <li><strong>Played vs Scheduled Matches:</strong> ${actM} played matches out of ${schM} scheduled fixtures (${abM} rain washouts / 0-ball fixtures).</li>
          <li><strong>Identity Disambiguation:</strong> Player entities keyed strictly by verified numeric <code>player_id</code> to prevent homonym collisions.</li>
          <li><strong>Sample Thresholds:</strong> Batters ≥ 150 total balls &amp; ≥ 45 pressure balls (${qBat} qualified); Bowlers ≥ 150 legal balls &amp; ≥ 60 pressure balls (${qBowl} qualified).</li>
        </ul>
      </div>

      <div class="methodology-pillar">
        <h3 class="pillar-title">Out-of-Sample Temporal &amp; Sensitivity Checks</h3>
        <ul class="dq-list">
          <li><strong>Bowling Temporal Validation:</strong> Spearman $\\rho = ${Number(val.temporal_bowl_spearman ?? 0).toFixed(3)}$ ($p = ${Number(val.temporal_bowl_p_value ?? 0).toFixed(4)}$, $N = ${Math.round(val.temporal_bowl_n ?? 0)}$) — out-of-sample economy persistence check.</li>
          <li><strong>Batting Temporal Check:</strong> Raw out-of-sample strike-rate correlation ($\\rho = ${Number(val.temporal_bat_spearman ?? 0).toFixed(3)}$, $p = ${Number(val.temporal_bat_p_value ?? 0).toFixed(4)}$, $N = ${Math.round(val.temporal_bat_n ?? 0)}$) — motivating Empirical Bayes shrinkage and bootstrap CIs.</li>
          <li><strong>Weight Sensitivity:</strong> Across Execution-Heavy, Resilience-Heavy, Consistency-Heavy &amp; Flat weights, minimum rank correlation is $\\rho \\ge ${Number(val.bat_weight_min_rho ?? 0).toFixed(3)}$ (batting) and $\\rho \\ge ${Number(val.bowl_weight_min_rho ?? 0).toFixed(3)}$ (bowling).</li>
          <li><strong>Format Agreement:</strong> Batting $\\rho = ${Number(val.ipl_vs_comb_bat_spearman ?? 0).toFixed(3)}$, Bowling $\\rho = ${Number(val.ipl_vs_comb_bowl_spearman ?? 0).toFixed(3)}$.</li>
        </ul>
      </div>

      <div class="methodology-pillar" style="grid-column: 1 / -1;">
        <h3 class="pillar-title">Pressure Threshold Sensitivity &amp; Sample Caveats</h3>
        <p class="pillar-explanation" style="margin-bottom: 10px;">
          Sensitivity Top-5 overlap spans ${ts[0] ? ts[0].overlap_with_official_top5 : '--'} at baseline to ${ts[2] ? ts[2].overlap_with_official_top5 : '--'} under stricter sample gates.
          Small-sample qualifiers at the 45-ball batting floor and overseas performers without IPL deliveries carry explicit sample-sensitivity and transferability caveats in their player dossiers and official reports.
        </p>
      </div>
    `;
    renderMath(grid);
  }

  // ==========================================
  // 5. TABS, JUMP LINKS & SEARCH
  // ==========================================
  document.querySelectorAll('.pill-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.pill-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const targetPane = document.getElementById(`tab-${tab.getAttribute('data-tab')}`);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  document.querySelectorAll('.jump-pill').forEach(link => {
    link.addEventListener('click', () => {
      document.querySelectorAll('.jump-pill').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    });
  });

  const searchInput = document.getElementById('universeSearch');
  const filterSelect = document.getElementById('universeFilter');
  if (searchInput && filterSelect) {
    const handleFilter = () => renderUniverseTable(searchInput.value, filterSelect.value);
    searchInput.addEventListener('input', handleFilter);
    filterSelect.addEventListener('change', handleFilter);
  }

  // ==========================================
  // 6. CHART.JS VISUALIZATIONS
  // ==========================================
  function initCharts() {
    if (typeof Chart === 'undefined') return;

    const ctxBat = document.getElementById('battingChartCanvas');
    if (ctxBat && data.batters.length > 0) {
      const labels = data.batters.map(p => p.player_name.split(' ').slice(-1)[0]);
      battingChart = new Chart(ctxBat, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            { label: 'Pressure SR', data: data.batters.map(p => p.pres_sr), backgroundColor: '#E84D87', borderRadius: 4 },
            { label: 'Normal Baseline SR', data: data.batters.map(p => p.norm_sr), backgroundColor: '#2A3660', borderRadius: 4 }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#F4F5FA', font: { size: 11 } } },
            tooltip: { callbacks: { title: (items) => data.batters[items[0].dataIndex].player_name } }
          },
          scales: {
            x: { ticks: { color: '#A1A8BC', font: { size: 10 } }, grid: { display: false } },
            y: { ticks: { color: '#A1A8BC', font: { size: 10 } }, grid: { color: '#1C2442' } }
          }
        }
      });
    }

    const ctxBowl = document.getElementById('bowlingChartCanvas');
    if (ctxBowl && data.bowlers.length > 0) {
      const labels = data.bowlers.map(p => p.player_name.split(' ').slice(-1)[0]);
      bowlingChart = new Chart(ctxBowl, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            { label: 'Pressure Economy', data: data.bowlers.map(p => p.pres_economy), backgroundColor: '#24C58A', borderRadius: 4 },
            { label: 'Normal Economy', data: data.bowlers.map(p => p.norm_economy), backgroundColor: '#2A3660', borderRadius: 4 }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#F4F5FA', font: { size: 11 } } },
            tooltip: { callbacks: { title: (items) => data.bowlers[items[0].dataIndex].player_name } }
          },
          scales: {
            x: { ticks: { color: '#A1A8BC', font: { size: 10 } }, grid: { display: false } },
            y: { ticks: { color: '#A1A8BC', font: { size: 10 } }, grid: { color: '#1C2442' } }
          }
        }
      });
    }
  }

  function bootDashboard() {
    if (!applyModeVisibility()) return;
    hydrateOverview();
    renderBattersTable();
    renderBowlersTable();
    renderOverallTable();
    renderAllRoundersTable();
    renderUniverseTable();
    renderDataQuality();
    initCharts();
    renderMath(document.body);
  }

  window.addEventListener('load', () => renderMath(document.body));
  bootDashboard();
})();
