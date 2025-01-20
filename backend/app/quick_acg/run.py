#!flask/bin/python
from app.quick_acg.quick_acg_app import quick_acg_app
from flask_session import Session
import os
from ..ds_config import DS_CONFIG

quick_acg_app.config["QUICK_ACG"] = True
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

if os.environ.get("DEBUG", False) == "True":
    quick_acg_app.config["DEBUG"] = True
    quick_acg_app.config['SESSION_TYPE'] = 'filesystem'
    sess = Session()
    sess.init_app(quick_acg_app)
    port = int(os.environ.get("PORT", 3000))
    DS_CONFIG["doc_pdf"] = "submitted_file.pdf"
    quick_acg_app.run(host="localhost", port=3000, debug=True)
else:
    quick_acg_app.config['SESSION_TYPE'] = 'filesystem'
    sess = Session()
    sess.init_app(quick_acg_app)
    DS_CONFIG["doc_pdf"] = "submitted_file.pdf"
    quick_acg_app.run(host="localhost", port=3000, debug=True)