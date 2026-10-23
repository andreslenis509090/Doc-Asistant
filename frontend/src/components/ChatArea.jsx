import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import {
  ArrowUp,
  Sparkles,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  ArrowRight,
  Bookmark,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { streamChatApi } from '../services/api';

const SUGGESTED_PROMPTS = [
  '¿Cuáles son los objetivos principales de esta guía?',
  'Resume el contenido temático y conceptos clave.',
  '¿Qué fórmulas, ecuaciones o variables se analizan?',
];

export default function ChatArea({ selectedDoc, onOpenCitation }) {
  const { token } = useAuth();
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '¡Hola Andres! ¿En qué puedo ayudarte hoy con tus documentos? Puedo responder preguntas, resumir secciones o explicar fórmulas basándome estrictamente en tus PDFs.',
      citations: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 'welcome-' + Date.now(),
        role: 'assistant',
        content: 'Conversación reiniciada. ¿Qué otra consulta tienes sobre tus documentos?',
        citations: [],
      },
    ]);
  };

  const handleSend = async (customMessage = null) => {
    const query = (customMessage || input).trim();
    if (!query || loading) return;

    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    const assistantMsgId = 'msg-' + Date.now();

    setMessages((prev) => [
      ...prev,
      { id: 'user-' + Date.now(), role: 'user', content: query },
      { id: assistantMsgId, role: 'assistant', content: '', citations: [], isStreaming: true },
    ]);
    setLoading(true);

    await streamChatApi({
      message: query,
      documentId: selectedDoc?.id || null,
      token,
      onCitations: (citations) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.id !== assistantMsgId) return prev;
          return [...prev.slice(0, -1), { ...last, citations }];
        });
      },
      onToken: (tokenText) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.id !== assistantMsgId) return prev;
          return [...prev.slice(0, -1), { ...last, content: last.content + tokenText }];
        });
      },
      onDone: () => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.id !== assistantMsgId) return prev;
          return [...prev.slice(0, -1), { ...last, isStreaming: false }];
        });
        setLoading(false);
      },
      onError: (err) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (!last || last.id !== assistantMsgId) return prev;
          return [
            ...prev.slice(0, -1),
            {
              ...last,
              content:
                last.content +
                `\n\n> ⚠️ **Error al generar respuesta:** ${err.message || 'Fallo de conexión'}`,
              isStreaming: false,
            },
          ];
        });
        setLoading(false);
      },
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputResize = (e) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <main className="flex-1 flex flex-col h-full bg-[#212121] overflow-hidden text-[#ececec]">
      {/* Top Bar */}
      <header className="h-12 px-5 border-b border-[#2f2f2f] bg-[#212121]/90 backdrop-blur-md flex items-center justify-between shrink-0 z-10">
        <div className="flex items-center gap-2 text-xs">
          <BookOpen className="w-3.5 h-3.5 text-[#8e8e8e]" />
          <span className="text-[#8e8e8e] hidden sm:inline">Contexto:</span>
          <span className="font-medium text-white bg-[#2f2f2f] px-2.5 py-0.5 rounded-full text-xs truncate max-w-[260px]">
            {selectedDoc ? selectedDoc.filename : 'Todos los documentos'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleClearChat}
            title="Nuevo chat"
            className="flex items-center gap-1.5 px-2 py-1 text-xs text-[#8e8e8e] hover:text-white rounded-md hover:bg-[#2f2f2f] transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            <span className="hidden sm:inline">Limpiar chat</span>
          </button>
          <div className="h-3.5 w-px bg-[#2f2f2f]" />
          <div className="flex items-center gap-1.5 text-[11px] text-[#8e8e8e]">
            <Sparkles className="w-3 h-3 text-[#10a37f]" />
            <span>Gemini 3.5 Flash</span>
          </div>
        </div>
      </header>

      {/* Messages Scroll View */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 sm:gap-4 ${
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {/* Bot Avatar */}
              {msg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-full bg-[#10a37f] flex items-center justify-center shrink-0 text-white shadow-sm mt-0.5">
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                </div>
              )}

              {/* Message Content */}
              <div
                className={`flex flex-col gap-2 max-w-[85%] ${
                  msg.role === 'user' ? 'items-end' : 'items-start flex-1'
                }`}
              >
                {msg.role === 'user' ? (
                  <div className="bg-[#2f2f2f] text-white px-4 py-2.5 rounded-3xl text-sm leading-relaxed whitespace-pre-wrap max-w-full">
                    {msg.content}
                  </div>
                ) : (
                  <div className="relative group w-full text-sm leading-relaxed text-[#ececec]">
                    <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-headings:text-white prose-headings:font-semibold prose-strong:text-white prose-ul:my-2 prose-li:my-0.5">
                      {msg.content ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      ) : msg.isStreaming ? (
                        <div className="flex items-center gap-2 text-[#8e8e8e] py-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#10a37f] animate-ping" />
                          <span className="text-xs">Buscando citas y redactando...</span>
                        </div>
                      ) : null}

                      {msg.isStreaming && msg.content && (
                        <span className="inline-block w-1.5 h-4 bg-white ml-1 animate-pulse align-middle" />
                      )}
                    </div>

                    {/* Copy Button */}
                    {msg.content && !msg.isStreaming && (
                      <div className="flex items-center gap-2 mt-2 pt-1">
                        <button
                          onClick={() => handleCopy(msg.id, msg.content)}
                          title="Copiar respuesta"
                          className="flex items-center gap-1 text-[11px] text-[#8e8e8e] hover:text-white p-1 rounded hover:bg-[#2f2f2f] transition-colors"
                        >
                          {copiedId === msg.id ? (
                            <>
                              <Check className="w-3 h-3 text-[#10a37f]" />
                              <span className="text-[#10a37f]">Copiado</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copiar</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Citations Badges */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="text-[10px] text-[#8e8e8e] flex items-center gap-1 mr-1">
                      <Bookmark className="w-2.5 h-2.5 text-[#10a37f]" /> Fuentes:
                    </span>
                    {msg.citations.map((c, cIdx) => (
                      <button
                        key={cIdx}
                        onClick={() => onOpenCitation(c)}
                        title={`Ver cita de ${c.document_name} página ${c.page_number}`}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-[#2f2f2f] hover:bg-[#383838] text-[#d1d5db] hover:text-white border border-[#404040] transition-colors cursor-pointer"
                      >
                        <span className="font-medium text-[#10a37f]">Pág. {c.page_number}</span>
                        <span className="text-[#8e8e8e] text-[10px]">({c.document_name})</span>
                        <span className="text-[10px] text-[#10a37f] font-mono">
                          {(c.similarity * 100).toFixed(0)}%
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Suggested Prompts (ChatGPT style cards) */}
          {messages.length === 1 && (
            <div className="pt-8 max-w-2xl mx-auto">
              <p className="text-xs font-medium text-[#8e8e8e] text-center mb-3">
                Sugerencias para empezar
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {SUGGESTED_PROMPTS.map((promptText, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(promptText)}
                    className="p-3 text-left rounded-2xl bg-[#212121] hover:bg-[#282828] border border-[#2f2f2f] hover:border-[#404040] text-xs text-[#b4b4b4] hover:text-white transition-all flex flex-col justify-between group"
                  >
                    <span className="leading-relaxed">{promptText}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#666666] group-hover:text-white group-hover:translate-x-0.5 transition-all mt-3 self-end" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Floating Input Capsule (ChatGPT Style) */}
      <div className="p-4 bg-gradient-to-t from-[#212121] via-[#212121] to-transparent shrink-0">
        <div className="max-w-3xl mx-auto">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="relative bg-[#2f2f2f] border border-[#383838] focus-within:border-[#525252] rounded-3xl shadow-lg transition-colors flex items-center px-4 py-2"
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputResize}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder={
                loading
                  ? 'Generando respuesta...'
                  : selectedDoc
                  ? `Pregunta sobre ${selectedDoc.filename}...`
                  : 'Mensaje a Docs Assistant...'
              }
              className="w-full bg-transparent text-sm text-white placeholder-[#8e8e8e] focus:outline-none resize-none py-1.5 pr-10 max-h-36"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className={`absolute right-3 p-1.5 rounded-full transition-all flex items-center justify-center cursor-pointer disabled:cursor-not-allowed ${
                input.trim() && !loading
                  ? 'bg-white text-black hover:bg-neutral-200 shadow-sm'
                  : 'bg-[#404040] text-[#737373]'
              }`}
            >
              <ArrowUp className="w-4 h-4 stroke-[2.5]" />
            </button>
          </form>

          <div className="text-center mt-2 text-[11px] text-[#737373]">
            Docs Assistant puede cometer errores. Verifica la información en las citas.
          </div>
        </div>
      </div>
    </main>
  );
}
