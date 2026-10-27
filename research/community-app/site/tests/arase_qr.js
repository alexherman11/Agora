// Print QR symbols from Kazuhiko Arase's encoder, for comparison with ours.
// usage: node arase_qr.js <path to qrcode-terminal/vendor/QRCode>  < jobs.json
// jobs.json is [[version, mask, text], ...]; prints a JSON list of row-string lists.
const dir = process.argv[2];
const QRCode = require(dir + '/index.js');
const Level = require(dir + '/QRErrorCorrectLevel.js');
let input = '';
process.stdin.on('data', (d) => { input += d; });
process.stdin.on('end', () => {
  const out = JSON.parse(input).map(([version, mask, text]) => {
    const qr = new QRCode(version, Level.M);
    qr.addData(text);
    qr.makeImpl(false, mask);
    const rows = [];
    for (let r = 0; r < qr.getModuleCount(); r++) {
      let line = '';
      for (let c = 0; c < qr.getModuleCount(); c++) line += qr.isDark(r, c) ? '1' : '0';
      rows.push(line);
    }
    return rows;
  });
  process.stdout.write(JSON.stringify(out));
});
