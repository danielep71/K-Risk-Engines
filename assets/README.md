# 🎨 Website assets

[![CSS and docs](https://img.shields.io/badge/CSS_and_docs-MPL--2.0-1f3a5f?style=flat-square)](../LICENSE)
[![Artwork](https://img.shields.io/badge/Artwork-excluded_from_MPL-B60205?style=flat-square)](../NOTICE.md)

- `K-Risk-Engines-social-preview.png`: AI-generated portfolio artwork in a blue, light-blue and purple palette. Used by the website, README and social metadata. Its model illustrations are decorative, not model outputs.
- `site.css`: responsive website styles.
- `CCR_framework.svg`, `CCR_framework.png`: the counterparty credit risk framework diagram, from exposures to capital requirements, showing where K-SACCR, K-SFTs and K-CVA belong. Drawn on 2026-10-26 at the maintainer's request (#89), as one picture shared with the K-SACCR and K-SFTs repositories. The SVG is the source, shown by the website and the README; the PNG is its export with headless Chromium at a device scale factor of 2 (3200 x 3056 px), quantized to 256 colours. It is an architecture diagram, not a source or a status report: it does not certify implemented functionality, and the risk weights of its CCP table are a summary not checked against the CRR text for this picture. Change it in all three repositories together.

The artwork shows prepayment modelling as planned: that project now has its own repository at the specification stage, with no implemented model. Revisit the image when it delivers an implementation or the portfolio scope changes.

To set GitHub's repository social preview, upload the PNG under repository Settings → General → Social preview. Website Open Graph metadata is configured separately in `index.html`.

## ⚖️ Licensing

`site.css`, `CCR_framework.svg`, `CCR_framework.png` and this documentation
are covered by [MPL-2.0](../LICENSE).
`K-Risk-Engines-social-preview.png` is excluded; no separate reuse licence is
granted for the artwork. See [licensing and attribution](../NOTICE.md).

- `K-Risk-Engines-social-preview-v2.jpg`: six-project AI-generated artwork in dark navy, teal and electric blue, matching the K-SFTs visual family. Used by the README and website social metadata. Decorative illustrations, not model outputs. Excluded from MPL-2.0 on the same terms as the original artwork.
