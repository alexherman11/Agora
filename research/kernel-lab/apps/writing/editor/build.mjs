// Builds doc-editor.bundle.js: one script that sets WR_CM (createEditor, diff, spans, fingerprint, ...).
// install.py puts it in front of writing-components.js for the doc-page component only. `npm install` then `npm run build`.
import {build} from 'esbuild';
await build({entryPoints: ['doc-editor.src.js'], bundle: true, format: 'iife', globalName: 'WR_CM', minify: true,
  target: 'es2022', alias: {'@codemirror/lang-html': './no-html.js'}, outfile: 'doc-editor.bundle.js', legalComments: 'none',
  banner: {js: '// Built by build.mjs from doc-editor.src.js: CodeMirror 6 (MIT, Marijn Haverbeke and others). Do not edit.'}});
console.log('built doc-editor.bundle.js');
