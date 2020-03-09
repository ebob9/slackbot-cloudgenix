import logging
import sys
import os
import json
import re
import inspect
import random

from fuzzywuzzy import fuzz, process
import cloudgenix
import cloudgenix_idname

from slackbot.bot import respond_to, listen_to, default_reply
from slackbot.utils import download_file, create_tmp_file
import slackbot_cloudgenix.getevents
from .sites import showsites
from .topology import render_topology, render_site_app_paths, render_site_media_paths
from .apps import get_appdefs
from .helpers import update_id2n_dicts_delta, update_id2n_dicts_slow
from .health import site_health_header, site_health_alarms, site_health_alerts, site_health_links, site_health_dns, \
    site_health_cloud

logger = logging.getLogger(__name__)

# Globals
CGX_API_ERROR_MSG = "Sorry, having problems communicating with CloudGenix. Please contact my support."
GOOD_RESPONSE = 'white_check_mark'
BAD_RESPONSE = 'x'
POOR_RESPONSE = 'red_circle'
NO_RESPONSE = 'white_circle'
BEYOND_GOOD_RESPONSE = 'large_blue_circle'
WARNING_RESPONSE = 'warning'

# Check config file for AUTH_TOKEN, Controller, ssl_verify, add in cwd.
sys.path.append(os.getcwd())
try:
    from slackbot_settings import CLOUDGENIX_AUTH_TOKEN
except ImportError:
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes priority.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None
try:
    from slackbot_settings import CLOUDGENIX_CONTROLLER
except ImportError:
    CLOUDGENIX_CONTROLLER = None

try:
    from slackbot_settings import CLOUDGENIX_SSL_VERIFY
except ImportError:
    CLOUDGENIX_SSL_VERIFY = None

try:
    from slackbot_settings import DEFAULT_REPLY
except ImportError:
    DEFAULT_REPLY = "Hello, my configuration is missing DEFAULT_REPLY! Please send Help! Beep, Boop!"

try:
    from slackbot_settings import DEBUG_LEVEL
except ImportError:
    DEBUG_LEVEL = 0

if DEBUG_LEVEL == 1:
    logging.basicConfig(level=logging.INFO)
    clilogger = logging.getLogger()
    clilogger.setLevel(logging.INFO)
elif DEBUG_LEVEL >= 2:
    logging.basicConfig(level=logging.DEBUG)
    clilogger = logging.getLogger()
    clilogger.setLevel(logging.DEBUG)
else:
    logging.basicConfig(level=logging.WARNING)
    clilogger = logging.getLogger()
    clilogger.setLevel(logging.WARNING)

# ok. try to login.
if CLOUDGENIX_SSL_VERIFY is None and CLOUDGENIX_CONTROLLER is None:
    # Normal login
    sdk = cloudgenix.API()
elif CLOUDGENIX_SSL_VERIFY is None:
    # custom controller
    sdk = cloudgenix.API(controller=CLOUDGENIX_CONTROLLER)
elif CLOUDGENIX_CONTROLLER is None:
    # custom SSL Verification setting.
    sdk = cloudgenix.API(ssl_verify=CLOUDGENIX_SSL_VERIFY)
else:
    # custom everything.
    sdk = cloudgenix.API(controller=CLOUDGENIX_CONTROLLER, ssl_verify=CLOUDGENIX_SSL_VERIFY)

# actual api token use
token_login = sdk.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
# if login fails, sdk.tenant_id will be None.


# start cloudgenix_idname instance to cache responses.
idname = cloudgenix_idname.CloudGenixIDName(sdk)

logger.warning("Loading CloudGenix ID->Name cache at startup, this may take several minutes..")
global_id2n = update_id2n_dicts_slow(idname)
logger.warning("ID->Name cache successfully updated.")

