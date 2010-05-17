"""Setup the SFLvault application"""
import logging

from paste.deploy import appconfig
from pylons import config
from datetime import datetime, timedelta

from sflvault.config.environment import load_environment

log = logging.getLogger(__name__)

def setup_config(command, filename, section, vars):
    """Place any commands to setup sflvault here"""
    conf = appconfig('config:' + filename)
    load_environment(conf.global_conf, conf.local_conf)

    from sflvault import model
    log.info("Creating tables")
    model.meta.metadata.create_all(bind=model.meta.engine)
    ## Add default user 'admin' with 5 minutes for the client to call "sflvault setup"
    if model.query(model.User).filter_by(username='admin').first():
        log.info("User 'admin' already exists, skipping insertion of admin user.")
    else:
        u = model.User()
        u.waiting_setup = datetime.now() + timedelta(0, 900)
        u.username = u'admin'
        u.created_time = datetime.now()
        u.is_admin = True

        model.meta.Session.add(u)        
        model.meta.Session.commit()

        log.info("Added 'admin' user, you have 15 minutes to setup from your client")
    
    log.info("Successfully setup")
