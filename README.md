# CONTRACT ANALYZER APPLICATION
This application allows the user to submit a pdf file containing a contract and have the contract analyzed by an AI model. The model provides the following results post-analysis:
+ A short form summary
+ A long form summary
+ Sections of the contract that correspond to the most important labels in contracts.

The short form uses the Google Pagasus model from hugging face that can be viewed <a href="https://huggingface.co/google/pegasus-xsum">here</a>.

The long form summary uses a model that I trained and deployed <a href="https://huggingface.co/louiseclon3/summarization-legal">here</a>. The model used is based on distillbart that can be found <a href="https://huggingface.co/sshleifer/distilbart-cnn-12-6">here</a>.

Finally, the labeling model is finetuned from the <a href="https://huggingface.co/nlpaueb/legal-bert-base-uncased">Legal-Bert uncased</a> model. The finetuning process can be seen <a href="https://www.kaggle.com/code/hannahmuthonihailu/legal-bert-finetuning/edit">here</a> and the final tuned model can be viewed <a href="https://huggingface.co/louiseclon3/labeling-legal">here</a>

The application also allows the user to sign the document through the <a href="https://developers.docusign.com/docs/esign-rest-api/reference/">Docusign E-signature REST Api</a>

The final working version of the application can be accessed <a href="https://contract-analyzer-uw74.onrender.com/>here</a>.

The application is licensed under <a href="https://opensource.org/license/mit">The MIT License</a>.