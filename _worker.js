// XDFclier EdgeOne Edge Function
// Handles: /api/slice, /api/health
// Static files are served by EdgeOne Pages CDN

// ============================================================
// DOCX Parser (pure JS, no dependencies)
// ============================================================

function parseZip(buf) {
  const dv = new DataView(buf);
  let pos = 0;
  const files = {};
  while (pos < buf.byteLength - 30) {
    if (dv.getUint32(pos, true) !== 0x04034b50) { pos++; continue; }
    const version = dv.getUint16(pos + 4, true);
    const flags = dv.getUint16(pos + 6, true);
    const method = dv.getUint16(pos + 8, true);
    const nameLen = dv.getUint16(pos + 26, true);
    const extraLen = dv.getUint16(pos + 28, true);
    const name = new TextDecoder().decode(new Uint8Array(buf, pos + 30, nameLen));
    const dataStart = pos + 30 + nameLen + extraLen;
    const compSize = dv.getUint32(pos + 18, true);
    const uncompSize = dv.getUint32(pos + 22, true);
    let data;
    if (method === 0) {
      data = new Uint8Array(buf, dataStart, compSize);
    } else if (method === 8) {
      data = inflateRaw(new Uint8Array(buf, dataStart, compSize), uncompSize);
    } else {
      data = new Uint8Array(0);
    }
    files[name] = data;
    pos = dataStart + compSize;
  }
  return files;
}

