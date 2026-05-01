# ASESMA Poster

A 24 in by 36 in portrait poster for hanging inpublic space.

## Files

- `ASESMA_poster_24x36.svg` - editable vector source, exact size `24in x 36in`.
- `ASESMA_poster_24x36.pdf` - print-ready PDF.
- `ASESMA_poster_24x36_300dpi.png` - high-resolution PNG, `7200 x 10800` (300 dpi).
- `ASESMA_poster_24x36_preview.png` - screen preview, `2400 x 3600` (100 dpi).
- `build_poster.py` - script that regenerates the SVG from the source assets.
- `assets/`:
  - `asesma_logo.png` - simple ASESMA logo (Africa outline + colored letters).
  - `photo_tutoring.png` - real photograph extracted from the ASESMA brochure showing tutors and students at hands-on tutorials.
  - `photo_lecture.png`, `photo_group2025.png` - additional real ASESMA photographs available for re-use.
  - `qr_website.svg`, `qr_github.svg`, `qr_youtube.svg`, `qr_mini2026.svg` - real, scannable QR codes.

## Sections

1. What ASESMA is and why it matters - paragraph + Adinkra-style stats panel.
2. Upcoming events - timeline with mini-ASESMA Ghana 2026, ASESMA Dakar 2027, and year-round online activities. Year labels are placed clearly above each marker; place and subtitle are clearly below.
3. ASESMA is people - real photograph from the brochure with tutor (Garu Gebreyesus Hagoss) and student (Diana Keya) story blurbs.
4. Resources - four real, scannable QR codes for the website, GitHub, YouTube, and mini-ASESMA 2026 page, with consistent label cards.
5. Supporters - 12 supporter pills (ICTP, IUPAP, NSF, APS, CECAM, Psi-k, MARVEL, ETH4D, CNRS, U. Ghana, Witwatersrand, QE Foundation), with the closing tagline.

## Build and export

```bash
python build_poster.py
```

Generate a PNG preview at any resolution (replace `WIDTH` and `HEIGHT`):

```bash
rsvg-convert -f png -w WIDTH -h HEIGHT -o poster_preview.png ASESMA_poster_24x36.svg
```

Example:

```bash
rsvg-convert -f png -w 1600 -h 2400 -o poster_preview_1600x2400.png ASESMA_poster_24x36.svg
```

Generate a print-ready PDF:

```bash
rsvg-convert -f pdf -o ASESMA_poster_24x36.pdf ASESMA_poster_24x36.svg
```
