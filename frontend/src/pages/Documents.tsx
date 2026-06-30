import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Files, History, Image, Mic, Paperclip, Trash2, Type, UploadCloud } from 'lucide-react'
import {
  deleteDocument,
  exportDocumentText,
  extractAttachments,
  getDocumentHistory,
  getDocuments,
} from '../api/client'

function fmtBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function Documents() {
  const qc = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [notice, setNotice] = useState('')
  const docs = useQuery({ queryKey: ['documents'], queryFn: getDocuments })
  const history = useQuery({ queryKey: ['documents-history'], queryFn: getDocumentHistory })
  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: async () => {
      await Promise.all([
        qc.invalidateQueries({ queryKey: ['documents'] }),
        qc.invalidateQueries({ queryKey: ['documents-history'] }),
      ])
    },
  })

  const documents = docs.data ?? []
  const events = history.data ?? []
  const latestDocument = documents[0]

  async function downloadDocument(id: string, name: string) {
    const text = await exportDocumentText(id)
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${name}.txt`
    link.click()
    URL.revokeObjectURL(url)
  }

  async function upload(fileList?: FileList | null) {
    const files = Array.from(fileList ?? [])
    if (!files.length) return
    setNotice('Extracting and saving documents...')
    try {
      const extracted = await extractAttachments(files)
      setNotice(`${extracted.filter(item => item.kind !== 'unsupported').length} document(s) saved.`)
      await Promise.all([
        qc.invalidateQueries({ queryKey: ['documents'] }),
        qc.invalidateQueries({ queryKey: ['documents-history'] }),
      ])
    } catch {
      setNotice('Upload failed. Check the orchestrator and OCR/voice services.')
    } finally {
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="page documents-page">
      <header className="page-intro documents-intro">
        <div className="page-icon"><Files className="h-5 w-5" /></div>
        <div>
          <p className="eyebrow">Knowledge library</p>
          <h1>Documents</h1>
          <p>Upload text, image, and audio files. Export extracted text and review document history.</p>
        </div>
      </header>

      <section className="surface-card document-upload-card">
        <input
          ref={inputRef}
          type="file"
          multiple
          className="composer-file-input"
          accept=".txt,.md,.csv,.json,.png,.jpg,.jpeg,.webp,.wav,.mp3,.m4a,.webm,.ogg,text/plain,text/markdown,text/csv,application/json,image/*,audio/*"
          onChange={event => void upload(event.target.files)}
        />
        <button className="document-drop" onClick={() => inputRef.current?.click()}>
          <span className="document-drop-icon"><UploadCloud className="h-6 w-6" /></span>
          <strong>Upload documents</strong>
          <span>Drop in reports, screenshots, notes, or voice memos. LaRuche extracts clean context for the advisor.</span>
          <div className="document-type-pills">
            <span><Type className="h-3 w-3" /> Text</span>
            <span><Image className="h-3 w-3" /> OCR</span>
            <span><Mic className="h-3 w-3" /> Voice</span>
          </div>
        </button>
        {notice && <p className="document-notice">{notice}</p>}
      </section>

      <div className="document-summary-grid">
        <div className="surface-card document-summary-card">
          <span>Total files</span>
          <strong>{documents.length}</strong>
        </div>
        <div className="surface-card document-summary-card">
          <span>History events</span>
          <strong>{events.length}</strong>
        </div>
        <div className="surface-card document-summary-card document-summary-wide">
          <span>Latest document</span>
          <strong>{latestDocument ? latestDocument.name : 'No uploads yet'}</strong>
        </div>
      </div>

      <div className="documents-grid">
        <section className="surface-card document-panel">
          <div className="data-panel-header">
            <h2>Library</h2>
            <span>{documents.length} saved files</span>
          </div>
          <div className="document-list">
            {documents.map(doc => (
              <article key={doc.id} className="document-row">
                <div className="document-kind"><Paperclip className="h-4 w-4" /></div>
                <div>
                  <h3>{doc.name}</h3>
                  <p>{doc.preview || 'No extracted preview available.'}</p>
                  <small>{doc.kind} - {fmtBytes(doc.size)} - {new Date(doc.created_at).toLocaleString()}</small>
                </div>
                <div className="document-actions">
                  <button
                    className="icon-button"
                    title="Export extracted text"
                    onClick={() => void downloadDocument(doc.id, doc.name)}
                  >
                    <Download className="h-4 w-4" />
                  </button>
                  <button
                    className="icon-button"
                    title="Delete document"
                    onClick={() => deleteMutation.mutate(doc.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </article>
            ))}
            {docs.isLoading && <div className="empty-card empty-card-tall">Loading your document library...</div>}
            {!docs.isLoading && !documents.length && (
              <div className="empty-card empty-card-tall">
                <Files className="h-6 w-6" />
                <strong>No documents yet</strong>
                <span>Upload a text file, image, or voice note to build your local library.</span>
              </div>
            )}
          </div>
        </section>

        <aside className="surface-card document-panel">
          <div className="data-panel-header">
            <h2><History className="h-4 w-4" /> History</h2>
            <span>Latest uploads</span>
          </div>
          <div className="history-list">
            {events.slice().reverse().map(event => (
              <div key={`${event.document_id}-${event.timestamp}`} className="history-row">
                <strong>{event.name}</strong>
                <span>{event.kind} uploaded</span>
                <small>{new Date(event.timestamp).toLocaleString()}</small>
              </div>
            ))}
            {history.isLoading && <div className="empty-card empty-card-tall">Loading history...</div>}
            {!history.isLoading && !events.length && (
              <div className="empty-card empty-card-tall">
                <History className="h-6 w-6" />
                <strong>No history yet</strong>
                <span>Uploads, exports, and deletes will appear here.</span>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
