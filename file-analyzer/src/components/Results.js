import React, { useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Button from 'react-bootstrap/Button';
import axios from 'axios';

const ResultPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const result = location.state?.result || 'No result available.';
    
    const [showHelp, setShowHelp] = useState(true);
    const [summary, setSummary] = useState('');
    const [nohelp, setNoHelp] = useState('');
    const [help, setHelp] = useState('');
    const [email, setEmail] = useState('');
    const [formData, setFormData] = useState({});
    const [formErrors, setFormErrors] = useState({});
    const [response, setResponse] = useState(null);

    const helpFormRef = useRef(null);

    const displaySummary = (type) => {
        if (type === 'long') {
            setSummary(result['long-summary']);  // Display long summary
        } else {
            setSummary(result['short-summary']); // Display short summary
        }
    }

    const AIhelp = (decision) => {
        if (decision === "yes"){
            setHelp("Please answer these questions to better personalize the decision made by the AI model");
            if (helpFormRef.current) {
                helpFormRef.current.scrollIntoView({ behavior: 'smooth' });
            }
        }
        else {
            setNoHelp("Please answer these questions to better personalize the decision made by the AI model")
        }
    }

    // Handle input changes dynamically
    const handleInputChange = (event, questionIndex) => {
        const { name, value } = event.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value, // Use the question index as the key
        }));
    }

    const validateForm = () => {
        const errors = {};
        result.help.forEach((_, index) => {
            if (!formData[index]) {
                errors[index] = "This question is required";
            }
        });
        return errors;
    }

    // Handle form submission
    const handleSubmit = async (event) => {
        event.preventDefault();

        // Validate form
        const errors = validateForm();
        if (Object.keys(errors).length > 0) {
            setFormErrors(errors);  // Set form errors if validation fails
            return;
        }

        // Prepare data for submission
        const submissionData = result.help.map((questionSet, index) => ({
            question: questionSet[2],
            response: formData[index],
        }));

        // Send data to the backend (app.py)
        try {
            const response = await axios.post('http://localhost:5000/submit-form', { answers: submissionData });
            setShowHelp(false);
            setResponse(response.data);
        } catch (error) {
            console.error('Error submitting form:', error);
        }
    }

    // Dynamically render the form elements based on `result.help`
    const renderHelpForm = () => {
        if (result.help && result.help.length > 0) {
            return result.help.map((questionSet, index) => {
                const question = questionSet[1];
                const prediction = questionSet[2];
                return (
                    <div key={index} className="mb-3">
                        <label className="form-label">{question} <br></br> <strong>{prediction}</strong></label>
                        <div>
                            {/* Yes radio button */}
                            <div className="form-check">
                                <input
                                    type="radio"
                                    id={`yes-${index}`}
                                    name={index} // Use the index as the name to identify this question
                                    value="yes"
                                    onChange={(e) => handleInputChange(e, index)}
                                    className="form-check-input"
                                    checked={formData[index] === 'yes'}
                                />
                                <label className="form-check-label" htmlFor={`yes-${index}`}>
                                    Yes
                                </label>
                            </div>

                            {/* No radio button */}
                            <div className="form-check">
                                <input
                                    type="radio"
                                    id={`no-${index}`}
                                    name={index} // Use the index as the name to identify this question
                                    value="no"
                                    onChange={(e) => handleInputChange(e, index)}
                                    className="form-check-input"
                                    checked={formData[index] === 'no'}
                                />
                                <label className="form-check-label" htmlFor={`no-${index}`}>
                                    No
                                </label>
                            </div>
                        </div>
                        {formErrors[index] && <div className="text-danger">{formErrors[index]}</div>}
                    </div>
                );
            });
        }
        return null;
    }

    // Sign the document
    const signDocument = async () => {
        const response = await axios.post('http://localhost:5000/create-signing-url', formData);
        console.log(response)
    }

    // Goodbye
    const goodbye = () => {
        navigate('/end-process');
    }

    if (!result) {
        return <div>No result available.</div>;
    }

    return (
        <div className="container mt-5 d-flex flex-column align-items-center p-2 border border-primary-subtle rounded-4 bg-body-secondary">
            <h1 className='m-3 text-primary'>Analysis complete!!</h1>
            <div className='d-flex flex-row justify-content-evenly w-50 p-3'>
                <Button onClick={() => displaySummary('long')}>Long Form Summary</Button>
                <Button onClick={() => displaySummary('short')}>Short Form Summary</Button>
            </div>

            {summary && (
                <div className="mt-4 p-3 w-75 border rounded bg-light d-flex flex-column align-items-center">
                    <h4>Summary:</h4>
                    <p>{summary}</p>
                    Would you like AI assistance in the negotiation?
                    <div className='d-flex flex-row justify-content-evenly w-100 p-3'>
                        <Button onClick={() => AIhelp('yes')}>Yes, Is this contract good for me?</Button>
                        <Button onClick={() => AIhelp('no')}>No, I've made my own decision!</Button>
                    </div>

                </div>
            )}

            {showHelp && help && (
                <div ref={helpFormRef} className="mt-4 p-3 w-75 border rounded bg-light">
                    <h4>{help}</h4>
                    <form onSubmit={handleSubmit}>
                        {renderHelpForm()}
                        <Button type="submit" className="mt-3">Submit Answers</Button>
                    </form>
                </div>
            )}

            {response && (
                <div className="mt-4 p-3 w-75 border rounded bg-light d-flex flex-column align-items-center">
                    <h4>Result</h4>
                    {response.analysis === 'good' ? <p>This contract seems to be a good fit for you. Your responses show that all elements of the contract are favorable to you. Feel free to sign the contract</p> 
                    : 
                    <div className='m-2'>
                        <p>This contract may not be a good fit for you. Please review the following sections that you did not find to suit your needs previously.</p>
                        <ul className='bg-white'>
                            {response.message.map((text) => (
                                <li>{text}</li>
                            ))}
                        </ul>
                    </div>
                    }
                    {response.analysis === 'good' ? <p>Would you like to sign the contract?</p> : <p>Do you still want to sign this contract despite the issues above?</p>}
                    <div className='d-flex flex-row justify-content-evenly w-100 p-3'>
                        <Button onClick={signDocument}>Sign the contract</Button>
                        <Button onClick={goodbye}>I don't want this contract</Button>
                    </div>
                </div>
            )}

            {nohelp && (
                <div className="mt-4 p-3 w-75 border rounded bg-light d-flex flex-column align-items-center">
                    Would you like to sign the document?
                    <div className='d-flex flex-row justify-content-evenly w-100 p-3'>
                        <Button onClick={signDocument}>Sign the contract</Button>
                        <Button onClick={goodbye}>I don't want this contract</Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ResultPage;
