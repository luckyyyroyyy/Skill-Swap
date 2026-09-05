import os

# Let's create multiple candidate styles for "Lucky" without the bottom loop flourish!

# 1. Authentic Apple Hello (Susan Kare / 2021 iMac modernized monoline cursive)
# Clean, rounded, elegant, no backward underline, clean tail finish.

def get_apple_authentic(name="Lucky"):
    # Authentic Apple Hello capital L:
    # Gentle top oval, natural downstroke, small crisp base knot, smooth baseline lead-in
    # u: smooth valley
    # c: rounded oval
    # k: clean ascender loop, mid loop, kick
    # y: u-valley, descender loop, upward exit flick
    
    # L
    L = "M 22 -40 C 26 -72, 38 -92, 46 -92 C 51 -92, 44 -78, 36 -52 C 28 -26, 22 -6, 22 0 C 22 5, 12 5, 10 -1 C 8 -8, 18 -8, 30 -6 C 44 -4, 56 -2, 68 0"
    w_L = 68
    
    # u
    u = f"C {w_L+8} -24, {w_L+14} -44, {w_L+18} -44 C {w_L+18} -44, {w_L+16} -18, {w_L+16} -6 C {w_L+16} 2, {w_L+28} 2, {w_L+32} -6 L {w_L+34} -44 C {w_L+34} -44, {w_L+33} -14, {w_L+33} -4 C {w_L+33} 1, {w_L+38} 1, {w_L+44} 0"
    w_u = 44
    x = w_L + w_u
    
    # c
    c = f"C {x+6} -24, {x+14} -44, {x+24} -44 C {x+28} -44, {x+28} -36, {x+22} -34 C {x+14} -32, {x+8} -20, {x+8} -10 C {x+8} 2, {x+18} 2, {x+32} 0"
    w_c = 32
    x += w_c
    
    # k (tall loop ascender, middle knot, kick)
    k = f"C {x+10} -28, {x+20} -94, {x+28} -94 C {x+31} -94, {x+24} -65, {x+18} -32 L {x+18} 0 C {x+18} -22, {x+32} -30, {x+32} -20 C {x+32} -10, {x+20} -10, {x+20} -10 C {x+26} -6, {x+34} 0, {x+44} 0"
    w_k = 44
    x += w_k
    
    # y (smooth valley, descender loop, gentle upward finish - NO UNDERLINE)
    y = f"C {x+7} -24, {x+14} -44, {x+18} -44 C {x+18} -44, {x+15} -18, {x+15} -6 C {x+15} 2, {x+28} 2, {x+32} -6 L {x+34} -44 L {x+32} 24 C {x+30} 46, {x+14} 46, {x+6} 34 C {x+1} 22, {x+16} 8, {x+36} -8"
    w_y = 36
    x += w_y
    
    path = f"{L} {u} {c} {k} {y}"
    return path, x

path, width = get_apple_authentic("Lucky")

svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 350" width="800" height="350" style="background:#000;">
  <g transform="translate({400 - width/2}, 180)">
    <!-- Glow -->
    <path d="{path}" fill="none" stroke="#ffffff" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"
          filter="drop-shadow(0 0 3px #ffffff) drop-shadow(0 0 10px rgba(255,255,255,0.7)) drop-shadow(0 0 24px rgba(56,189,248,0.4))" />
  </g>
</svg>'''

with open("scratch/preview_apple_clean.svg", "w") as f:
    f.write(svg_content)
print("Saved preview_apple_clean.svg, width:", width)
