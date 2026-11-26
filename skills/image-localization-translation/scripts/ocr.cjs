// Whole-page inventory plus optional per-box exact-copy QA. No image upload.
const fs = require('node:fs');
const path = require('node:path');
const { createWorker, PSM } = require('tesseract.js');
const sharp = require('sharp');

const [file, language, langPath, planFile] = process.argv.slice(2);
const norm = text => text.normalize('NFC').replace(/\s+/gu, ' ').trim();

async function main() {
  if (!file || !language || !langPath) throw Error('Usage: node ocr.cjs image lang local-tessdata [plan.json]');
  for (const lang of language.split('+')) {
    fs.accessSync(path.join(langPath, lang + '.traineddata.gz'));
  }
  const worker = await createWorker(language, 1, { langPath: path.resolve(langPath), cacheMethod: 'none' });
  try {
    await worker.setParameters({ tessedit_pageseg_mode: PSM.SPARSE_TEXT });
    const scan = await worker.recognize(file, {}, { blocks: true, text: true });
    const lines = (scan.data.blocks || []).flatMap(b => b.paragraphs.flatMap(p =>
      p.lines.map(l => ({ text: l.text.trim(), box: l.bbox, confidence: l.confidence }))));
    const checks = [];
    if (planFile) {
      const plan = JSON.parse(fs.readFileSync(planFile, 'utf8').replace(/^\uFEFF/, ''));
      await worker.setParameters({ tessedit_pageseg_mode: PSM.SINGLE_BLOCK });
      for (const block of plan.blocks) {
        const [left, top, right, bottom] = block.box;
        const crop = sharp(file).extract({ left, top, width: right-left, height: bottom-top });
        const { data, info } = await crop.removeAlpha().greyscale().raw().toBuffer({ resolveWithObject: true });
        // Otsu contrast separation on a tight label crop; use the majority as background.
        const counts = new Array(256).fill(0);
        let total = 0;
        for (const v of data) { counts[v]++; total += v; }
        let sum = 0, n = 0, best = -1, threshold = 0, darkBackground = false;
        for (let v = 0; v < 255; v++) {
          n += counts[v]; sum += v * counts[v];
          if (!n || n === data.length) continue;
          const dist = sum / n - (total - sum) / (data.length - n);
          const score = n * (data.length - n) * dist * dist;
          if (score > best) { best = score; threshold = v; darkBackground = n > data.length / 2; }
        }
        const pixels = data.map(v => ((v <= threshold) === darkBackground) ? 255 : 0);
        const input = await sharp(pixels, { raw: info }).resize({width: info.width*2})
          .extend({top:20, bottom:20, left:20, right:20, background:'white'}).png().toBuffer();
        const result = await worker.recognize(input);
        checks.push({ expected: block.text, actual: result.data.text.trim(), match: norm(result.data.text) === norm(block.text) });
      }
    }
    console.log(JSON.stringify({ file, language, lines, checks }, null, 2));
    if (checks.some(c => !c.match)) process.exitCode = 2;
  } finally {
    await worker.terminate();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