class CgxParseforRaw(object):
    """
    Class to allow using raw
    """
    Slacker = None
    SlackClient = None
    self_data = None
    self_id = None
    message_body = None
    channel_id = None
    source_team_id = None
    user_team_id = None
    user_id = None
    team_id = None
    event_ts = None
    ts = None

    def __init__(self, message):
        """
        Parse message and populate the object with needed items.
        :param message: Slackbot Messsage.
        """
        self.SlackClient = message._client
        self.Slacker = self.SlackClient.webapi
        self.self_data = message._client.login_data.get('self', {})
        self.self_id = self.self_data.get('id')
        self.message_body = message._body
        self.channel_id = self.message_body.get('channel')
        self.source_team_id = self.message_body.get('source_team')
        self.user_team_id = self.message_body.get('user_team')
        self.user_id = self.message_body.get('user')
        self.team_id = self.message_body.get('team')
        self.event_ts = self.message_body.get('event_ts')
        self.ts = self.message_body.get('ts')


def log_message_env(message):
    """
    log message details for debugging
    :param message: SlackMessage object
    :return:
    """
    try:
        user = message.channel._client.users.get(message.body.get('user'), 'UNKNOWN USER')
        d_display_name = user.get('real_name', 'UNKNOWN')
    except KeyError as e:
        # some times user does not work. Put default messages here.
        d_display_name = "NO USERNAME ({0})".format(str(e))

    try:
        channel = message.channel._client.channels.get(message.body.get('channel', 'UNKNOWN CHANNEL'),
                                                       'UNKNOWN CHANNEL')
        d_channel_name = channel.get('name', '<Private Message>')
    except KeyError as e:
        # some times channel does not work. Put default messages here.
        d_channel_name = "NO CHANNEL({0})".format(str(e))

    try:
        d_message_txt = message.body.get('text', 'NON PARSABLE MESSAGE DETECTED.')
    except KeyError as e:
        # some times message does not work. Put default messages here.
        d_message_txt = "NO MESSAGE({0})".format(str(e))

    try:
        d_calling_function = inspect.currentframe().f_back.f_code.co_name
    except KeyError as e:
        # some times message does not work. Put default messages here.
        d_calling_function = "UNABLE TO GET FUNCTION({0})".format(str(e))

    logger.debug("FUNCTION: '{0}'".format(d_calling_function))
    logger.debug("CHANNEL: '{0}'".format(d_channel_name))
    logger.debug("USER   : '{0}'".format(d_display_name))
    logger.debug("MESSAGE: '{0}'".format(d_message_txt))

    return


# @respond_to('hi', re.IGNORECASE)
# def hi(message):
#     message.reply('I can understand hi or HI!')
#     # react with thumb up emoji
#     message.react('+1')


@respond_to('help', re.IGNORECASE)
def help(message):
    log_message_env(message)
    message.react(GOOD_RESPONSE)
    message_text = 'I can take the following commands (for now):\n' \
                   '*CloudGenix Commands:*\n' \
                   '"Show sites"\n' \
                   '"Show site <site name>"\n' \
                   '"Show paths of <site name>"\n' \
                   '"Show health <site name>"\n' \
                   '"Show applications"\n' \
                   '"Show application <app name>"\n' \
                   '"what region"\n' \
                   '"what tenant or what customer"\n' \
                   '"you there or you alive"\n' \
                   '"Show media <app name> at <site name>"\n' \
                   '"show alarms <all | code_list>"\n' \
                   '"Show site-alarms <site name>"\n'
    message.reply(message_text, in_thread=True)


# @respond_to('I love you')
# def love(message):
#     message.reply('I love you too!')

# attempt to show all alarms for all sites or a list of alarm codes across all sites
# @mike.korenbaum@cloudgenix.com
#
@respond_to('show alarms (.*)', re.IGNORECASE)
def show_alarms(message, code_list):
    log_message_env(message)
    if sdk.tenant_id:
        # get alarms
        message.react(GOOD_RESPONSE)
        if code_list == "all":
            ec = []
            message.reply("Retrieving all alarms")
            output = (getevents.run(sdk, ec, 10, global_id2n))

            # Too large for slack, attach as text message
            with create_tmp_file(content=output.encode('ascii')) as tmpf:
                message.channel.upload_file('Alarms.csv', tmpf, '')


        else:
            message.reply("This is the code_list: ({0}).".format(code_list))
    else:
        message.react(BAD_RESPONSE)
        message.reply(CGX_API_ERROR_MSG)


