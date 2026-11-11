# Visual mockup guidelines

These notes cover HTML/SVG mockups and diagrams, not native Qt layouts. Keep explanatory prose outside the visual; use labels inside it.

## Diagrams

- Limit box subtitles to five words. Put details in the accompanying prose or a detail view.
- Use at most two color ramps per diagram. When colors represent states or tiers, add a one-line legend; otherwise use one neutral ramp.
- Place at most four full-width boxes in a horizontal tier, at about 140px each. For five or more, shrink boxes to at most 110px, wrap into two rows, or split overview and detail diagrams.

## Appearance and typography

- Use flat surfaces without gradients, mesh backgrounds, noise textures, blur, glow or decorative shadows. Keep functional focus rings.
- Use transparent outer containers when embedding a mockup in a host page.
- Use Noto Sans with Noto Sans CJK SC Medium for Chinese/English text. Use `--font-mono` for code.
- For mockups, use 22px h1, 18px h2 and 16px h3 headings at weight 500. Body text is 16px, weight 400, line-height 1.7. Keep text at least 11px; use weights 400 and 500 rather than 600 or 700.
- Use sentence case for headings, labels and SVG text. Reserve bold for headings and labels; put entity, class and function names in code style.
- Use Tabler outline icons rather than emoji or hand-drawn icon paths. Avoid `-filled` variants. Decorative icons need `aria-hidden="true"`; icon-only buttons need `aria-label`. Icons inherit the parent's color and font size.

## Layout and controls

- Use a block container at 100% width. For a 680px mockup, `repeat(auto-fit, minmax(160px, 1fr))` lets columns follow the available width.
- Keep content in normal flow and specify diagram heights. For a modal mockup, use a normal-flow overlay with a minimum height of 400px instead of fixed positioning.
- Put styles before content and scripts after it. Keep content visible while a mockup loads; interactive steppers can hide sections once initialized.
- Use 0.5px borders with `var(--border)` or `var(--border-strong)` for emphasis. Use `var(--radius)` (8px) for most corners and 12px for cards; larger corners may use 12px or 16px.
- Cards use `var(--surface-2)`, a 0.5px border, a 12px radius and `1rem 1.25rem` padding. Optional outer spacing is `1rem 0`.
- Text inputs are 36px high. Range sliders use a 4px track and an 18px thumb. Provide hover and focus styles for inputs and buttons.

## Theme colors

Use the CSS variables defined in `web/styles.css` for surfaces, text, borders, padding and gaps. Check every color in light and dark mode; do not assume a white card or black text will work in both.

- Surfaces: `--surface-0`, `--surface-1`, `--surface-2`.
- Text: `--text-primary`, `--text-secondary`, `--text-muted`.
- Borders: `--border`, `--border-strong`.
- Typography: `--font-sans`, `--font-mono`.
- Layout: `--radius`, `--pad-sm`, `--pad-md`, `--pad-lg`, `--gap-sm`, `--gap-md`.

SVG text needs an explicit text color or a theme-aware class. Use theme-aware classes for colored nodes where available; define the mockup's styles rather than relying on a host to supply them.
