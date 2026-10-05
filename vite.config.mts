/// <reference types="vitest/config" />
import babel from '@rolldown/plugin-babel';
import react from '@vitejs/plugin-react';
import {playwright} from '@vitest/browser-playwright';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {defineConfig} from 'vite';
import {coverageConfigDefaults} from 'vitest/config';

const require = createRequire(import.meta.url);

// Emulates the vite 6 behaviour -> TODO: file an issue in NL DS components to use
// proper exports
const nodeModulesImporter = {
  findFileUrl(url: string) {
    // Let Sass handle relative/absolute/Sass-native URLs itself.
    if (
      url.startsWith('.') ||
      url.startsWith('/') ||
      url.startsWith('file:') ||
      url.startsWith('sass:')
    ) {
      return null;
    }

    try {
      const filename = require.resolve(url);

      // Don't accidentally turn JS package imports into Sass imports.
      if (!/\.(?:css|scss|sass)$/.test(filename)) {
        return null;
      }

      return pathToFileURL(filename);
    } catch {
      // Let Sass/Vite continue with their other resolution mechanisms.
      return null;
    }
  },
};

// https://vite.dev/config/
export default defineConfig(({mode}) => {
  const isDevelopment = mode === 'development';
  const jsRoot = resolve(import.meta.dirname, 'src/openforms/js');
  const scssRoot = resolve(import.meta.dirname, 'src/openforms/scss');
  return {
    plugins: [
      react(),
      // see babel.config.js (used by Webpack)
      babel({
        presets: [
          [
            '@babel/preset-react',
            {
              runtime: 'automatic',
            },
          ],
        ],
        plugins: [
          [
            'formatjs',
            {
              idInterpolationPattern: '[sha512:contenthash:base64:6]',
              ast: true,
            },
          ],
        ],
      }),
    ],
    // must match settings.STATIC_URL
    base: '/static/bundles/',
    // entry points
    input: {
      // public end user facing
      public: resolve(jsRoot, 'public.js'),
      'public-styles': resolve(scssRoot, 'public.scss'),
      'pdf-css': resolve(scssRoot, 'pdf.scss'),
      // admin user facing
      admin_overrides: resolve(scssRoot, 'admin/admin_overrides.scss'),
      'core-js': resolve(jsRoot, 'index.js'),
      'core-css': resolve(scssRoot, 'screen.scss'),
    },
    // TODO: replace with import.meta.env.VITE_FOO & .env configuration?
    define: {
      'process.env.API_BASE_URL': JSON.stringify(process.env.API_BASE_URL ?? ''),
    },
    optimizeDeps: {
      rolldownOptions: {
        moduleTypes: {
          '.js': 'jsx',
        },
      },
    },
    // TODO: migrate to @/ prefix like the other TS/JS projects
    resolve: {
      tsconfigPaths: true,
      alias: {
        'compiled-lang': resolve(jsRoot, 'compiled-lang'),
        components: resolve(jsRoot, 'components'),
        hooks: resolve(jsRoot, 'hooks'),
        utils: resolve(jsRoot, 'utils'),
        tinymce_appearance: resolve(jsRoot, 'tinymce_appearance'),
      },
    },
    css: {
      preprocessorOptions: {
        scss: {
          charset: false,
          quietDeps: true,
          api: 'modern',
          silenceDeprecations: ['import'],
          // backwards compatibility with webpack sass loader, a neater approach is using
          importers: [nodeModulesImporter],
        },
      },
    },
    build: {
      manifest: 'manifest.json',
      outDir: resolve(import.meta.dirname, 'src/openforms/static/bundles/'),
      emptyOutDir: true,
      copyPublicDir: false,
      sourcemap: true,
      minify: !isDevelopment,
      rolldownOptions: {
        experimental: {
          incrementalBuild: isDevelopment,
        },
        // django manifest static files storage post-processes everything anyway
        output: {
          entryFileNames: '[name].js',
          chunkFileNames: 'chunks/[name].js',
          assetFileNames: assetInfo => {
            if (assetInfo.names?.some(name => name.endsWith('.css'))) {
              return '[name][extname]';
            }
            return 'assets/[name][extname]';
          },
        },
      },
    },
    test: {
      environment: 'node',

      coverage: {
        provider: 'v8',
        include: ['src/openforms/js/**/*.{js,jsx,ts,tsx}'],
        exclude: [
          'src/openforms/js/**/*.d.ts',
          'src/openforms/js/**/*.stories.{ts,tsx}',
          'src/openforms/js/api-mocks/*',
          'src/openforms/js/**/mocks.ts',
          'src/openforms/js/components/admin/form_design/story-decorators.js',
          'src/openforms/js/utils/storybookTestHelpers.js',
          ...coverageConfigDefaults.exclude,
        ],
        reporter: ['text', 'cobertura', 'html'],
      },

      browser: {
        enabled: true,
        headless: true,
        provider: playwright({}),
        instances: [
          {
            browser: 'chromium',
            viewport: {
              width: 1600,
              height: 1200,
            },
          },
        ],
      },

      projects: [
        {
          extends: true,
          test: {
            name: 'unit',
            setupFiles: ['./vitest-unit.setup.ts'],
            include: ['src/openforms/js/**/*.spec.{js,ts,tsx}'],
          },
        },
      ],
    },
  };
});
