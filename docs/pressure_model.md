# Continuous Pressure Modeling Methodology
## SupeRR Selector Season 2 — Rajasthan Royals IPL 2027 Auction Analytics

**Author:** Gandhi Kalasi  
**Methodology:** Context-Aware Non-Linear Dynamic Pressure Modeling in T20 Cricket  

---

## 1. Cricket Problem Framing: What Constitutes Pressure?

In limited-overs cricket, pressure is not simply the accumulation of runs or the identity of the opposition. Pressure is the **acute psychological and tactical urgency created by the match state**. It is defined by:
1. **Resource Scarcity:** Few wickets remaining relative to target.
2. **Rate Stress:** The divergence between the required scoring rate and the par scoring rate.
3. **Temporal Horizon:** Decreasing deliveries remaining to execute tactical objectives.
4. **Contestability / Closeness:** Whether the game is on a knife's edge or effectively decided.

The SupeRR Selector Pressure Model evaluates every delivery on a continuous $[0, 100]$ scale, uniquely distinguishing the pressure experienced by batters from that experienced by bowlers.

---

## 2. Mathematical Formulation

### A. Second Innings (Chasing Situations)

When chasing, the match state is completely quantified by the current score, balls remaining, wickets down, and target.

#### 1. Rate Stress Function ($S_{\text{rate}}$)
$$\text{RRR} = \frac{\text{Runs Needed}}{\text{Balls Remaining}} \times 6$$
Rate stress accelerates non-linearly using a logistic sigmoid centered at a demanding T20 chase rate of 9.50 runs/over:
$$S_{\text{rate}} = \frac{1}{1 + e^{-0.45 \cdot (\text{RRR} - 9.50)}}$$

#### 2. Resource Scarcity ($S_{\text{wicket}}$)
$$S_{\text{wicket}} = \left(\frac{11 - \text{Wickets in Hand}}{10}\right)^{1.2}$$

#### 3. Temporal Urgency ($S_{\text{urgency}}$)
$$S_{\text{urgency}} = 1 - \left(\frac{\text{Balls Remaining}}{\text{Max Balls}}\right)^{0.75}$$

#### 4. Match Contestability / Closeness ($C_{\text{match}}$)
Using a win-probability z-score that models expected run generation per wicket remaining:
$$z = \frac{\text{Runs Needed} - \text{Balls Remaining} \cdot [1.35 - 0.07 \cdot (10 - \text{Wickets in Hand})]}{\sqrt{\text{Balls Remaining} \cdot 1.8 + 1.0}}$$
$$P_{\text{win}} = \frac{1}{1 + e^{1.10 \cdot z}}$$
$$C_{\text{match}} = 4 \cdot P_{\text{win}} \cdot (1 - P_{\text{win}})$$
When $P_{\text{win}} = 0.50$ (a 50-50 nail-biter), $C_{\text{match}} = 1.0$. If a match is effectively settled ($P_{\text{win}} \rightarrow 0$ or $1$), $C_{\text{match}} \rightarrow 0$.

#### 5. Composite Chasing Batting Pressure ($P_{\text{bat, chase}}$)
$$P_{\text{bat, chase}} = 100 \cdot \Big[0.38 S_{\text{rate}} + 0.32 S_{\text{wicket}} + 0.20 S_{\text{urgency}} + 0.10 (S_{\text{rate}} \cdot S_{\text{urgency}})\Big] \cdot \big(0.35 + 0.65 C_{\text{match}}\big)$$

#### 6. Second-Innings Bowling Modulation ($P_{\text{bowl, chase}}$)
Bowlers defending a tight target face intense pressure in death overs, but minimal stress when opposition is 8 down needing 18 an over (clean-up mode):
$$P_{\text{bowl, chase}} = 100 \cdot \Big[0.42 (1 - 0.40 S_{\text{rate}}) + 0.28 S_{\text{urgency}} + 0.30 C_{\text{match}}\Big] \cdot \Phi_{\text{defense}}$$

---

### B. First Innings (Setting a Target)

When setting a target, there is no fixed RRR. Pressure is driven by **par score deficit**, **early cluster wickets**, and **death overs acceleration**.

#### 1. Projected Total via Resource Retention
Using the standard 170 par benchmark for elite T20 venues:
$$R_{\text{res}} = \left(\frac{\text{Balls Remaining}}{\text{Max Balls}}\right)^{0.65} \cdot \left(\frac{\text{Wickets in Hand}}{10}\right)^{0.50}$$
$$\text{Score}_{\text{projected}} = \text{Current Runs} + 170 \cdot R_{\text{res}}$$
$$\Delta_{\text{par}} = \frac{170 - \text{Score}_{\text{projected}}}{170}$$

#### 2. Crisis & Acceleration Factors
$$\text{Crisis} = \left(\frac{\text{Wickets Lost}}{9}\right)^{1.2}$$
$$\text{Deficit} = \text{clip}\left(\frac{\Delta_{\text{par}} + 0.20}{0.45}, 0, 1\right)$$
$$\text{Death Accel} = \left(1 - \frac{\text{Balls Remaining}}{\text{Max Balls}}\right)^{1.50}$$

#### 3. First-Innings Batting Pressure ($P_{\text{bat, 1st}}$)
$$P_{\text{bat, 1st}} = 100 \cdot \Big[0.35 \cdot \text{Deficit} + 0.35 \cdot \text{Crisis} + 0.30 \cdot \text{Death Accel}\Big]$$

---

### C. Super Overs (Innings $\ge 3$)
Sudden-death leverage is maximal. Pressure is bounded within $[85, 100]$:
$$P_{\text{super}} = \text{clip}(85 + 2.5 \cdot \text{Ball Number}, 85, 100)$$

---

## 3. Operational Pressure Thresholds
- **High Pressure Threshold for Batting:** $P_{\text{bat}} \ge 50.0$ (Captures high-leverage chase overs and 1st-innings crisis/death phases).
- **High Pressure Threshold for Bowling:** $P_{\text{bowl}} \ge 55.0$ (Captures critical defensive spells, death overs, and close chase containment).

