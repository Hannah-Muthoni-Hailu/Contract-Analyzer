import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import FileUpload from './components/FileUpload';
import ResultPage from './components/Results';
import EndPage from './components/EndPage';
import 'bootstrap/dist/css/bootstrap.min.css';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<FileUpload />} />
                <Route path="/result" element={<ResultPage />} />
                <Route path="/end-process" element={<EndPage />} />
            </Routes>
        </Router>
    );
}

export default App;