function inflateRaw(input, outputSize) {
  // Minimal inflate implementation for raw deflate
  const output = new Uint8Array(outputSize || input.length * 3);
  let ip = 0, op = 0;
  // Bit buffer
  let bits = 0, nbits = 0, eof = false;
  function readBits(n) {
    while (nbits < n) {
      if (ip >= input.length) { eof = true; return 0; }
      bits |= input[ip++] << nbits;
      nbits += 8;
    }
    const v = bits & ((1 << n) - 1);
    bits >>>= n;
    nbits -= n;
    return v;
  }
  function readHuff(tree) {
    let node = tree;
    while (node[0] !== undefined) {
      const bit = readBits(1);
      node = node[bit];
    }
    return node;
  }
  // Fixed Huffman trees
  function buildFixedTree() {
    const len = [];
    for (let i = 0; i <= 143; i++) len[i] = 8;
    for (let i = 144; i <= 255; i++) len[i] = 9;
    for (let i = 256; i <= 279; i++) len[i] = 7;
    for (let i = 280; i <= 287; i++) len[i] = 8;
    return buildTree(len);
  }
  function buildTree(lengths) {
    const maxLen = Math.max(...lengths.filter(x => x > 0));
    const blCount = new Array(maxLen + 1).fill(0);
    for (const l of lengths) if (l > 0) blCount[l]++;
    const nextCode = new Array(maxLen + 1).fill(0);
    let code = 0;
    for (let i = 1; i <= maxLen; i++) {
      code = (code + blCount[i - 1]) << 1;
      nextCode[i] = code;
    }
    const tree = {};
    for (let i = 0; i < lengths.length; i++) {
      const len = lengths[i];
      if (len === 0) continue;
      let node = tree;
      for (let b = len - 1; b >= 0; b--) {
        const bit = (nextCode[len] >> b) & 1;
        if (!node[bit]) node[bit] = {};
        node = node[bit];
      }
      node[i] = true;
      nextCode[len]++;
    }
    return tree;
  }
  const baseLength = [3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258];
  const extraLength = [0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0];
  const baseDist = [1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577];
  const extraDist = [0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13];
  const fixedTree = buildFixedTree();
  const fixedDist = buildTree(new Array(32).fill(5));
  const lenTreeTbl = [16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
  while (!eof) {
    const bfinal = readBits(1);
    const btype = readBits(2);
    if (btype === 0) {
      // No compression
      nbits = 0; bits = 0;
      const len = readBits(16);
      const nlen = readBits(16);
      for (let i = 0; i < len && ip < input.length; i++) output[op++] = input[ip++];
      if (bfinal) break;
      continue;
    }
    if (btype === 3) break;
    const litTree = btype === 1 ? fixedTree : readDynamicTree();
    const distTree = btype === 1 ? fixedDist : readDynamicTree2();
    while (true) {
      const sym = readHuff(litTree);
      if (sym === 256) break;
      if (sym < 256) {
        if (op >= output.length) break;
        output[op++] = sym;
      } else {
        const lenIdx = sym - 257;
        const len = baseLength[lenIdx] + readBits(extraLength[lenIdx]);
        const distIdx = readHuff(distTree);
        const dist = baseDist[distIdx] + readBits(extraDist[distIdx]);
        for (let i = 0; i < len; i++) {
          if (op >= output.length) break;
          output[op] = output[op - dist];
          op++;
        }
      }
    }
    if (bfinal) break;
  }
  return output.slice(0, op);
  function readDynamicTree() {
    const hl = readBits(5) + 257;
    const hd = readBits(5) + 1;
    const hc = readBits(4) + 4;
    const codeLen = new Array(19).fill(0);
    for (let i = 0; i < hc; i++) codeLen[lenTreeTbl[i]] = readBits(3);
    const codeTree = buildTree(codeLen);
    const allLens = [];
    while (allLens.length < hl + hd) {
      const sym = readHuff(codeTree);
      if (sym < 16) allLens.push(sym);
      else if (sym === 16) { const rep = readBits(2) + 3; for (let j = 0; j < rep; j++) allLens.push(allLens[allLens.length - 1]); }
      else if (sym === 17) { const rep = readBits(3) + 3; for (let j = 0; j < rep; j++) allLens.push(0); }
      else if (sym === 18) { const rep = readBits(7) + 11; for (let j = 0; j < rep; j++) allLens.push(0); }
    }
    return buildTree(allLens.slice(0, hl));
  }
  function readDynamicTree2() {
    // Same as readDynamicTree but uses the dist part
    const hl = readBits(5) + 257;
    const hd = readBits(5) + 1;
    const hc = readBits(4) + 4;
    const codeLen = new Array(19).fill(0);
    for (let i = 0; i < hc; i++) codeLen[lenTreeTbl[i]] = readBits(3);
    const codeTree = buildTree(codeLen);
    const allLens = [];
    while (allLens.length < hl + hd) {
      const sym = readHuff(codeTree);
      if (sym < 16) allLens.push(sym);
      else if (sym === 16) { const rep = readBits(2) + 3; for (let j = 0; j < rep; j++) allLens.push(allLens[allLens.length - 1]); }
      else if (sym === 17) { const rep = readBits(3) + 3; for (let j = 0; j < rep; j++) allLens.push(0); }
      else if (sym === 18) { const rep = readBits(7) + 11; for (let j = 0; j < rep; j++) allLens.push(0); }
    }
    return buildTree(allLens.slice(hl, hl + hd));
  }
}

function parseDocx(buf) {
  const files = parseZip(buf);
  const xml = new TextDecoder().decode(files['word/document.xml']);
  const paragraphs = [];
  const pRegex = /<w:p[ >][\s\S]*?<\/w:p>/g;
  let match;
  while ((match = pRegex.exec(xml)) !== null) {
    const pXml = match[0];
    const textRegex = /<w:t[^>]*>([\s\S]*?)<\/w:t>/g;
    let text = '', tMatch;
    while ((tMatch = textRegex.exec(pXml)) !== null) {
      text += tMatch[1];
    }
    paragraphs.push(text);
  }
  return paragraphs;
}

function makeDocx(paragraphs, typeName, gradeInfo) {
  // Build XML body
  let bodyXml = '';
  for (const p of paragraphs) {
    bodyXml += `<w:p><w:r><w:rPr><w:rFonts w:eastAsia="SimSun"/><w:sz w:val="21"/></w:rPr><w:t xml:space="preserve">${escapeXml(p)}</w:t></w:r></w:p>`;
  }
  const docXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>${bodyXml}</w:body></w:document>`;

  const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>`;

  const rels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>`;

  const wRels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>`;

  const stylesXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:spacing w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:eastAsia="SimSun"/><w:sz w:val="21"/></w:rPr></w:style>
<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="DefaultParagraph Font"/></w:style>
</w:styles>`;

  return makeZip({
    '[Content_Types].xml': strToU8(contentTypes),
    '_rels/.rels': strToU8(rels),
    'word/document.xml': strToU8(docXml),
    'word/_rels/document.xml.rels': strToU8(wRels),
    'word/styles.xml': strToU8(stylesXml),
  });
}

function makeZip(files) {
  // Build a minimal ZIP file
  const encoder = new TextEncoder();
  const fileEntries = Object.entries(files);
  let offset = 0;
  const localHeaders = [];
  const centralEntries = [];
  
  for (const [name, data] of fileEntries) {
    const nameBytes = encoder.encode(name);
    const crc = crc32(data);
    const headerSize = 30 + nameBytes.length;
    
    // Local file header
    const header = new Uint8Array(headerSize);
    const dv = new DataView(header.buffer);
    dv.setUint32(0, 0x04034b50, true); // signature
    dv.setUint16(4, 20, true); // version needed
    dv.setUint16(6, 0, true); // flags
    dv.setUint16(8, 0, true); // compression (store)
    dv.setUint16(10, 0, true); // mod time
    dv.setUint16(12, 0, true); // mod date
    dv.setUint32(14, crc, true); // crc32
    dv.setUint32(18, data.byteLength, true); // compressed size
    dv.setUint32(22, data.byteLength, true); // uncompressed size
    dv.setUint16(26, nameBytes.length, true); // filename length
    dv.setUint16(28, 0, true); // extra field length
    header.set(nameBytes, 30);
    
    localHeaders.push({ header, data, offset: offset });
    
    // Central directory entry
    const centralSize = 46 + nameBytes.length;
    const central = new Uint8Array(centralSize);
    const cdv = new DataView(central.buffer);
    cdv.setUint32(0, 0x02014b50, true); // signature
    cdv.setUint16(4, 20, true); // version made by
    cdv.setUint16(6, 20, true); // version needed
    cdv.setUint16(8, 0, true); // flags
    cdv.setUint16(10, 0, true); // compression
    cdv.setUint16(12, 0, true); // mod time
    cdv.setUint16(14, 0, true); // mod date
    cdv.setUint32(16, crc, true);
    cdv.setUint32(20, data.byteLength, true);
    cdv.setUint32(24, data.byteLength, true);
    cdv.setUint16(28, nameBytes.length, true);
    cdv.setUint16(30, 0, true); // extra field length
    cdv.setUint16(32, 0, true); // file comment length
    cdv.setUint16(34, 0, true); // disk number start
    cdv.setUint16(36, 0, true); // internal attrs
    cdv.setUint32(38, 0, true); // external attrs
    cdv.setUint32(42, offset, true); // local header offset
    central.set(nameBytes, 46);
    centralEntries.push(central);
    
    offset += headerSize + data.byteLength;
  }
  
  // Build final ZIP
  const centralOffset = offset;
  const centralSize = centralEntries.reduce((s, e) => s + e.byteLength, 0);
  const eocdSize = 22;
  const totalSize = centralOffset + centralSize + eocdSize;
  const zip = new Uint8Array(totalSize);
  let pos = 0;
  
  for (const lh of localHeaders) {
    zip.set(lh.header, pos); pos += lh.header.byteLength;
    zip.set(new Uint8Array(lh.data), pos); pos += lh.data.byteLength;
  }
  
  const cdOffset = pos;
  for (const ce of centralEntries) {
    zip.set(ce, pos); pos += ce.byteLength;
  }
  
  // EOCD
  const eocd = new Uint8Array(22);
  const edv = new DataView(eocd.buffer);
  edv.setUint32(0, 0x06054b50, true);
  edv.setUint16(4, 0, true); // disk number
  edv.setUint16(6, 0, true); // disk with central
  edv.setUint16(8, fileEntries.length, true); // entries on disk
  edv.setUint16(10, fileEntries.length, true); // total entries
  edv.setUint32(12, centralSize, true); // central directory size
  edv.setUint32(16, cdOffset, true); // central directory offset
  edv.setUint16(20, 0, true); // comment length
  zip.set(eocd, pos);
  
  return zip;
}

function strToU8(s) {
  return new TextEncoder().encode(s);
}

function escapeXml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// CRC32
const crcTable = new Uint32Array(256);
for (let i = 0; i < 256; i++) {
  let c = i;
  for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
  crcTable[i] = c;
}
function crc32(data) {
  let c = 0xFFFFFFFF;
  for (let i = 0; i < data.length; i++) c = crcTable[(c ^ data[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0;
}

// ============================================================
// Classifier (ported from formatters/classify.py)
// ============================================================

const SchoolKeywords = ['厦门一中','厦门二中','厦门三中','厦门六中','厦门外国语学校','厦门外国语','厦门大学附属科技中学','科技中学','厦门实验中学','厦门实验','厦门市双十中学','双十中学','双十','翔安第一中学','翔安一中','海沧实验中学','厦门湖滨中学','湖滨中学','同安一中','福州一中','福州三中','师大附中'];

function classifyGlobal(text) {
  if (!text.trim()) return 'empty';
  if (/^【/.test(text) && /】/.test(text) && /[厦门考试月考期中期末]/.test(text)) return 'source_label';
  if (/^[一二三四五六七八九十百]+[、.．]/.test(text)) return 'skip_header';
  const m = text.match(/^[（(][一二三四五六七八九十百]+[）)]/);
  if (m) {
    if (/[阅读默写诗歌文言古诗作文语言文字名句写作]/.test(text)) return 'skip';
    return 'other';
  }
  if (text.startsWith('【答案】')) return 'answer_marker';
  if (text.startsWith('【注】') || text.startsWith('【注释】') || text.startsWith('[注]')) return 'annotation';
  if (/^【[\u4e00-\u9fff]{2,}】/.test(text)) return 'explanation_marker';
  if (text.startsWith('阅读下面')) return 'instruction';
  const qm = text.match(/^(\d+[．.、])/);
  if (qm) {
    const after = text.slice(qm[0].length).trim();
    if (after.startsWith('阅读')) return 'instruction';
  }
  if (/本题考查/.test(text) || text.startsWith('【分析】')) return 'explanation_auto';
  if (/^故选[A-D]/.test(text) || text.startsWith('故选：')) return 'explanation_auto';
  if (/^\d+[．.、]\s*本题考查/.test(text)) return 'explanation_auto';
  if (text.startsWith('句意：') || text.startsWith('①句意') || text.startsWith('②句意')) return 'explanation_auto';
  if (/^(全文翻译|参考译文|译文|全文译文)/.test(text)) return 'explanation_auto';
  if (/^\d+[．.、]/.test(text)) return 'question';
  if (/^[（(]\d+[）)]/.test(text) && !/[月考期中期末考试]/.test(text)) return 'question';
  if (/^[①②③④⑤⑥⑦⑧⑨⑩]/.test(text)) return 'question_sub';
  if (/^[A-D][．.、)]/.test(text)) return 'option';
  return null;
}

function classifyGushici(text) {
  if (text.includes('阅读下面')) return 'instruction';
  if (/下列句子中，句式与其他三项不同的一项是|下列加点字词的解释|下列加点虚词的意义及用法|下列有关文学常识的表述|补写出下列句子中的空缺部分|课内古诗文阅读/.test(text)) return 'skip_content';
  const clean = text.replace(/[\s，。！？、；：\u201c\u201d\u2018\u2019《》（）]/g, '').trim();
  if (/^[\u4e00-\u9fff·\s]{2,10}$/.test(text.trim())) {
    if (/^[\u4e00-\u9fff]{2,3}$/.test(text.trim()) && knownPoets.includes(text.trim())) return 'poem_author';
    return 'poem_title';
  }
  if (clean.length >= 4 && clean.length <= 28 && clean.length >= text.trim().length * 0.5) return 'poem_text';
  if (text.includes('，') && text.trim().length <= 40) {
    const parts = text.trim().split('，');
    if (parts.every(p => p.length >= 3 && p.length <= 10)) return 'poem_text';
  }
  return 'other';
}

const knownPoets = ['李白','杜甫','白居易','杜牧','王维','孟浩然','李商隐','王昌龄','刘禹锡','杜荀鹤','苏轼','李清照','辛弃疾','陆游','王安石','欧阳修','陶渊明','曹操','王阳明','黄庭坚','杨万里','范成大','晏殊','柳永','温庭筠','韦庄','李贺','贾岛','孟郊','张若虚','高适','岑参','王之涣','王勃','骆宾王','杨炯','卢照邻','陈子昂','贺知章','张九龄','王湾','常建','刘长卿','韦应物','柳宗元','元稹','张籍','李益','卢纶','李煜','范仲淹','秦观','周邦彦','姜夔','马致远','关汉卿','王实甫','纳兰性德','龚自珍','曹植','屈原','项羽','刘邦','岳飞','文天祥','于谦','郑燮','袁枚','赵翼'];

function classifyNonpoem(text) {
  if (text.length > 30 && !(/^[（(]?(摘编自|选自|节选自|摘自|有删改|有删节)/.test(text) || text.includes('有删改') || text.includes('有删节'))) return 'modern_text';
  if (/^材料/.test(text) || /^文本/.test(text)) return 'modern_text';
  return 'other';
}

function classifyText(text, typeName) {
  const g = classifyGlobal(text);
  if (g !== null) return g;
  if (typeName === '古诗词阅读') return classifyGushici(text);
  if (['论述类文本', '文学类文本', '文言文阅读'].includes(typeName)) return classifyNonpoem(text);
  return 'other';
}

const ZoneMap = {
  'empty': 'skip', 'skip': 'skip', 'skip_header': 'skip', 'skip_content': 'skip',
  'other': 'reading', 'source_label': 'reading', 'annotation': 'reading',
  'modern_text': 'reading', 'instruction': 'reading',
  'answer_marker': 'answer', 'explanation_marker': 'explanation', 'explanation_auto': 'explanation',
  'question': 'question', 'question_sub': 'question', 'option': 'question',
  'poem_text': 'reading', 'poem_title': 'reading', 'poem_author': 'reading'
};

const TYPE_NAMES = ['论述类文本', '文学类文本', '文言文阅读', '古诗词阅读'];

function detectTypes(texts) {
  const types = {};
  const l1Pat = /^[一二三四五六七八九十百]+[、.．]/;
  const l2Pat = /^[（(][一二三四五六七八九十百]+[）)]/;
  const typeKeywords = {
    '论述类文本': ['阅读Ⅰ','阅读I','阅读1','现代文阅读Ⅰ','现代文阅读I','现代文阅读1','论述类','论述类文本','信息类','信息类文本','信息类文本阅读','信息类阅读','论述文','实用类文本','非连续性文本','阅读下面的文字，完成下面小题'],
    '文学类文本': ['阅读Ⅱ','阅读II','阅读2','现代文阅读Ⅱ','现代文阅读II','现代文阅读2','文学类','文学'],
    '文言文阅读': ['文言文阅读','文言文','文言知识','课外文言文','课外文言文阅读','阅读Ⅲ','阅读III','古代诗文阅读Ⅰ'],
    '古诗词阅读': ['古代诗歌阅读','古代诗歌鉴赏','古诗阅读','诗歌阅读','诗歌鉴赏','古诗词','阅读Ⅳ','阅读IV','古代诗文阅读Ⅱ']
  };
  const nonTarget = ['名篇名句默写','名句默写','古诗文默写','语言文字运用','语用','作文','写作','基础知识','古代诗文阅读Ⅲ'];
  
  const l1Headers = [];
  const l2Headers = [];
  for (let i = 0; i < texts.length; i++) {
    const t = texts[i].trim();
    if (!t) continue;
    if (l1Pat.test(t)) l1Headers.push(i);
    else if (l2Pat.test(t)) l2Headers.push(i);
  }
  
  function classifyText(text) {
    for (const [type, keywords] of Object.entries(typeKeywords)) {
      for (const kw of keywords) {
        if (text.includes(kw)) return type;
      }
    }
    return null;
  }
  
  for (const i of l2Headers) {
    const t = texts[i];
    if (nonTarget.some(k => t.includes(k))) continue;
    const type = classifyText(t);
    if (type) {
      const end = findNext(i + 1);
      types[type] = { start: i, end: end - 1 };
    }
  }
  
  if (Object.keys(types).length === 0) {
    for (const i of l1Headers) {
      const t = texts[i];
      if (nonTarget.some(k => t.includes(k))) continue;
      const type = classifyText(t);
      if (type) {
        const end = findNext(i + 1);
        types[type] = { start: i, end: end - 1 };
      }
    }
  }
  
  function findNext(from) {
    const all = [...l1Headers, ...l2Headers].filter(x => x >= from).sort((a, b) => a - b);
    return all.length > 0 ? all[0] : texts.length;
  }
  
  return types;
}

// ============================================================
// Edge Function Handler
// ============================================================

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  // GET /api/health
  if (path === '/api/health' && request.method === 'GET') {
    return new Response(JSON.stringify({ status: 'ok', version: 'edgeone' }), {
      headers: { 'content-type': 'application/json' }
    });
  }

  // POST /api/slice
  if (path === '/api/slice' && request.method === 'POST') {
    try {
      return await handleSlice(request);
    } catch (err) {
      return new Response(JSON.stringify({ detail: err.message }), {
        status: 500, headers: { 'content-type': 'application/json' }
      });
    }
  }

  // Not found
  return new Response('Not Found', { status: 404 });
}

async function handleSlice(request) {
  const formData = await request.formData();
  const files = formData.getAll('files');
  const gradeInfo = formData.get('grade_info') || 'exam';
  
  if (!files || files.length === 0) {
    throw new Error('No files uploaded');
  }

  // Process each file
  const typeCollections = {};
  for (const type of TYPE_NAMES) typeCollections[type] = [];

  for (const file of files) {
    if (!file.name.toLowerCase().endsWith('.docx')) continue;
    
    const buf = await file.arrayBuffer();
    const paragraphs = parseDocx(buf);
    
    // Detect types
    const ranges = detectTypes(paragraphs);
    
    if (!ranges || Object.keys(ranges).length === 0) {
      throw new Error(`Could not detect any question types in ${file.name}`);
    }
    
    // Process each type range
    for (const [type, range] of Object.entries(ranges)) {
      const content = paragraphs.slice(range.start, range.end + 1);
      // Classify each paragraph into zones
      const zones = findZones(content, type);
      typeCollections[type].push({
        school: detectSchool(file.name),
        exam: '', content: content.map(t => [t, false, 0, null, null]), zones
      });
    }
  }

  // Generate output DOCX files
  const outputFiles = {};
  for (const type of TYPE_NAMES) {
    const items = typeCollections[type];
    if (items.length === 0) continue;
    
    // Collect all paragraphs for this type
    const allContent = [];
    for (const item of items) {
      for (const zone of item.zones) {
        const [zoneName, start, end] = zone;
        if (zoneName === 'skip') continue;
        for (let i = start; i <= end && i < item.content.length; i++) {
          allContent.push(item.content[i][0]);
        }
      }
    }
    
    if (allContent.length === 0) continue;
    
    const docxBytes = makeDocx(allContent, type, gradeInfo);
    const fileName = `${gradeInfo}${type.replace(/[\[\]]/g, '')}切片.docx`;
    outputFiles[fileName] = docxBytes;
  }

  if (Object.keys(outputFiles).length === 0) {
    throw new Error('No output generated');
  }

  // Create output ZIP
  const zipFiles = {};
  for (const [name, data] of Object.entries(outputFiles)) {
    zipFiles[name] = data;
  }
  const zipBytes = makeZip(zipFiles);

  return new Response(zipBytes, {
    headers: {
      'content-type': 'application/zip',
      'content-disposition': `attachment; filename=slice_result.zip`
    }
  });
}

function detectSchool(filename) {
  for (const kw of SchoolKeywords) {
    if (filename.includes(kw)) return kw;
  }
  return null;
}

function findZones(texts, typeName) {
  const zones = [];
  let current = 'reading';
  let zStart = 0;
  
  for (let i = 0; i < texts.length; i++) {
    const t = texts[i];
    if (!t.trim()) continue;
    const cls = classifyText(t, typeName);
    const zone = ZoneMap[cls] || 'reading';
    
    if (zone !== current) {
      zones.push([current, zStart, i - 1]);
      current = zone;
      zStart = i;
    }
  }
  zones.push([current, zStart, texts.length - 1]);
  
  // Merge adjacent same zones
  const merged = [zones[0]];
  for (let i = 1; i < zones.length; i++) {
    const last = merged[merged.length - 1];
    if (zones[i][0] === last[0] && zones[i][1] === last[2] + 1) {
      last[2] = zones[i][2];
    } else {
      merged.push(zones[i]);
    }
  }
  
  return merged;
}

// ============================================================
// Entry Point
// ============================================================

export default {
  async fetch(request) {
    const url = new URL(request.url);
    // API routes go to our handler
    if (url.pathname.startsWith('/api/')) {
      return handleRequest(request);
    }
    // Everything else serves static files (handled by EdgeOne Pages)
    return fetch(request);
  }
};
