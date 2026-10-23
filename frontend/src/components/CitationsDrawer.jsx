import React from 'react';
import { X, Bookmark } from 'lucide-react';

export default function CitationsDrawer({ citation, onClose }) {
  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg bg-[#1e1e1e] border border-[#2f2f2f] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh] text-[#ececec]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#2f2f2f] bg-[#1a1a1a]">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-[#10a37f]/20 text-[#10a37f]">
              <Bookmark className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Detalle de la Cita</h3>
              <p className="text-[11px] text-[#8e8e8e]">Fragmento extraído de tus documentos</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#8e8e8e] hover:text-white hover:bg-[#2f2f2f] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-[#252525] border border-[#2f2f2f]">
              <span className="text-[#8e8e8e] block mb-1">Documento:</span>
              <span className="font-medium text-white break-words">{citation.document_name}</span>
            </div>
            <div className="p-3 rounded-xl bg-[#252525] border border-[#2f2f2f]">
              <span className="text-[#8e8e8e] block mb-1">Página citada:</span>
              <span className="font-semibold text-[#10a37f]">Página {citation.page_number}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-[#252525] border border-[#2f2f2f] flex items-center justify-between">
            <span className="text-[#8e8e8e]">Similitud semántica (pgvector):</span>
            <span className="px-2 py-0.5 rounded-full bg-[#10a37f]/20 text-[#10a37f] font-mono font-medium">
              {(citation.similarity * 100).toFixed(1)}% de coincidencia
            </span>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#8e8e8e] mb-2 uppercase tracking-wider">
              Texto exacto del fragmento:
            </label>
            <div className="p-4 rounded-xl bg-[#141414] border border-[#282828] text-xs text-[#d1d5db] leading-relaxed font-mono whitespace-pre-wrap">
              {citation.snippet}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#2f2f2f] bg-[#1a1a1a] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#2f2f2f] hover:bg-[#383838] text-white rounded-xl text-xs font-medium transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
}
