import React, { useState } from 'react';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  Clock,
  AlertTriangle,
  LogOut,
  RefreshCw,
  FolderOpen,
  Filter,
  Trash2,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { uploadDocumentApi, deleteDocumentApi } from '../services/api';

export default function Sidebar({
  documents,
  selectedDocId,
  onSelectDoc,
  onRefreshDocs,
  loadingDocs,
}) {
  const { user, token, logout } = useAuth();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [deletingId, setDeletingId] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Solo se admiten archivos PDF');
      return;
    }

    setUploadError('');
    setUploading(true);
    try {
      await uploadDocumentApi(file, token);
      await onRefreshDocs();
    } catch (err) {
      setUploadError(err.message || 'Error al subir el archivo');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!confirm('¿Deseas eliminar este documento y sus fragmentos indexados?')) {
      return;
    }

    setDeletingId(docId);
    try {
      await deleteDocumentApi(docId, token);
      if (selectedDocId === docId) {
        onSelectDoc(null);
      }
      await onRefreshDocs();
    } catch (err) {
      alert(err.message || 'Error al eliminar');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <aside className="w-[270px] bg-[#171717] border-r border-[#262626] flex flex-col h-full shrink-0 select-none">
      {/* Brand Header */}
      <div className="p-3 border-b border-[#262626]">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-[#10a37f] flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white tracking-tight leading-tight">Docs Assistant</h1>
              <span className="text-[10px] text-[#8e8e8e]">RAG + pgvector</span>
            </div>
          </div>
          <button
            onClick={logout}
            title="Cerrar sesión"
            className="p-1.5 rounded-lg text-[#8e8e8e] hover:text-white hover:bg-[#212121] transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>

        <div className="mt-2.5 px-2.5 py-1.5 bg-[#212121] rounded-lg flex items-center justify-between text-xs border border-[#2f2f2f]">
          <span className="text-[#b4b4b4] truncate max-w-[190px] text-[11px]">{user?.email}</span>
          <span className="w-2 h-2 rounded-full bg-[#10a37f]" title="En línea"></span>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="p-3 border-b border-[#262626]">
        <label
          className={`border border-dashed rounded-xl p-3 flex flex-col items-center justify-center gap-1.5 cursor-pointer transition-colors ${
            uploading
              ? 'border-[#10a37f] bg-[#10a37f]/10 cursor-not-allowed'
              : 'border-[#383838] hover:border-[#525252] bg-[#212121]/60 hover:bg-[#212121]'
          }`}
        >
          <input
            type="file"
            accept=".pdf"
            disabled={uploading}
            onChange={handleFileUpload}
            className="hidden"
          />
          {uploading ? (
            <RefreshCw className="w-4 h-4 text-[#10a37f] animate-spin" />
          ) : (
            <UploadCloud className="w-4 h-4 text-[#b4b4b4]" />
          )}
          <div className="text-center">
            <p className="text-xs font-medium text-white">
              {uploading ? 'Indexando documento...' : 'Subir archivo PDF'}
            </p>
            <p className="text-[10px] text-[#8e8e8e]">Hasta 20 págs (máx 10 MB)</p>
          </div>
        </label>

        {uploadError && (
          <p className="mt-2 text-[11px] text-[#ef4444] bg-[#ef4444]/10 p-2 rounded-lg border border-[#ef4444]/20">
            {uploadError}
          </p>
        )}
      </div>

      {/* Filter / Scope Header */}
      <div className="px-3 py-2 border-b border-[#262626] flex items-center justify-between text-xs text-[#8e8e8e]">
        <div className="flex items-center gap-1.5 font-medium">
          <Filter className="w-3.5 h-3.5" />
          <span>Filtro de contexto</span>
        </div>
        <button
          onClick={onRefreshDocs}
          title="Actualizar documentos"
          className="p-1 rounded text-[#8e8e8e] hover:text-white transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingDocs ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <button
          onClick={() => onSelectDoc(null)}
          className={`w-full text-left px-3 py-2 rounded-lg text-xs flex items-center justify-between transition-colors ${
            selectedDocId === null
              ? 'bg-[#262626] text-white font-medium'
              : 'text-[#b4b4b4] hover:bg-[#212121] hover:text-white'
          }`}
        >
          <div className="flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-[#8e8e8e]" />
            <span>Todos los documentos</span>
          </div>
          <span className="text-[10px] bg-[#171717] px-2 py-0.5 rounded-full text-[#8e8e8e]">
            {documents.length}
          </span>
        </button>

        <div className="pt-3 pb-1 text-[10px] font-semibold text-[#666666] uppercase tracking-wider px-2">
          Tus Documentos
        </div>

        {documents.length === 0 ? (
          <div className="p-4 text-center text-xs text-[#666666]">
            No hay PDFs cargados.
          </div>
        ) : (
          documents.map((doc) => {
            const isSelected = selectedDocId === doc.id;
            const isDeleting = deletingId === doc.id;
            return (
              <div
                key={doc.id}
                onClick={() => onSelectDoc(doc.id)}
                className={`group relative px-3 py-2 rounded-lg text-xs cursor-pointer flex items-center justify-between transition-colors ${
                  isSelected
                    ? 'bg-[#262626] text-white font-medium'
                    : 'text-[#b4b4b4] hover:bg-[#212121] hover:text-white'
                }`}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <FileText className="w-4 h-4 text-[#8e8e8e] shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate" title={doc.filename}>
                      {doc.filename}
                    </p>
                    <div className="flex items-center gap-1.5 text-[10px] text-[#737373] mt-0.5">
                      <span>{doc.page_count} pág.</span>
                      <span>•</span>
                      {doc.status === 'completed' && (
                        <span className="flex items-center gap-1 text-[#10a37f]">
                          <CheckCircle2 className="w-2.5 h-2.5" /> Listo
                        </span>
                      )}
                      {doc.status === 'processing' && (
                        <span className="flex items-center gap-1 text-[#eab308]">
                          <Clock className="w-2.5 h-2.5 animate-spin" /> Procesando
                        </span>
                      )}
                      {doc.status === 'failed' && (
                        <span className="flex items-center gap-1 text-[#ef4444]">
                          <AlertTriangle className="w-2.5 h-2.5" /> Error
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Delete button */}
                <button
                  onClick={(e) => handleDelete(e, doc.id)}
                  disabled={isDeleting}
                  title="Eliminar documento"
                  className="opacity-0 group-hover:opacity-100 p-1 rounded text-[#8e8e8e] hover:text-[#ef4444] hover:bg-[#171717] transition-all ml-1 shrink-0"
                >
                  {isDeleting ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Trash2 className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
