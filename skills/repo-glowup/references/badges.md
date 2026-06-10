# Badge chips (shields.io)

All use `style=for-the-badge` (the chunky "chip" look). Substitute `OWNER/REPO`, the
workflow filename, and package name. Wrap status/license/registry badges in links.

## Status & meta (any repo)

```md
[![Build](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/WORKFLOW.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=build)](https://github.com/OWNER/REPO/actions/workflows/WORKFLOW.yml)
[![License](https://img.shields.io/github/license/OWNER/REPO?style=for-the-badge)](LICENSE)
![Release](https://img.shields.io/github/v/release/OWNER/REPO?style=for-the-badge)
![Last commit](https://img.shields.io/github/last-commit/OWNER/REPO?style=for-the-badge)
```

## Registry / version (pick the one that matches)

```md
npm     ![npm](https://img.shields.io/npm/v/PKG?style=for-the-badge&logo=npm&logoColor=white)
PyPI    ![PyPI](https://img.shields.io/pypi/v/PKG?style=for-the-badge&logo=pypi&logoColor=white)
crates  ![crates.io](https://img.shields.io/crates/v/PKG?style=for-the-badge&logo=rust&logoColor=white)
Go      [![Go ref](https://img.shields.io/badge/pkg.go.dev-reference-007D9C?style=for-the-badge&logo=go&logoColor=white)](https://pkg.go.dev/MODULE)
GHCR    [![Image](https://img.shields.io/badge/ghcr.io-REPO-2496ED?style=for-the-badge&logo=podman&logoColor=white)](https://github.com/users/OWNER/packages/container/package/REPO)
Docker  ![Docker](https://img.shields.io/docker/v/OWNER/REPO?style=for-the-badge&logo=docker&logoColor=white)
```

## Tech chips (static; pick 4–6)

Pattern: `https://img.shields.io/badge/LABEL-HEX?style=for-the-badge&logo=SLUG&logoColor=white`

| Tech | hex | simple-icons slug | note |
|---|---|---|---|
| TypeScript | 3178C6 | typescript | |
| JavaScript | F7DF1E | javascript | `logoColor=black` |
| Node.js | 5FA04E | nodedotjs | |
| Python | 3776AB | python | |
| Rust | 000000 | rust | |
| Go | 00ADD8 | go | |
| React | 61DAFB | react | `logoColor=black` |
| Next.js | 000000 | nextdotjs | |
| Svelte | FF3E00 | svelte | |
| PostgreSQL | 4169E1 | postgresql | |
| Redis | FF4438 | redis | |
| Docker | 2496ED | docker | |
| Podman | 892CA0 | podman | |
| Kubernetes | 326CE5 | kubernetes | |
| Fedora | 51A2DA | fedora | |
| KDE | 1D99F3 | kde | |
| NVIDIA | 76B900 | nvidia | |
| QEMU | FF6600 | qemu | |
| Linux | 0A0A0A | linux | |
| cosign / Sigstore | FBC02D | sigstore | `logoColor=black` |

Notes:
- Yellow/cyan logos read better with `logoColor=black`.
- Verify a slug exists at simpleicons.org before using it; an unknown slug silently
  drops the logo.
- Keep the palette disciplined — brand colors for the chips, not a rainbow.
