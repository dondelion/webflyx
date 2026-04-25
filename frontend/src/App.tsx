import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import VoiceLibraryPage from "./pages/VoiceLibraryPage";
import UploadPage from "./pages/UploadPage";
import ChunkEditorPage from "./pages/ChunkEditorPage";
import TrainPage from "./pages/TrainPage";
import SynthesizePage from "./pages/SynthesizePage";
import ApiKeysPage from "./pages/ApiKeysPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/voices" replace />} />
          <Route path="voices" element={<VoiceLibraryPage />} />
          <Route path="voices/:voiceId/upload" element={<UploadPage />} />
          <Route path="voices/:voiceId/chunks" element={<ChunkEditorPage />} />
          <Route path="voices/:voiceId/train" element={<TrainPage />} />
          <Route path="voices/:voiceId/synthesize" element={<SynthesizePage />} />
          <Route path="settings/keys" element={<ApiKeysPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
