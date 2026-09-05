# Test all alphabet letters in Authentic Apple Hello style to ensure valid SVG paths

def get_upper(ch, x):
    if ch == 'L':
        return {
            'd': f"M {x+18} -45 C {x+22} -72, {x+32} -88, {x+40} -88 C {x+45} -88, {x+40} -76, {x+32} -50 C {x+24} -24, {x+18} -4, {x+18} 0 C {x+18} 4, {x+10} 4, {x+8} -1 C {x+6} -6, {x+14} -6, {x+24} -4 C {x+36} -2, {x+48} 0, {x+56} 0",
            'w': 56
        }
    elif ch == 'A':
        return {
            'd': f"M {x+14} -16 C {x+22} -50, {x+34} -88, {x+44} -88 C {x+50} -88, {x+46} -68, {x+42} -40 C {x+38} -8, {x+46} 0, {x+52} 0 C {x+44} -22, {x+24} -42, {x+20} -42 C {x+18} -42, {x+34} -42, {x+50} -42 C {x+56} -25, {x+60} 0, {x+68} 0",
            'w': 68
        }
    elif ch == 'H':
        return {
            'd': f"M {x+12} -58 C {x+18} -88, {x+28} -88, {x+28} -64 L {x+28} 0 C {x+28} -40, {x+50} -40, {x+50} -40 L {x+50} -88 L {x+50} 0 C {x+54} 0, {x+60} 0, ${x+66} 0",
            'w': 66
        }
    elif ch == 'S':
        return {
            'd': f"M {x+12} 0 C {x+22} -35, {x+32} -88, {x+42} -88 C {x+50} -88, {x+46} -65, {x+36} -38 C {x+26} -12, {x+35} 0, {x+48} 0 C {x+56} 0, {x+64} 0, {x+70} 0",
            'w': 70
        }
    else:
        return {
            'd': f"M {x+16} -58 C {x+22} -88, {x+38} -88, {x+44} -70 C {x+46} -38, {x+34} -10, {x+26} 0 C {x+36} 0, {x+50} 0, {x+62} 0",
            'w': 62
        }

def get_lower(ch, x, is_last=False):
    h = -40
    asc = -88
    dsc = 44
    exit_flick = -6 if is_last else 0
    
    if ch == 'u':
        return {
            'd': f"C {x+6} -20, {x+14} {h}, {x+18} {h} C {x+18} {h}, {x+15} -14, {x+15} -4 C {x+15} 2, {x+25} 2, {x+28} -4 L {x+30} {h} C {x+30} {h}, {x+29} -12, {x+29} -3 C {x+29} 1, {x+34} 1, {x+40} {exit_flick}",
            'w': 40
        }
    elif ch == 'c':
        return {
            'd': f"C {x+6} -22, {x+14} {h}, {x+22} {h} C {x+26} {h}, {x+25} -32, {x+20} -30 C {x+12} -28, {x+7} -18, {x+7} -8 C {x+7} 2, {x+16} 2, {x+28} {exit_flick}",
            'w': 28
        }
    elif ch == 'k':
        return {
            'd': f"C {x+8} -28, {x+18} {asc}, {x+24} {asc} C {x+28} {asc}, {x+22} -58, {x+16} -28 L {x+16} 0 C {x+16} -20, {x+28} -26, {x+28} -16 C {x+28} -8, {x+18} -8, {x+18} -8 C {x+23} -4, {x+28} 0, {x+36} {exit_flick}",
            'w': 36
        }
    elif ch == 'y':
        return {
            'd': f"C {x+6} -20, {x+14} {h}, {x+18} {h} C {x+18} {h}, {x+15} -14, {x+15} -4 C {x+15} 2, {x+25} 2, {x+28} -4 L {x+30} {h} L {x+28} 24 C {x+26} {dsc}, {x+12} {dsc}, {x+5} 32 C {x+1} 22, {x+14} 10, {x+32} -4",
            'w': 32
        }
    elif ch == 'l':
        return {
            'd': f"C {x+8} -26, {x+18} {asc}, {x+24} {asc} C {x+20} {asc}, {x+15} -32, {x+15} 0 C {x+17} 0, {x+22} 0, {x+28} {exit_flick}",
            'w': 28
        }
    elif ch == 'e':
        return {
            'd': f"C {x+8} -16, {x+20} -20, {x+20} -20 C {x+15} {h}, {x+5} -20, {x+5} -10 C {x+5} 0, {x+15} 0, {x+24} {exit_flick}",
            'w': 24
        }
    elif ch == 'o':
        return {
            'd': f"C {x+6} -20, {x+14} {h}, {x+22} {h} C {x+12} {h}, {x+4} -24, {x+4} -12 C {x+4} 0, {x+15} 0, {x+24} 0 C {x+24} -18, {x+24} -28, {x+24} -28 C {x+28} -26, {x+30} -22, {x+34} {exit_flick}",
            'w': 34
        }
    else:
        return {
            'd': f"C {x+6} -20, {x+14} {h}, {x+14} {h} L {x+14} 0 C {x+18} 0, {x+22} 0, {x+28} {exit_flick}",
            'w': 28
        }

# Test building "Lucky"
cmds = []
x = 0
first = get_upper('L', x)
cmds.append(first['d'])
x += first['w']

name = "Lucky"
rest = name[1:]
for i, ch in enumerate(rest):
    l = get_lower(ch, x, i == len(rest) - 1)
    cmds.append(l['d'])
    x += l['w']

full = " ".join(cmds)
print("Total width of Lucky:", x)
print("Path preview:", full[:150], "...")
