import babel from '@rolldown/plugin-babel';
import react from '@vitejs/plugin-react';
import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {defineConfig} from 'vite';

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
    // make chunk imports relative
    base: './',
    // entry points
    input: {
      // public end user facing
      public: resolve(import.meta.dirname, 'src/openforms/js/public.js'),
      'public-styles': resolve(import.meta.dirname, 'src/openforms/scss/public.scss'),
      'pdf-css': resolve(import.meta.dirname, 'src/openforms/scss/pdf.scss'),
      // admin user facing
      admin_overrides: resolve(
        import.meta.dirname,
        'src/openforms/scss/admin/admin_overrides.scss'
      ),
      'core-js': resolve(import.meta.dirname, 'src/openforms/js/index.js'),
      'core-css': resolve(import.meta.dirname, 'src/openforms/scss/screen.scss'),
    },
    // TODO: replace with import.meta.env.VITE_FOO & .env configuration
    define: {
      STATIC_URL: JSON.stringify(process.env.STATIC_URL ?? '/static/'),
      'process.env.API_BASE_URL': JSON.stringify(process.env.API_BASE_URL ?? ''),
    },
    // TODO: migrate to @/ prefix like the other TS/JS projects
    resolve: {
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
  };
});
