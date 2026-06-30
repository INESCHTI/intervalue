import { detectLanguage, languageToLocale, type SupportedLanguage } from './language'

function stripMarkdown(text: string): string {
  let s = text
  // LaTeX blocks: $$...$$ and $...$  and \(...\) and \[...\]
  s = s.replace(/\$\$[\s\S]*?\$\$/g, '')
  s = s.replace(/\$[^$\n]+?\$/g, '')
  s = s.replace(/\\\(.*?\\\)/g, '')
  s = s.replace(/\\\[[\s\S]*?\\\]/g, '')
  // Code blocks ```...```
  s = s.replace(/```[\s\S]*?```/g, '')
  // Inline code `...`
  s = s.replace(/`[^`]+`/g, '')
  // Images ![alt](url)
  s = s.replace(/!\[[^\]]*\]\([^)]*\)/g, '')
  // Links [text](url) → keep text
  s = s.replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
  // Headings ### → remove hashes
  s = s.replace(/^#{1,6}\s+/gm, '')
  // Bold/italic ***text*** **text** *text* __text__ _text_
  s = s.replace(/\*{1,3}([^*]+)\*{1,3}/g, '$1')
  s = s.replace(/_{1,3}([^_]+)_{1,3}/g, '$1')
  // Strikethrough ~~text~~
  s = s.replace(/~~([^~]+)~~/g, '$1')
  // Blockquotes >
  s = s.replace(/^>\s+/gm, '')
  // Horizontal rules --- *** ___
  s = s.replace(/^[-*_]{3,}\s*$/gm, '')
  // Unordered list markers - * +
  s = s.replace(/^[\s]*[-*+]\s+/gm, '')
  // Ordered list markers 1. 2.
  s = s.replace(/^[\s]*\d+\.\s+/gm, '')
  // HTML tags
  s = s.replace(/<[^>]+>/g, '')
  // Table pipes and dashes
  s = s.replace(/\|/g, ', ')
  s = s.replace(/^[\s]*[-:]+[\s]*$/gm, '')
  // Collapse multiple whitespace/newlines
  s = s.replace(/\n{2,}/g, '. ')
  s = s.replace(/\s+/g, ' ')
  return s.trim()
}

type SpeakOptions = {
  rate?: number
  pitch?: number
  onStart?: () => void
  language?: SupportedLanguage
  voiceURI?: string
}

const PREFERRED_NAMES: Record<SupportedLanguage, string[]> = {
  en: ['aria', 'jenny', 'guy', 'samantha', 'alex', 'daniel', 'google us english'],
  fr: ['denise', 'henri', 'thomas', 'audrey', 'google français', 'google francais'],
  ar: ['hoda', 'naayf', 'maged', 'tarik', 'google العربية', 'ar'],
}

function pickVoice(voices: SpeechSynthesisVoice[], language: SupportedLanguage, voiceURI = '') {
  if (voiceURI) {
    const selected = voices.find(voice => voice.voiceURI === voiceURI)
    if (selected) return selected
  }
  const locale = languageToLocale(language).toLowerCase()
  const family = language
  const languageVoices = voices.filter(voice => voice.lang.toLowerCase().startsWith(family))
  const preferredNames = PREFERRED_NAMES[language]

  return (
    languageVoices.find(voice => voice.lang.toLowerCase() === locale && preferredNames.some(name => voice.name.toLowerCase().includes(name))) ??
    languageVoices.find(voice => voice.lang.toLowerCase() === locale) ??
    languageVoices.find(voice => preferredNames.some(name => voice.name.toLowerCase().includes(name))) ??
    languageVoices[0] ??
    null
  )
}

export function loadVoices() {
  const synth = window.speechSynthesis
  const voices = synth.getVoices()
  if (voices.length) return Promise.resolve(voices)

  return new Promise<SpeechSynthesisVoice[]>(resolve => {
    const timeout = window.setTimeout(() => resolve(synth.getVoices()), 350)
    const onVoicesChanged = () => {
      window.clearTimeout(timeout)
      synth.removeEventListener('voiceschanged', onVoicesChanged)
      resolve(synth.getVoices())
    }
    synth.addEventListener('voiceschanged', onVoicesChanged)
  })
}

export async function speakLocalized(text: string, options: SpeakOptions = {}) {
  if (!('speechSynthesis' in window)) return

  const clean = stripMarkdown(text)
  if (!clean) return
  const language = options.language ?? detectLanguage(clean)
  const voices = await loadVoices()
  const utterance = new SpeechSynthesisUtterance(clean)
  const voice = pickVoice(voices, language, options.voiceURI)

  utterance.lang = voice?.lang ?? languageToLocale(language)
  utterance.voice = voice
  utterance.rate = options.rate ?? 0.96
  utterance.pitch = options.pitch ?? (language === 'ar' ? 0.98 : 0.94)

  return new Promise<void>(resolve => {
    window.speechSynthesis.cancel()
    utterance.onstart = options.onStart ?? null
    utterance.onend = () => resolve()
    utterance.onerror = () => resolve()
    window.speechSynthesis.speak(utterance)
  })
}
