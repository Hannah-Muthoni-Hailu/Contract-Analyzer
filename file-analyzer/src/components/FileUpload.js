import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';

const FileUpload = () => {
    const [file, setFile] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async () => {
        if (!file) return;
        
        const allowedTypes = ['application/pdf'];
        if (!allowedTypes.includes(file.type)) {
            alert('Only PDF files are allowed.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        setLoading(true);

        try {
            const response = await axios.post('http://localhost:5000/upload', formData);
            navigate('/result', { state: { result: response.data } });
        } catch (error) {
            console.error('Error uploading file:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2 className="fs-4 text-center m-4">Upload a File</h2>
            <Form className='d-flex flex-column align-items-center m-4'>
                <Form.Group className='m-3'>
                    <Form.Control type="file" size="lg" onChange={handleFileChange} />
                </Form.Group>
                <Button className='text-center' type="submit" onClick={handleUpload} disabled={!file || loading}>{loading ? 'Uploading...' : 'Upload'}</Button>
            </Form>
            {result && (
                <div>
                    <h3>Analysis Result:</h3>
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </div>
            )}
        </div>
    );
};

export default FileUpload;