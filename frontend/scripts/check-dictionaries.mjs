/**
 * Guard against dictionary drift.
 *
 * TypeScript already catches a missing key, but not an untranslated one: a
 * copy-pasted English value in ar.ts type-checks perfectly and ships an English
 * string into an Arabic screen. This walks both trees and reports keys whose
 * values are identical, plus any placeholder that did not survive translation.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))

// Values that are the same in both languages by design: header names and other
// literal API tokens, which are not prose and must not be translated.
const ALLOWED_IDENTICAL = new Set([
  'providers.authBearer',
  'admin.openaiGenerations',
  'admin.geminiGenerations',
  'admin.minimaxGenerations',
])

function extractStrings(source, exportName) {
  // A deliberately small parser: the dictionaries are two-level objects of
  // string literals, so a full TS parse would be more machinery than the job
  // needs. The declaration may carry a type annotation (`ar: Dictionary = {`),
  // so find the name first and the opening brace after it.
  const declaration = source.indexOf(`const ${exportName}`)
  if (declaration === -1) throw new Error(`could not find the ${exportName} declaration`)
  const open = source.indexOf('= {', declaration)
  if (open === -1) throw new Error(`could not find the body of ${exportName}`)

  const out = {}
  let section = null
  let pendingKey = null

  for (const raw of source.slice(open).split('\n')) {
    const line = raw.trim()

    if (line.endsWith(': {')) {
      section = line.slice(0, -3).trim()
      continue
    }
    if (line === '},' || line === '}') {
      section = null
      continue
    }
    if (!section) continue

    // A value wrapped onto its own line: `key:` then `'value',`
    if (pendingKey) {
      const value = line.match(/^'(.*)',?$/)
      if (value) out[`${section}.${pendingKey}`] = value[1]
      pendingKey = null
      continue
    }
    if (line.endsWith(':')) {
      pendingKey = line.slice(0, -1).trim()
      continue
    }

    const kv = line.match(/^(\w+):\s*'(.*)',?$/)
    if (kv) out[`${section}.${kv[1]}`] = kv[2]
  }
  return out
}

const en = extractStrings(
  readFileSync(resolve(here, '../lib/i18n/dictionaries/en.ts'), 'utf8'),
  'en',
)
const ar = extractStrings(
  readFileSync(resolve(here, '../lib/i18n/dictionaries/ar.ts'), 'utf8'),
  'ar',
)

const placeholders = (value) => (value.match(/\{(\w+)\}/g) ?? []).sort().join(',')
const problems = []

for (const key of Object.keys(en)) {
  if (!(key in ar)) {
    problems.push(`missing in ar: ${key}`)
    continue
  }
  if (ar[key] === en[key] && !ALLOWED_IDENTICAL.has(key)) {
    problems.push(`untranslated: ${key} — "${en[key]}"`)
  }
  if (placeholders(en[key]) !== placeholders(ar[key])) {
    problems.push(`placeholder mismatch: ${key}`)
  }
}

for (const key of Object.keys(ar)) {
  if (!(key in en)) problems.push(`extra in ar: ${key}`)
}

if (problems.length > 0) {
  console.error(`Dictionary check failed (${problems.length}):`)
  for (const problem of problems) console.error(`  ${problem}`)
  process.exit(1)
}

console.log(`Dictionaries agree — ${Object.keys(en).length} keys, en + ar.`)
