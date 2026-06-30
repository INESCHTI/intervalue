import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import type { SupportedLanguage } from '../utils/language'

export type LanguageMode = 'auto' | SupportedLanguage

export type UserSettings = {
  languageMode: LanguageMode
  voiceURI: string
  setLanguageMode: (language: LanguageMode) => void
  setVoiceURI: (voiceURI: string) => void
}

const SettingsContext = createContext<UserSettings | null>(null)

const STORAGE_KEY = 'laruche.user-settings'

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { languageMode: 'auto' as LanguageMode, voiceURI: '' }
    const parsed = JSON.parse(raw) as Partial<Pick<UserSettings, 'languageMode' | 'voiceURI'>>
    return {
      languageMode: parsed.languageMode ?? 'auto',
      voiceURI: parsed.voiceURI ?? '',
    }
  } catch {
    return { languageMode: 'auto' as LanguageMode, voiceURI: '' }
  }
}

export function UserSettingsProvider({ children }: { children: ReactNode }) {
  const initial = loadSettings()
  const [languageMode, setLanguageMode] = useState<LanguageMode>(initial.languageMode)
  const [voiceURI, setVoiceURI] = useState(initial.voiceURI)

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ languageMode, voiceURI }))
  }, [languageMode, voiceURI])

  const value = useMemo(
    () => ({ languageMode, voiceURI, setLanguageMode, setVoiceURI }),
    [languageMode, voiceURI],
  )

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useUserSettings() {
  const context = useContext(SettingsContext)
  if (!context) throw new Error('useUserSettings must be used inside UserSettingsProvider')
  return context
}
