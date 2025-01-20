import base64
from os import path

from docusign_esign import AccountsApi, EnvelopesApi, RecipientViewRequest, Document, Signer, EnvelopeDefinition, SignHere, Tabs, \
    Recipients
from docusign_esign.client.api_exception import ApiException
from flask import session, url_for, request

from ...consts import authentication_method, demo_docs_path, pattern, signer_client_id
from ...docusign import create_api_client
from ...ds_config import DS_CONFIG


class Eg041CFREmbeddedSigningController:
    @staticmethod
    def get_args():
        signer_email = pattern.sub("", request.form.get("signer_email"))
        signer_name = pattern.sub("", request.form.get("signer_name"))
        country_code = pattern.sub("", request.form.get("country_code"))
        phone_number = pattern.sub("", request.form.get("phone_number"))
        envelope_args = {"signer_email": signer_email, "signer_name": signer_name, "phone_number": phone_number, "country_code": country_code, "signer_client_id": signer_client_id, "ds_return_url": url_for("ds.ds_return", _external=True), "workflow_id": session['workflow_id']}
        args = {"account_id": session["ds_account_id"], "base_path": session["ds_base_path"], "access_token": session["ds_access_token"], "envelope_args": envelope_args}
        return args

    @classmethod
    def worker(cls, args):
        envelope_args = args["envelope_args"]
        # Create the envelope request object
        envelope_definition = cls.make_envelope(envelope_args)

        api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])

        envelope_api = EnvelopesApi(api_client)
        results = envelope_api.create_envelope(account_id=args["account_id"], envelope_definition=envelope_definition)

        envelope_id = results.envelope_id

        recipient_view_request = RecipientViewRequest(authentication_method=authentication_method, client_user_id=envelope_args["signer_client_id"], recipient_id="1", return_url=envelope_args["ds_return_url"], user_name=envelope_args["signer_name"], email=envelope_args["signer_email"])
        
        results = envelope_api.create_recipient_view(account_id=args["account_id"], envelope_id=envelope_id, recipient_view_request=recipient_view_request)

        return {"envelope_id": envelope_id, "redirect_url": results.url}

    #ds-snippet-start:eSign41Step3
    @classmethod
    def make_envelope(cls, args):
        with open(path.join(demo_docs_path, DS_CONFIG["doc_pdf"]), "rb") as file:
            content_bytes = file.read()
        base64_file_content = base64.b64encode(content_bytes).decode("ascii")

        # Create the document model
        document = Document(document_base64=base64_file_content, name="Sign document", file_extension="pdf", document_id=1)

        # Create the signer recipient model
        signer = Signer(email=args["signer_email"], name=args["signer_name"], recipient_id="1", routing_order="1", identity_verification={ "workflowId": session['workflow_id'], "steps": "null", "inputOptions":[{"name":"phone_number_list","valueType":"PhoneNumberList","phoneNumberList":[{"countryCode":args["country_code"],"code":"1","number":args["phone_number"]}]}], "idCheckConfigurationName":""}, client_user_id=args["signer_client_id"])

        # Create a sign_here tab (field on the document)
        sign_here = SignHere(anchor_string="/sn1/", anchor_units="pixels", anchor_y_offset="-30", anchor_x_offset="20")

        signer.tabs = Tabs(sign_here_tabs=[sign_here])

        # Next, create the top level envelope definition and populate it.
        envelope_definition = EnvelopeDefinition(email_subject="Please sign this document sent from the Python SDK", documents=[document], recipients=Recipients(signers=[signer]), status="sent")

        return envelope_definition
    
    @staticmethod
    def get_workflow(args):
        """Retrieve the workflow id"""
        try:
            api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])

            workflow_details = AccountsApi(api_client)
            workflow_response = workflow_details.get_account_identity_verification(account_id=args["account_id"])

            if workflow_response.identity_verification:
                for workflow in workflow_response.identity_verification:
                    if workflow.default_name == "SMS for access & signatures":
                        session['workflow_id'] = workflow.workflow_id

                return session['workflow_id']

            else:
                return None

        except ApiException as err:
            return process_error(err)