# attempt to show all alarms for a particular site
# @mike.korenbaum@cloudgenix.com
#
@respond_to('show site-alarms (.*)', re.IGNORECASE)
def show_site_alarms(message, site_string):
    log_message_env(message)
    if sdk.tenant_id:
        # get list of sites.
        sites_n2id = idname.generate_sites_map(key_val='name', value_val='id')
        name_list = sites_n2id.keys()

        # fuzzy match
        choice, percent = process.extractOne(site_string, name_list)
        # perfect match, just get..
        if percent == 100:
            message.react(GOOD_RESPONSE)
            # message.reply("```" + str(showsites(sites_n2id[choice], sdk, global_id2n)) + "```")
            message.reply("100% match found...".format(choice))
        # good guess match..
        elif percent > 50:
            message.react(GOOD_RESPONSE)
            message.reply("I think you meant *{0}*, looking that up..".format(choice))
            # message.send("```" + str(showsites(sites_n2id[choice], sdk, global_id2n)) + "```")
        # not even close..
        else:
            message.react(BAD_RESPONSE)
            message.reply("I couldn't find a site that matched what you asked for ({0}). Try asking me about "
                          "\"What sites are there?\".".format(site_string))
    else:
        message.react(BAD_RESPONSE)
        message.reply(CGX_API_ERROR_MSG)

##
# Adding show health info from Karl's script
##

