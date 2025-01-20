import React, { useState } from 'react';
import axios from 'axios';
import { useLocation, useNavigate } from 'react-router-dom';

const SignDocument = () => {
    const [signingUrl, setSigningUrl] = useState(null);
    const [userEmail, setUserEmail] = useState('');
    const [userName, setUserName] = useState('');
    const location = useLocation();
    const result = location.state?.result || 'No result available.';


    const handleSignDocument = async () => {
        try {
            const response = await axios.post('http://localhost:5000/create-signing-url', {
                email: userEmail,
                name: userName,
                documentPath: result['filepath']
            });
            setSigningUrl(response.data.signingUrl);
        } catch (error) {
            console.error("Error creating signing URL:", error);
        }
    };

    return (
        <div>
            <div>
                <div className="mb-3">
                    <label htmlFor="userName" className="form-label">Your Name</label>
                    <input type="text" id="userName" value={userName} onChange={(e) => setUserName(e.target.value)} className="form-control" required/>
                </div>

                <div className="mb-3">
                    <label htmlFor="userEmail" className="form-label">Your Email</label>
                    <input type="email" id="userEmail" value={userEmail} onChange={(e) => setUserEmail(e.target.value)} className="form-control" required/>
                </div>
            </div>
            <button onClick={handleSignDocument}>Sign Document</button>
            {signingUrl && (
                <div>
                    <p>Click the link below to sign the document:</p>
                    <a href={signingUrl} target="_blank" rel="noopener noreferrer">Sign Document</a>
                </div>
            )}
        </div>
    );
};

export default SignDocument;