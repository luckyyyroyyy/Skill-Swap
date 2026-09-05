import os

def generate_svg(stroke_w=4.2, glow_type="apple"):
    # Authentic Apple Hello
    L = "M 18 -45 C 22 -72, 32 -88, 40 -88 C 45 -88, 40 -76, 32 -50 C 24 -24, 18 -4, 18 0 C 18 4, 10 4, 8 -1 C 6 -6, 14 -6, 24 -4 C 36 -2, 48 0, 56 0"
    w_L = 56
    
    x = w_L
    u = f"C {x+6} -20, {x+14} -40, {x+18} -40 C {x+18} -40, {x+15} -14, {x+15} -4 C {x+15} 2, {x+25} 2, {x+28} -4 L {x+30} -40 C {x+30} -40, {x+29} -12, {x+29} -3 C {x+29} 1, {x+34} 1, {x+40} 0"
    w_u = 40
    
    x += w_u
    c = f"C {x+6} -22, {x+14} -40, {x+22} -40 C {x+26} -40, {x+25} -32, {x+20} -30 C {x+12} -28, {x+7} -18, {x+7} -8 C {x+7} 2, {x+16} 2, {x+28} 0"
    w_c = 28
    
    x += w_c
    k = f"C {x+8} -28, {x+18} -86, {x+24} -86 C {x+28} -86, {x+22} -58, {x+16} -28 L {x+16} 0 C {x+16} -20, {x+28} -26, {x+28} -16 C {x+28} -8, {x+18} -8, {x+18} -8 C {x+23} -4, {x+28} 0, {x+36} 0"
    w_k = 36
    
    x += w_k
    y = f"C {x+6} -20, {x+14} -40, {x+18} -40 C {x+18} -40, {x+15} -14, {x+15} -4 C {x+15} 2, {x+25} 2, {x+28} -4 L {x+30} -40 L {x+28} 24 C {x+26} 44, {x+12} 44, {x+5} 32 C {x+1} 22, {x+14} 10, {x+32} -4"
    w_y = 32
    
    total_w = x + w_y
    full_path = f"{L} {u} {c} {k} {y}"
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 300" width="700" height="300" style="background:#000000;">
  <defs>
    <filter id="appleGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#ffffff" flood-opacity="0.9" />
      <feDropShadow dx="0" dy="0" stdDeviation="6" flood-color="#ffffff" flood-opacity="0.5" />
      <feDropShadow dx="0" dy="0" stdDeviation="16" flood-color="#38bdf8" flood-opacity="0.25" />
    </filter>
  </defs>
  <g transform="translate({350 - total_w/2}, 160)">
    <path d="{full_path}" fill="none" stroke="#ffffff" stroke-width="{stroke_w}" stroke-linecap="round" stroke-linejoin="round" filter="url(#appleGlow)" />
  </g>
</svg>'''
    return svg, total_w

svg, w = generate_svg()
with open("scratch/apple_hello_authentic.svg", "w") as f:
    f.write(svg)
print("Saved apple_hello_authentic.svg, total width:", w)
