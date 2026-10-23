import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginModal from './components/LoginModal';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import CitationsDrawer from './components/CitationsDrawer';
import { getDocumentsApi } from './services/api';

function MainApp() {
  const { isAuthenticated, token } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [activeCitation, setActiveCitation] = useState(null);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const fetchDocuments = async () => {
    if (!token) return;
    setLoadingDocs(true);
    try {
      const data = await getDocumentsApi(token);
      setDocuments(data);
    } catch (err) {
      console.error('Error al cargar documentos:', err);
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchDocuments();
    }
  }, [isAuthenticated, token]);

  if (!isAuthenticated) {
    return <LoginModal />;
  }

  const selectedDoc = documents.find((d) => d.id === selectedDocId) || null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 font-sans">
      <Sidebar
        documents={documents}
        selectedDocId={selectedDocId}
        onSelectDoc={setSelectedDocId}
        onRefreshDocs={fetchDocuments}
        loadingDocs={loadingDocs}
      />
      <ChatArea
        selectedDoc={selectedDoc}
        onOpenCitation={setActiveCitation}
      />
      <CitationsDrawer
        citation={activeCitation}
        onClose={() => setActiveCitation(null)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}
