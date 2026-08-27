/** Yoak Properties — Tailwind config
 *  Tokens mirror premium_industrial_modern/DESIGN.md so the compiled CSS
 *  matches the approved design system exactly.
 */
const MONT = ['Montserrat', 'system-ui', '-apple-system', 'Segoe UI', 'Arial', 'sans-serif'];
const INTER = ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'Helvetica Neue', 'Arial', 'sans-serif'];

// Where to scan for class names. This must be resolved from the config's own
// location, not the working directory: a relative glob that misses the pages
// produces a stylesheet with no utility classes in it at all, and the site
// renders completely unstyled with no error anywhere in the build.
const path = require('path');
const ROOT = process.env.YOAK_OUT
  ? path.resolve(process.env.YOAK_OUT)
  : path.resolve(__dirname, '..');

module.exports = {
  darkMode: 'class',
  content: [
    // the seven built pages, which all sit at the site root
    path.join(ROOT, '*.html'),
    // site.js adds and removes classes at runtime, so they must be kept too
    path.join(ROOT, 'assets/js/*.js'),
  ],
  theme: {
    extend: {
      colors: {
        surface: '#fcf8fa',
        'surface-dim': '#dcd9db',
        'surface-bright': '#fcf8fa',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f6f3f5',
        'surface-container': '#f0edef',
        'surface-container-high': '#eae7e9',
        'surface-container-highest': '#e4e2e4',
        'on-surface': '#1b1b1d',
        'on-surface-variant': '#45464d',
        'inverse-surface': '#303032',
        'inverse-on-surface': '#f3f0f2',
        outline: '#76777d',
        'outline-variant': '#c6c6cd',
        'surface-tint': '#565e74',
        primary: '#000000',
        'on-primary': '#ffffff',
        'primary-container': '#131b2e',
        'on-primary-container': '#7c839b',
        'inverse-primary': '#bec6e0',
        secondary: '#735c00',
        'on-secondary': '#ffffff',
        'secondary-container': '#fed65b',
        'on-secondary-container': '#745c00',
        tertiary: '#000000',
        'on-tertiary': '#ffffff',
        'tertiary-container': '#271901',
        'on-tertiary-container': '#98805d',
        error: '#ba1a1a',
        'on-error': '#ffffff',
        'error-container': '#ffdad6',
        'on-error-container': '#93000a',
        'primary-fixed': '#dae2fd',
        'primary-fixed-dim': '#bec6e0',
        'on-primary-fixed': '#131b2e',
        'on-primary-fixed-variant': '#3f465c',
        'secondary-fixed': '#ffe088',
        'secondary-fixed-dim': '#e9c349',
        'on-secondary-fixed': '#241a00',
        'on-secondary-fixed-variant': '#574500',
        'tertiary-fixed': '#fcdeb5',
        'tertiary-fixed-dim': '#dec29a',
        'on-tertiary-fixed': '#271901',
        'on-tertiary-fixed-variant': '#574425',
        background: '#fcf8fa',
        'on-background': '#1b1b1d',
        'surface-variant': '#e4e2e4',
        'deep-navy': '#0F172A',
        'heritage-gold': '#D4AF37',
        'soft-gold': '#F9F5E8',
        'slate-gray': '#64748B',
        'surface-off-white': '#FDFDFD',
      },
      fontFamily: {
        'headline-xl': MONT,
        'headline-lg': MONT,
        'headline-lg-mobile': MONT,
        'headline-md': MONT,
        'body-lg': INTER,
        'body-md': INTER,
        'label-bold': INTER,
        caption: INTER,
        sans: INTER,
      },
      fontSize: {
        'headline-xl': ['48px', { lineHeight: '56px', letterSpacing: '-0.02em', fontWeight: '700' }],
        'headline-lg': ['32px', { lineHeight: '40px', letterSpacing: '-0.01em', fontWeight: '600' }],
        'headline-lg-mobile': ['28px', { lineHeight: '36px', fontWeight: '600' }],
        'headline-md': ['24px', { lineHeight: '32px', fontWeight: '600' }],
        'body-lg': ['18px', { lineHeight: '28px', fontWeight: '400' }],
        'body-md': ['16px', { lineHeight: '24px', fontWeight: '400' }],
        'label-bold': ['14px', { lineHeight: '20px', letterSpacing: '0.05em', fontWeight: '600' }],
        caption: ['12px', { lineHeight: '16px', fontWeight: '500' }],
      },
      borderRadius: {
        sm: '0.125rem',
        DEFAULT: '0.25rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
        full: '9999px',
      },
      spacing: {
        'margin-mobile': '16px',
        gutter: '24px',
        'section-gap-desktop': '120px',
        'section-gap-mobile': '64px',
      },
      maxWidth: {
        'container-max': '1280px',
      },
      boxShadow: {
        card: '0px 4px 20px rgba(15, 23, 42, 0.05)',
        'card-hover': '0px 12px 32px rgba(15, 23, 42, 0.12)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
};
