import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from 'react-router-dom';


const SignDocument = () => {
    const location = useLocation();
    const [signingUrl, setSigningUrl] = useState('');
    
    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const url = queryParams.get("signing_url");

        if (url) {
            setSigningUrl(decodeURIComponent(url));  // Decode the URL as it was encoded in the backend
        }
    }, [location.state]);

    return (
        <div>
            <h1>Sign Document</h1>
            {signingUrl ? (
                <iframe
                    src={signingUrl}
                    width="100%"
                    height="600px"
                    title="DocuSign Signing"
                />
            ) : (
                <p>Loading signing interface...</p>
            )}
        </div>
    );
};

export default SignDocument;