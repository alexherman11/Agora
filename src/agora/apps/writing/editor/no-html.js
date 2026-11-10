// Stands in for @codemirror/lang-html: HTML inside a document is kept as plain text, so the bundle needs no HTML, CSS
// or JavaScript language (they were 60% of it). lang-markdown reads .support and .language.parser from what html() gives.
export function html() { return {support: [], language: {parser: undefined}} }
export function htmlCompletionSource() { return null }
