"""Assemble index.html from template.html + molecule data + figures + tables."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "template.html")) as f:
    html = f.read()

with open(os.path.join(HERE, "mols.json")) as f:
    mols = json.load(f)

# ---- molecule data (trim fields the page does not use) ----
slim = [
    {
        "name": m["name"],
        "formula": m["formula"],
        "n_atoms": m["n_atoms"],
        "n_heavy": m["n_heavy"],
        "n_bonds": m["n_bonds"],
        "stable_set": m["stable_set"],
        "xyz": m["xyz"],
    }
    for m in mols
]
html = html.replace("/*MOLDATA*/", json.dumps(slim, separators=(",", ":")))

# ---- measured metrics for this checkpoint ----
MEASURED = os.path.join(HERE, "measured.html")
if os.path.exists(MEASURED):
    with open(MEASURED) as f:
        html = html.replace("<!--MEASURED-->", f.read())

# ---- figures ----
FIGS = {
    "<!--FIG_FRONT-->": """
    <figure>
      <img src="fig/front.png" alt="Molecule stability on QM9 plotted against number of function evaluations, with FlashMol at 4 to 8 NFE compared to GeoLDM, GeoLDM-respaced and recent few-step methods.">
      <figcaption><b>Figure 1 &middot; Molecule generation quality on QM9.</b> Comparable or superior performance with only 4 to 8 steps, against recent few-step molecule generative models. GeoLDM-respaced uses the respaced timesteps of &sect;4.2; GeoLDM uses the original DDPM timesteps.</figcaption>
    </figure>""",
    "<!--FIG_FRAMEWORK-->": """
    <figure>
      <img src="fig/training_diagram.png" alt="FlashMol training framework: the few-step generator produces molecules, the fake score network and discriminator update for five steps, then their outputs form the DMD and Jensen-Shannon gradients that update the generator.">
      <figcaption><b>Figure 2 &middot; Training framework.</b> Each iteration, the few-step generator <i>G</i> produces a batch of sampled molecules. The &mu;<sub>fake</sub> model approximating the fake score and the discriminator <i>D</i> are updated first, for five steps each, with the diffusion loss and the GAN loss. Their outputs then give the DMD and Jensen&ndash;Shannon gradients, which are mixed and applied to <i>G</i>.</figcaption>
    </figure>""",
    "<!--FIG_SCHEDULE-->": """
    <figure>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px">
        <img src="fig/vanilla/molecule_003.png" alt="4-step sample on the original GeoLDM schedule: scattered, disconnected atoms." style="border:0;background:transparent">
        <img src="fig/vanilla/molecule_001.png" alt="4-step sample on the original GeoLDM schedule." style="border:0;background:transparent">
        <img src="fig/vanilla/molecule_000.png" alt="4-step sample on the original GeoLDM schedule." style="border:0;background:transparent">
        <img src="fig/vanilla/molecule_002.png" alt="4-step sample on the original GeoLDM schedule." style="border:0;background:transparent">
        <img src="fig/resched/molecule_000.png" alt="4-step sample on the respaced schedule: a connected, chemically plausible molecule." style="border:0;background:transparent">
        <img src="fig/resched/molecule_001.png" alt="4-step sample on the respaced schedule." style="border:0;background:transparent">
        <img src="fig/resched/molecule_002.png" alt="4-step sample on the respaced schedule." style="border:0;background:transparent">
        <img src="fig/resched/molecule_005.png" alt="4-step sample on the respaced schedule." style="border:0;background:transparent">
      </div>
      <figcaption><b>Figure 3 &middot; Random 4-step samples from the multi-step teacher, no additional training.</b> Top row: original GeoLDM schedule &mdash; noisy and chemically invalid, with atoms left disconnected. Bottom row: the respaced schedule. Both rows are the same teacher weights at the same 4-step budget; only the timestep selection differs.</figcaption>
    </figure>""",
    "<!--FIG_RHO-->": """
    <figure>
      <img src="fig/rho_schedule.png" alt="Noise schedules plotted for several values of the exponent rho, showing how large rho pushes most steps to near-zero diffusion time.">
      <figcaption><b>Figure 4 &middot; Noise schedules for different &rho;.</b> The exponent in the respacing formula controls how steps are distributed between high and low noise. At &rho; = 7, more than 38% of the 1000 steps land at <i>t</i> &asymp; 0.</figcaption>
    </figure>""",
    "<!--FIG_VANILLA-->": """
    <figure>
      <img src="fig/vanilla_training_comparison.png" alt="DMD training dynamics under two sampling noise schedules; the uniform-schedule run fails to optimize while the respaced run trains stably.">
      <figcaption><b>Figure 5 &middot; Distillation training dynamics under different sampling noise schedules.</b> The 8-step student on uniform timesteps (blue) fails to optimize; on the respaced schedule (orange) training proceeds without gradient explosion, including in later stages.</figcaption>
    </figure>""",
    "<!--FIG_EPOCH-->": """
    <figure>
      <img src="fig/epoch-trade-off.png" alt="Across distillation epochs, molecule stability rises while valid-and-unique declines slightly.">
      <figcaption><b>Figure 6 &middot; Stability and diversity across training.</b> Molecule stability keeps increasing as distillation proceeds while valid-and-unique declines by a small margin. This is why the paper's protocol stops training when valid-and-unique starts to drop.</figcaption>
    </figure>""",
}
for k, v in FIGS.items():
    html = html.replace(k, v)

# ---- tables ----
TABLE_MAIN = """
    <div class="tbl-scroll">
    <table>
      <caption>Table 1 &middot; Unconditional molecule generation</caption>
      <thead>
        <tr>
          <th>Method</th><th>NFE</th>
          <th>QM9 Atom Sta</th><th>QM9 Mol Sta</th><th>QM9 Valid</th><th>QM9 V&amp;U</th>
          <th>DRUG Atom Sta</th><th>DRUG Valid</th>
        </tr>
      </thead>
      <tbody>
        <tr><td>Data</td><td>&mdash;</td><td>99.0</td><td>95.2</td><td>97.7</td><td>97.7</td><td>86.5</td><td>99.9</td></tr>
        <tr class="rule"><td>GDM-aug</td><td>1000</td><td>97.6</td><td>71.6</td><td>90.4</td><td>89.5</td><td>77.7</td><td>91.8</td></tr>
        <tr><td>EDM</td><td>1000</td><td>98.7</td><td>82.0</td><td>91.9</td><td>90.7</td><td>81.3</td><td>92.6</td></tr>
        <tr><td>EDM-Bridge</td><td>1000</td><td>98.8</td><td>84.6</td><td>92.0</td><td>90.7</td><td>82.4</td><td>92.8</td></tr>
        <tr><td>GeoLDM <span style="color:var(--muted)">(teacher)</span></td><td>1000</td><td>98.9</td><td>89.4</td><td>93.8</td><td class="best">92.7</td><td>84.4</td><td>99.3</td></tr>
        <tr><td>EquiFM</td><td>200</td><td>98.9</td><td>88.3</td><td>94.7</td><td>93.5</td><td>84.1</td><td>98.9</td></tr>
        <tr><td>GeoBFN</td><td>100</td><td>98.6</td><td>87.2</td><td>93.0</td><td>91.5</td><td>78.9</td><td>93.1</td></tr>
        <tr><td>GOAT</td><td>90</td><td>99.2</td><td>&mdash;</td><td>92.9</td><td>92.0</td><td>84.8</td><td>96.2</td></tr>
        <tr class="rule"><td>SLDM</td><td>50</td><td>98.70</td><td>88.09</td><td>92.84</td><td>89.53</td><td>&mdash;</td><td>&mdash;</td></tr>
        <tr><td>GeoRCG (EDM)</td><td>50</td><td>98.75</td><td>89.08</td><td>95.05</td><td>&mdash;</td><td>81.44</td><td>95.70</td></tr>
        <tr><td>AccGeoLDM</td><td>16</td><td>92.08</td><td>51.02</td><td>73.22</td><td>72.39</td><td>&mdash;</td><td>&mdash;</td></tr>
        <tr><td>MOLTD</td><td>12</td><td>99.40</td><td>92.53</td><td>96.04</td><td>92.0</td><td>86.88</td><td>95.33</td></tr>
        <tr class="rule"><td>GeoLDM-respaced</td><td>8</td><td>95.49</td><td>70.78</td><td>87.13</td><td>81.48</td><td>64.35</td><td>90.44</td></tr>
        <tr class="ours"><td>FlashMol</td><td>8</td><td>99.55</td><td>94.87</td><td>96.97</td><td>87.51</td><td>89.98</td><td>99.86</td></tr>
        <tr class="rule"><td>GeoLDM-respaced</td><td>5</td><td>82.11</td><td>27.96</td><td>62.10</td><td>59.20</td><td>18.27</td><td>82.07</td></tr>
        <tr class="ours"><td>FlashMol</td><td>5</td><td>98.73</td><td>87.05</td><td>92.67</td><td>78.83</td><td>87.69</td><td>99.69</td></tr>
        <tr class="rule"><td>GeoLDM-respaced</td><td>4</td><td>72.35</td><td>12.43</td><td>45.24</td><td>42.53</td><td>8.30</td><td>84.65</td></tr>
        <tr class="ours"><td>FlashMol</td><td>4</td><td>97.70</td><td>83.89</td><td>90.70</td><td>72.70</td><td>84.72</td><td>99.72</td></tr>
      </tbody>
    </table>
    <p class="tbl-note">All values in percent. FlashMol rows beat the respaced teacher at the same NFE on every metric shown. QM9 figures are means over three runs of 10,000 samples; the paper reports standard deviations of 0.0&ndash;0.5. The MOLTD V&amp;U entry is the authors' own estimate.</p>
    </div>"""

TABLE_COND = """
    <div class="tbl-scroll">
    <table>
      <caption>Table 2 &middot; Conditional generation, MAE against the target property (lower is better)</caption>
      <thead>
        <tr><th>Method</th><th>NFE</th><th>&alpha; (Bohr&sup3;)</th><th>&Delta;&epsilon; (meV)</th><th>HOMO (meV)</th><th>LUMO (meV)</th><th>&mu; (D)</th><th>C<sub>v</sub> (cal/mol&middot;K)</th></tr>
      </thead>
      <tbody>
        <tr><td>QM9 <span style="color:var(--muted)">(lower bound)</span></td><td>&mdash;</td><td>0.10</td><td>64</td><td>39</td><td>36</td><td>0.043</td><td>0.040</td></tr>
        <tr class="rule"><td>Random <span style="color:var(--muted)">(upper bound)</span></td><td>&mdash;</td><td>9.01</td><td>1470</td><td>645</td><td>1457</td><td>1.616</td><td>6.857</td></tr>
        <tr><td>N<sub>atoms</sub></td><td>&mdash;</td><td>3.86</td><td>866</td><td>426</td><td>813</td><td>1.053</td><td>1.971</td></tr>
        <tr><td>EDM</td><td>1000</td><td>2.76</td><td>655</td><td>356</td><td>584</td><td>1.111</td><td>1.101</td></tr>
        <tr><td>GeoLDM</td><td>1000</td><td>2.37</td><td>587</td><td>340</td><td>522</td><td>1.108</td><td>1.025</td></tr>
        <tr><td>GeoBFN</td><td>100</td><td>2.34</td><td>577</td><td class="best">328</td><td>516</td><td>0.998</td><td>0.949</td></tr>
        <tr><td>GeoLDM-respaced</td><td>32</td><td>2.14</td><td>565</td><td>342</td><td>491</td><td class="best">0.985</td><td>0.933</td></tr>
        <tr class="ours"><td>FlashMol</td><td>32</td><td>2.12</td><td>556</td><td>330</td><td>489</td><td>0.988</td><td>0.926</td></tr>
      </tbody>
    </table>
    <p class="tbl-note">A separate teacher and student are trained per property. GeoLDM-respaced at the same 32 NFE is already close, so most of the conditional gain comes from respacing rather than from distillation.</p>
    </div>"""

TABLE_ABL = """
    <div class="minitbl">
      <div>
        <table>
          <caption>Schedule exponent &rho;</caption>
          <thead><tr><th>&rho;</th><th>Mol Sta</th><th>V&amp;U</th></tr></thead>
          <tbody>
            <tr><td>2</td><td>69.93</td><td>81.27</td></tr>
            <tr><td>2.25</td><td class="best">70.78</td><td class="best">81.48</td></tr>
            <tr><td>2.75</td><td>68.46</td><td>81.35</td></tr>
            <tr><td>5</td><td>35.23</td><td>61.95</td></tr>
          </tbody>
        </table>
        <p class="tbl-note">Teacher only, no distillation.</p>
      </div>
      <div>
        <table>
          <caption>Divergence regularizer</caption>
          <thead><tr><th>Objective</th><th>Mol Sta</th><th>V&amp;U</th></tr></thead>
          <tbody>
            <tr><td>DMD only</td><td>81.51</td><td>68.84</td></tr>
            <tr><td>Forward KL</td><td>58.09</td><td>59.10</td></tr>
            <tr><td>JS only</td><td>83.34</td><td>72.36</td></tr>
            <tr><td>DMD + JS</td><td class="best">83.89</td><td class="best">72.70</td></tr>
          </tbody>
        </table>
        <p class="tbl-note">4 NFE, &lambda; = 0.1.</p>
      </div>
      <div>
        <table>
          <caption>Sampling method</caption>
          <thead><tr><th>NFE</th><th>Respaced</th><th>DDIM</th><th>Consist.</th></tr></thead>
          <tbody>
            <tr><td>4</td><td class="best">12.43</td><td>0.01</td><td>0.00</td></tr>
            <tr><td>8</td><td class="best">70.78</td><td>5.06</td><td>6.71</td></tr>
            <tr><td>16</td><td class="best">94.61</td><td>41.84</td><td>59.94</td></tr>
          </tbody>
        </table>
        <p class="tbl-note">Molecule stability, teacher only.</p>
      </div>
    </div>"""

html = html.replace("<!--TABLE_MAIN-->", TABLE_MAIN)
html = html.replace("<!--TABLE_COND-->", TABLE_COND)
html = html.replace("<!--TABLE_ABL-->", TABLE_ABL)

out = os.path.join(HERE, "index.html")
with open(out, "w") as f:
    f.write(html)

left = [t for t in ("<!--FIG_", "<!--TABLE_", "/*MOLDATA*/", "<!--MEASURED-->") if t in html]
print(f"wrote {out}  ({len(html)/1024:.0f} KB)")
print("unresolved placeholders:", left or "none")