@respond_to('show health (.*)', re.IGNORECASE)
def show_site_health(message, site_string):
    log_message_env(message)
    if sdk.tenant_id:
        # get list of sites.
        sites_n2id = idname.generate_sites_map(key_val='name', value_val='id')
        name_list = sites_n2id.keys()

        # fuzzy match
        choice, percent = process.extractOne(site_string, name_list)
        # perfect match, just get..
        if percent > 50:
            message.react(GOOD_RESPONSE)
            # if not 100%
            if percent != 100:
                message.reply("I think you meant *{0}*, looking that up..".format(choice))
            raw_api = CgxParseforRaw(message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(site_health_header(sites_n2id[choice], sdk, idname))
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(site_health_alarms(sites_n2id[choice], sdk, idname))
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(site_health_alerts(sites_n2id[choice], sdk, idname))
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            # links gives back 3 blocks message
            blocks1, blocks2, blocks3 = site_health_links(sites_n2id[choice], sdk, idname)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(blocks1)
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(blocks2)
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(blocks3)
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(site_health_dns(sites_n2id[choice], sdk, idname))
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
            constructed_raw_message = {
                "channel": raw_api.channel_id,
                "as_user": raw_api.self_id,
                "blocks": json.dumps(site_health_cloud(sites_n2id[choice], sdk, idname))
            }
            raw_api.Slacker.chat.post('chat.postMessage', data=constructed_raw_message)
        # not even close..
        else:
            message.react(BAD_RESPONSE)
            message.reply("I couldn't find a site that matched what you asked for ({0}). Try asking me about "
                          "\"What sites are there?\".".format(site_string))
    else:
        message.react(BAD_RESPONSE)
        message.reply(CGX_API_ERROR_MSG)


@respond_to('show site (.*)', re.IGNORECASE)
def show_site(message, site_string):
    log_message_env(message)
    if sdk.tenant_id:
        # get list of sites.
        sites_n2id = idname.generate_sites_map(key_val='name', value_val='id')
        name_list = sites_n2id.keys()

        # fuzzy match
        choice, percent = process.extractOne(site_string, name_list)
        # perfect match, just get..
        if percent == 100:
            message.react(GOOD_RESPONSE)
            message.reply("```" + str(showsites(sites_n2id[choice], sdk, global_id2n)) + "```")
        # good guess match..
        elif percent > 50:
            message.react(GOOD_RESPONSE)
            message.reply("I think you meant *{0}*, looking that up..".format(choice))
            message.send("```" + str(showsites(sites_n2id[choice], sdk, global_id2n)) + "```")
        # not even close..
        else:
            message.react(BAD_RESPONSE)
            message.reply("I couldn't find a site that matched what you asked for ({0}). Try asking me about "
                          "\"What sites are there?\".".format(site_string))
    else:
        message.react(BAD_RESPONSE)
        message.reply(CGX_API_ERROR_MSG)


@respond_to('state (for|of) (.*)', re.IGNORECASE)
@respond_to('status (for|of) (.*)', re.IGNORECASE)
@respond_to('paths (for|of) (.*)', re.IGNORECASE)
@respond_to('links (for|of) (.*)', re.IGNORECASE)
def stats_site(message, discard_middle, site_string):
    log_message_env(message)
    if sdk.tenant_id:
        # get list of sites.
        sites_n2id = idname.generate_sites_map(key_val='name', value_val='id')
        name_list = sites_n2id.keys()
        site_id = None
        # fuzzy match
        choice, percent = process.extractOne(site_string, name_list)
        # perfect match, just get..
        if percent == 100:
            message.react(GOOD_RESPONSE)
            site_id = sites_n2id[choice]
        # good guess match..
        elif percent > 50:
            message.react(GOOD_RESPONSE)
            message.reply("I think you meant *{0}*, looking that up..".format(choice))
            site_id = sites_n2id[choice]

        # not even close..
        else:
            message.react(BAD_RESPONSE)
            message.reply("I couldn't find a site that matched what you asked for ({0}). Try asking me about "
                          "\"What sites are there?\".".format(site_string))
            return

        # message.send("```" + str(get_bw_metrics(site_id, None, cli_vars=cli_vars)) + "```")
        # attachments = [
        #     {
        #         'pretext': "VPN",
        #         'text': 'Link ABC',
        #         'color': 'good'
        #     },
        #     {
        #         'text': 'Link DEF',
        #         'color': 'good'
        #     },
        #     {
        #         'text': 'Link GHI',
        #         'color': 'danger'
        #     },
        #     {
        #         'pretext': "Internet",
        #         'text': 'Link JKL',
        #         'color': 'warning'
        #     },
        #     {
        #         'text': get_topology(site_id, cli_vars=cli_vars),
        #         'color': '#888888'
        #     },
        # ]
        message.send_webapi('', json.dumps(render_topology(site_id, sdk, global_id2n)))
        # message.send_webapi('', get_bw_metrics(site_id, None, cli_vars=cli_vars))

    else:
        message.react(BAD_RESPONSE)
        message.reply(CGX_API_ERROR_MSG)


@respond_to('sites', re.IGNORECASE)
def sites(message):
    log_message_env(message)
    if sdk.tenant_id:
        output_message = showsites(None, sdk, global_id2n)
        message.react(GOOD_RESPONSE)
        message.reply("```" + str(output_message) + "```")
        #
        # attachments = [
        #     {
        #         "text": "```" + str(output_message) + "```",
        #         "color": "#FFFFFF",
        #         "mrkdwn_in": ["text"]
        #     }
        # ]
        # message.send_webapi('', json.dumps(attachments))
        # # message.send("```" + str(showsites(cli_vars=cli_vars)) + "```")
    else:
        message.react(BAD_RESPONSE)
        message.reply(CGX_API_ERROR_MSG)

@respond_to('show media (.*) at (.*)', re.IGNORECASE)
def showmedia_site(message, app_string, site_string):
    log_message_env(message)
    if sdk.tenant_id:
        # get list of apps.
        appdef_n2id = idname.generate_appdefs_map(key_val='display_name', value_val='id')
        app_list = appdef_n2id.keys()

        # get list of sites.
        sites_n2id = idname.generate_sites_map(key_val='name', value_val='id')
        site_list = sites_n2id.keys()

        # fuzzy match
        app_choice, app_percent = process.extractOne(app_string, app_list)
        site_choice, site_percent = process.extractOne(site_string, site_list)
        # perfect match, just get..
        if app_percent == 100 and site_percent == 100:
            message.react(GOOD_RESPONSE)
            app_id = appdef_n2id[app_choice]
            site_id = sites_n2id[site_choice]

        # good guess match..
        elif app_percent > 50 and site_percent > 50:
            message.react(GOOD_RESPONSE)
            message.reply("I think you meant *{0}* at *{1}*, looking that up..".format(app_choice, site_choice))
            app_id = appdef_n2id[app_choice]
            site_id = sites_n2id[site_choice]

        # if only one is good, or both are bad.
        else:
            message.react(BAD_RESPONSE)
            if app_percent <= 50:
                message.reply("I couldn't find a media application that matched what you asked for ({0}). "
                              "Try asking me about \"What apps are there?\".".format(app_string))
            if site_percent <= 50:
                message.reply("I couldn't find a site that matched what you asked for ({0}). "
                              "Try asking me about \"What sites are there?\".".format(site_string))
            return

        # Figure out the links/do all the work now.
        attachments = render_site_media_paths(app_id, site_id, sdk, global_id2n)

        # check if successful, add title
        if attachments[0].get('pretext') != "Sorry, couldn't query the media application info for this site at the " \
                                            "moment. Please try later.":
            message.reply("*Path status for {0} at {1}:*".format(app_choice, site_choice))

        # now, send it
        message.send_webapi('', json.dumps(attachments))

    else:
        message.react(BAD_RESPONSE)
        message.send(CGX_API_ERROR_MSG)


@respond_to('show app (.*) at (.*)', re.IGNORECASE)
@respond_to('show application (.*) at (.*)', re.IGNORECASE)
def showapp_site(message, app_string, site_string):
    log_message_env(message)
    if sdk.tenant_id:
        # get list of apps.
        appdef_n2id = idname.generate_appdefs_map(key_val='display_name', value_val='id')
        app_list = appdef_n2id.keys()

        # get list of sites.
        sites_n2id = idname.generate_sites_map(key_val='name', value_val='id')
        site_list = sites_n2id.keys()

        # fuzzy match
        app_choice, app_percent = process.extractOne(app_string, app_list)
        site_choice, site_percent = process.extractOne(site_string, site_list)
        # perfect match, just get..
        if app_percent == 100 and site_percent == 100:
            message.react(GOOD_RESPONSE)
            app_id = appdef_n2id[app_choice]
            site_id = sites_n2id[site_choice]

        # good guess match..
        elif app_percent > 50 and site_percent > 50:
            message.react(GOOD_RESPONSE)
            message.reply("I think you meant *{0}* at *{1}*, looking that up..".format(app_choice, site_choice))
            app_id = appdef_n2id[app_choice]
            site_id = sites_n2id[site_choice]

        # if only one is good, or both are bad.
        else:
            message.react(BAD_RESPONSE)
            if app_percent <= 50:
                message.reply("I couldn't find an application that matched what you asked for ({0}). "
                              "Try asking me about \"What apps are there?\".".format(app_string))
            if site_percent <= 50:
                message.reply("I couldn't find a site that matched what you asked for ({0}). "
                              "Try asking me about \"What sites are there?\".".format(site_string))
            return

        # Figure out the links/do all the work now.
        attachments = render_site_app_paths(app_id, site_id, sdk, global_id2n)

        # check if successful, add title
        if attachments[0].get('pretext') != "Sorry, couldn't query the application info for this site at the moment. " \
                                            "Please try later.":
            message.reply("*Path status for {0} at {1}:*".format(app_choice, site_choice))

        # now, send it
        message.send_webapi('', json.dumps(attachments))

    else:
        message.react(BAD_RESPONSE)
        message.send(CGX_API_ERROR_MSG)


@respond_to('show app (.*)', re.IGNORECASE)
@respond_to('show application (.*)', re.IGNORECASE)
def showapp(message, app_string):
    log_message_env(message)
    # check if " at " in the command, early return if so - we want this denied.
    checkstr = " at "
    if app_string.lower().find(checkstr) > -1:
        # return silently if " at " in app string.
        return
    if sdk.tenant_id:
        # get list of apps.
        appdef_n2id = idname.generate_appdefs_map(key_val='display_name', value_val='id')
        app_list = appdef_n2id.keys()
        # fuzzy match
        choice, percent = process.extractOne(app_string, app_list)
        # perfect match, just get..
        if percent == 100:
            message.react(GOOD_RESPONSE)
            message.reply("```" + str(get_appdefs(sdk, global_id2n, passed_detail=appdef_n2id[choice])) + "```")
        # good guess match..
        elif percent > 50:
            message.react(GOOD_RESPONSE)
            message.reply("I think you meant *{0}*, looking that up..".format(choice))
            message.send("```" + str(get_appdefs(sdk, global_id2n, passed_detail=appdef_n2id[choice])) + "```")
        # not even close..
        else:
            message.react(BAD_RESPONSE)
            message.reply("I couldn't find an application that matched what you asked for ({0}). "
                          "Try asking me about \"What apps are there?\".".format(app_string))
    else:
        message.react(BAD_RESPONSE)
        message.send(CGX_API_ERROR_MSG)


@respond_to('apps', re.IGNORECASE)
@respond_to('applications', re.IGNORECASE)
def apps(message):
    log_message_env(message)
    if sdk.tenant_id:
        message.react(GOOD_RESPONSE)
        output = str(get_appdefs(sdk=sdk, idname=idname))

        # Too large for slack, attach as text message
        with create_tmp_file(content=output.encode('ascii')) as tmpf:
            message.channel.upload_file('Application Definitions.txt', tmpf, '')

            # output_list = output.split('\n')
        # attachments = []
        # for line in output_list:
        #
        #     attachments.append({
        #                 "text": "```" + line + "```",
        #                 "color": "#FFFFFF",
        #                 "mrkdwn_in": ["text"]
        #             })
        # message.send_webapi('', json.dumps(attachments))
        # message.send("```" + str(showsites(sdk_vars=sdk_vars)) + "```")
    else:
        message.react(BAD_RESPONSE)
        message.send(CGX_API_ERROR_MSG)


@respond_to('what tenant', re.IGNORECASE)
@respond_to('what customer', re.IGNORECASE)
def customer(message):
    log_message_env(message)
    if sdk.tenant_id:
        message.react(GOOD_RESPONSE)
        message.send("I'm currently examining the \"" + str(sdk.tenant_name) + "\" Network.")

    else:
        message.react(BAD_RESPONSE)
        message.send(CGX_API_ERROR_MSG)


@respond_to('what region', re.IGNORECASE)
def customer(message):
    log_message_env(message)
    if sdk.tenant_id:
        message.react(GOOD_RESPONSE)
        message.send("I'm currently examining a tenant in region \"" + str(sdk.controller_region) + "\" .")

    else:
        message.react(BAD_RESPONSE)
        message.send(CGX_API_ERROR_MSG)




@respond_to('you there', re.IGNORECASE)
@respond_to('you alive', re.IGNORECASE)
def working(message):
    log_message_env(message)
    message.reply('I am alive.', in_thread=True)
    for attr, value in message.__dict__.items():
        print(attr, cloudgenix.jdout(value))
    for attr, value in message._client.__dict__.items():
        print(attr, cloudgenix.jdout(value))
    for attr, value in message._plugins.__dict__.items():
        print(attr, cloudgenix.jdout(value))
    # raw_send = message._client
    # channel = message._body.get('channel')
    # user_id = message._client.login_data.get('self', {}).get('id')

    raw_api = CgxParseforRaw(message)

    print(f"USER-ID: {raw_api.self_id}")

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "You have a new request:\n*<fakeLink.toEmployeeProfile.com|Fred Enriquez - New device request>*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Type:*\nComputer (laptop)"
                },
                {
                    "type": "mrkdwn",
                    "text": "*When:*\nSubmitted Aut 10"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Last Update:*\nMar 10, 2015 (3 years, 5 months)"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Reason:*\nAll vowel keys aren't working."
                },
                {
                    "type": "mrkdwn",
                    "text": "*Specs:*\n\"Cheetah Pro 15\" - Fast, really fast\""
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Approve"
                    },
                    "style": "primary",
                    "value": "click_me_123"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Deny"
                    },
                    "style": "danger",
                    "value": "click_me_123"
                }
            ]
        }
    ]

    blocks2 = [
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "title",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "What do you want to ask of the world?"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Title"
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "multi_channels_select",
                    "action_id": "channels",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Where should the poll be sent?"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Channel(s)"
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "option_1",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "First option"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Option 1"
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "option_2",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "How many options do they need, really?"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Option 2"
                }
            }
        ]
    constructed_message1 = {
        "channel": raw_api.channel_id,
        "as_user": raw_api.self_id,
        "blocks": json.dumps(blocks)
    }

    constructed_message2 = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "My App",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel",
            "emoji": True
        },
        "blocks": json.dumps(blocks2)
    }

    raw_api.Slacker.chat.post('chat.postMessage', data=constructed_message1)

    choice = random.randrange(10)
    if choice <= 5:
        message.react('zombie')
    else:
        message.react('female_zombie')


@default_reply()
def default_replies(message):
    log_message_env(message)
    message.react(BAD_RESPONSE)
    message.reply(DEFAULT_REPLY)
