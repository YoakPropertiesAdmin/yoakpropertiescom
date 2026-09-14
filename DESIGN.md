---
name: Premium Industrial Modern
colors:
  surface: '#fcf8fa'
  surface-dim: '#dcd9db'
  surface-bright: '#fcf8fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f5'
  surface-container: '#f0edef'
  surface-container-high: '#eae7e9'
  surface-container-highest: '#e4e2e4'
  on-surface: '#1b1b1d'
  on-surface-variant: '#45464d'
  inverse-surface: '#303032'
  inverse-on-surface: '#f3f0f2'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#735c00'
  on-secondary: '#ffffff'
  secondary-container: '#fed65b'
  on-secondary-container: '#745c00'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#ffe088'
  secondary-fixed-dim: '#e9c349'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#574500'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#fcf8fa'
  on-background: '#1b1b1d'
  surface-variant: '#e4e2e4'
  deep-navy: '#0F172A'
  heritage-gold: '#D4AF37'
  soft-gold: '#F9F5E8'
  slate-gray: '#64748B'
  surface-off-white: '#FDFDFD'
typography:
  headline-xl:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Montserrat
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-bold:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  section-gap-desktop: 120px
  section-gap-mobile: 64px
---

## Brand & Style

The design system is rooted in the "Corporate / Modern" aesthetic with a distinctive "Sleek and Trustworthy" layer. It balances the authority of a construction firm with the warmth of a family-focused rental agency. The visual narrative centers on stability and quality, utilizing high-end typography and structured whitespace to elevate the perception of affordable housing.

The brand personality is **reliable, professional, and sophisticated**. It targets families seeking security and quality without the "budget" aesthetic typically associated with affordable housing. The UI should feel like a premium concierge service: helpful, clear, and reassuringly solid.

## Colors

The palette is anchored by **Deep Navy (#0F172A)** to represent professional construction and structural integrity. **Heritage Gold (#D4AF37)** is used strategically as an accent to signify quality and the "golden standard" of service. 

- **Primary:** Deep Navy. Used for text, primary buttons, and structural elements.
- **Secondary:** Heritage Gold. Used for interactive accents, status badges, and decorative flourishes.
- **Neutral:** A range of slates and an off-white surface color to prevent the "starkness" of pure white, providing a softer, more inviting background for family users.
- **Tints:** Use **Soft Gold (#F9F5E8)** for large background containers to differentiate sections without losing the premium feel.

## Typography

This design system uses a dual-font strategy. **Montserrat** provides a geometric, architectural feel for headlines, echoing the construction side of the business. **Inter** is used for body copy and UI elements to ensure maximum legibility and a contemporary, tech-forward feel.

Large display headings use tight letter-spacing and heavy weights to command attention. Body text is set with generous line-height to ensure readability for families scanning through property details. Labels use uppercase styling with slight tracking to provide a professional, organized structure to the information hierarchy.

## Layout & Spacing

The layout utilizes a **12-column fixed grid** for desktop, ensuring content remains centered and focused. A "generous whitespace" philosophy is applied to create a premium feel; sections are separated by significant vertical gaps to allow the property imagery to breathe.

- **Desktop:** 120px vertical section spacing, 24px gutters.
- **Tablet:** 8-column grid, 80px section spacing.
- **Mobile:** 4-column grid, 16px margins, 64px section spacing.

Alignment should be primarily left-aligned for long-form content to maintain a grounded, trustworthy reading rhythm, with centered "Hero" sections for high-impact entry points.

## Elevation & Depth

The design system uses **Tonal Layers** combined with **Ambient Shadows** to create a sophisticated sense of depth. This distinguishes property listings from the base background.

- **Level 1 (Base):** Surface-off-white background.
- **Level 2 (Cards):** Pure white background with a very soft, diffused shadow (0px 4px 20px rgba(15, 23, 42, 0.05)).
- **Level 3 (Interactive):** On hover, cards lift slightly with a more pronounced shadow and a 1px Heritage Gold bottom border to indicate interactivity.
- **Navigation:** A sticky header uses a subtle 1px border-bottom in a low-contrast gray rather than a heavy shadow to maintain a sleek, modern profile.

## Shapes

The shape language is **Soft (0.25rem - 0.75rem)**. This avoids the "playfulness" of highly rounded corners while steering clear of the "sharpness" of industrial brutalism.

- **Small Components (Buttons, Inputs):** 4px (0.25rem) radius for a precise, engineered look.
- **Medium Components (Cards, Modals):** 12px (0.75rem) radius to soften the presentation of "home" and "family."
- **Image Containers:** Should always follow the 12px radius to maintain consistency with property cards.

## Components

### Buttons
- **Primary:** Deep Navy background, White text, 4px radius. High-contrast and authoritative.
- **Secondary:** Transparent background, Deep Navy text, 1px Heritage Gold border.
- **Ghost:** Heritage Gold text, no background. Used for "Learn More" links inside cards.

### Property Cards
Cards are the hero of the system. They feature a 12px radius, a Level 2 shadow, and a top-aligned image. Content should be padded by 24px. The price point should be styled in Montserrat Bold to emphasize value.

### Inputs & Forms
Form fields use a 1px slate-gray border and 4px radius. On focus, the border transitions to Heritage Gold with a soft gold outer glow.

### Chips & Badges
Used for status (e.g., "Available", "Newly Renovated"). These use a Soft Gold background with Deep Navy text to remain legible but secondary to primary actions.

### Testimonials
Quotes are housed in containers with a Soft Gold background and no border, using italicized Inter body-lg text to create a warm, human contrast to the structured property listings.