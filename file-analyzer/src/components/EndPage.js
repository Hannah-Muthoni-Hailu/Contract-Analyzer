import React from 'react';
import { useLocation } from 'react-router-dom';

const EndPage = () => {
    const location = useLocation();

    return (
        <div className="container mt-5">
            <h1 className='text-center fs-1'>Thankyou for using our application!</h1>
        </div>
    );
};

export default EndPage;
