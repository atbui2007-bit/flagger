# Self-hosted fonts

These are served directly from `site/` so the landing page makes **zero third-party
requests**. Previously the page loaded a render-blocking stylesheet from
`fonts.googleapis.com`, which gated first paint — and therefore LCP, since the hero
`<h1>` is the LCP element — on a cross-origin round trip.

Both files are the **`latin` subset only**. The page's copy is English plus a single
em dash, so the larger subsets are dead weight.

| File | Family | Weights | Size |
|---|---|---|---|
| `inter-latin-var.woff2` | Inter | variable, 100–900 | 48 KB |
| `playfair-display-400-latin.woff2` | Playfair Display | 400 | 22 KB |

Inter is the variable font, so one file covers the 400/500/600 the page uses.

## Licensing

Both are SIL Open Font License 1.1. The OFL requires the license to travel with the
font binaries when they are redistributed, which is what self-hosting is — see
`OFL-Inter.txt` and `OFL-PlayfairDisplay.txt`.

## Regenerating

The `unicode-range` in each `@font-face` block in `index.html` and `og.html` is copied
verbatim from the Google Fonts CSS response and must match the subset actually
embedded in the file. To refresh, request the CSS with a modern browser User-Agent
(the API serves woff2 only to UAs that support it), take the URL from the
`/* latin */` block, and download it:

```bash
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
curl -A "$UA" "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400&family=Inter:wght@400;500;600&display=swap"
```

Note: U+2197 (the `↗` in the brand mark) is **not** in this subset and falls back to a
system font. That was true with the hosted Google Fonts too, so it is existing
behavior, not a regression introduced by self-hosting.
