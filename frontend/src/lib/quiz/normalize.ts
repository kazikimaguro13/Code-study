// TS port of backend/src/grading/normalize.py — deterministic text normalization.

const KATAKANA_START = 0x30a1;
const KATAKANA_END = 0x30f6;
const HIRAGANA_START = 0x3041;

function katakanaToHiragana(text: string): string {
  return Array.from(text)
    .map((ch) => {
      const cp = ch.codePointAt(0) ?? 0;
      return cp >= KATAKANA_START && cp <= KATAKANA_END
        ? String.fromCodePoint(cp - KATAKANA_START + HIRAGANA_START)
        : ch;
    })
    .join("");
}

export function normalizeText(text: string): string {
  if (!text) return "";
  let s = text.normalize("NFKC");
  s = katakanaToHiragana(s);
  s = s.toLowerCase();
  s = s.replace(/\s+/g, " ").trim();
  return s;
}

export function normalizePath(path: string): string {
  if (!path) return "";
  let s = path.trim().replace(/\\/g, "/");
  s = s.replace(/^\.\//, "");
  s = s.replace(/\/+/g, "/");
  return s.toLowerCase();
}

const SYMBOL_STRIP_RE = /[() \t]/g;

export function normalizeSymbol(symbol: string): string {
  if (!symbol) return "";
  return symbol.replace(SYMBOL_STRIP_RE, "").toLowerCase();
}

export function symbolTail(symbol: string): string {
  const s = normalizeSymbol(symbol);
  if (!s) return s;
  return s.split(".").at(-1) ?? s;
}
