---
name: pixel-character-design
description: "Design pixel art characters from reference images and render them as HTML Canvas grids and terminal ASCII block art."
version: 1.0.0
author: hermes-agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, pixel-art, character, sprite, canvas, terminal, ascii]
    category: creative
---

# Pixel Character Design

Design pixel art characters/sprites from reference images, render them as
HTML Canvas pixel grids and terminal ASCII block art.

## When to Use

- User wants a pixel art character, avatar, or mascot for a project
- User provides a reference image/character (game, anime, etc.) to recreate as pixel art
- User wants pixel art displayed in a web page (Canvas) and/or terminal banner
- User says "像素人物", "pixel character", "sprite", "像素头像", "像素形象"

## Workflow

### Step 1 — Analyze Reference

Identify the character's key visual features (3-5 defining traits):
- Silhouette / body proportions
- Iconic accessories (weapon, hat, tool)
- Color palette (2-4 dominant colors)
- Facial features (eyes, mouth expression)
- Pose (front-facing works best for small grids)

### Step 2 — Design Grid

Choose grid size based on detail needs:
- **Minimal** (8×8): iconic silhouettes only
- **Standard** (14-16 wide × 18-24 tall): recognizable characters with details
- **Detailed** (20-24 wide × 28-32 tall): expressive faces, accessories

Design process:
1. Start with the head/face — this is what makes the character recognizable
2. Add body proportions relative to head
3. Add iconic accessories (weapons, capes, etc.)
4. Assign color codes: one letter per color (P=purple, G=gold, K=black, etc.)
5. Use `.` for transparent pixels

### Step 3 — Render HTML Canvas

Pattern: single `<canvas>` element + JS grid renderer.

```html
<canvas id="pixelCanvas"></canvas>
<script>
function drawCharacter(){
  var c=document.getElementById('pixelCanvas');
  if(!c)return;
  var ctx=c.getContext('2d');
  var s=10; // pixel size in CSS px
  // Color palette
  var P='#7b4fa2',K='#2a2a2a',W='#e8e0d0',R='#b03030';
  var grid=[
    '....PPPP....',
    '...PPPPPP...',
    '..PPKPPPPK..',
    // ... rows
  ];
  var w=grid[0].length,h=grid.length;
  c.width=w*s;c.height=h*s;
  ctx.clearRect(0,0,c.width,c.height);
  var colors={P:P,K:K,W:W,R:R};
  for(var y=0;y<h;y++)for(var x=0;x<w;x++){
    var ch=grid[y][x];
    if(ch!=='.'){
      ctx.fillStyle=colors[ch]||P;
      ctx.fillRect(x*s,y*s,s,s);
    }
  }
}
drawCharacter();
</script>
```

CSS for crisp pixels:
```css
canvas{
  display:block;
  margin:0 auto;
  image-rendering:pixelated;
  filter:drop-shadow(0 0 20px rgba(179,139,45,0.3));
}
```

### Step 4 — Render Terminal Block Art

Use Unicode block characters for terminal banners:
- `█` full block (main body)
- `▐` right half block (right edge/detail)
- `▌` left half block (left edge/detail)
- `▄` lower half block (bottom edge)
- `▀` upper half block (top edge)
- `▐███▌` = bordered block (body segments)
- Spaces for gaps/transparent areas

Pattern: Python string with ANSI color placeholders.

```python
_BANNER_ART = r"""
  {g}           ▄▄▄▄▄▄▄{r}
  {d}         ▐███████████▌{r}
  {d}        ▐█████████████▌{r}
  # ... character rows
  {g}           M  U  N  D  O{r}
""".strip()

BANNER = _BANNER_ART.format(g=C.GOLD, d=C.DIM, r=C.RESET)
```

## Pitfalls

### Grid Row Width (CRITICAL)

**Every row in the grid MUST have the same character count.** A single
off-by-one breaks Canvas rendering (shifted rows) or misaligns terminal art.

Verification — always run after editing the grid:

```python
rows = ['....PPPP....', '...PPPPPP...', '..PPKPPPPK..']
widths = set(len(r) for r in rows)
assert len(widths) == 1, f"Row width mismatch: {widths}"
```

For JS, add a console assertion:
```js
var widths = grid.map(r=>r.length);
console.assert(new Set(widths).size===1, "Row width mismatch");
```

### Terminal Character Alignment

- `▐█▌` is 3 display-width characters — count carefully
- `▄` and `▀` are single-width — they align with spaces
- Test in a real terminal; some fonts render block chars at different widths
- Keep left padding consistent across all rows (use spaces, not tabs)

### Proportion Tuning

- Head should be ~30-40% of total height for recognizable characters
- Legs: 2-3 rows is enough — longer legs look weird at pixel scale
- Weapons/accessories: extend beyond body width on one side
- Leave 1 transparent column on each side of the figure for breathing room

### Color Palette

- Use 4-7 colors max for readability at small sizes
- Map each color to a single uppercase letter (A-Z)
- `.` always means transparent
- Define colors as hex in a JS object or Python dict
- Dark skin tones (#2a2a2a) for eyes/details, not pure black (#000)

### Canvas Size

- `s=10` (10px per pixel cell) is a good default
- For a 14×19 grid: canvas is 140×190px — reasonable for a header
- Larger grids (20+) may need `s=8` to fit on screen
- Always set canvas.width/height before drawing

## Reference Design: LOL Dr. Mundo

See `references/lol-mundo-pixel-art.md` for the complete grid definition
and color palette used for the MUNDO agent character (14×19 grid).
