# -*- coding: UTF-8 -*-
# standard modules
import logging

# helpers
from .helpers import table_output, domain_to_idna, idna_to_domain, hierarchy_output

logger = logging.getLogger(__name__)


# def filter_lookup_table_id(idname):
#
#     return_dict = {}
#     return_dict.update(idname.generate_localprefixfilters_map())
#     return_dict.update(idname.generate_globalprefixfilters_map())
#     return return_dict


def get_appdefs(sdk, idname, passed_detail=None):
    logger.info('appdefinitionsv2 start:')

    if not passed_detail:
        logger.info('No ID/name passed')
        appdef_resp = sdk.get.appdefs()
        status = appdef_resp.cgx_status
        app_defs = appdef_resp.cgx_content

        # output the app_def info
        if status and app_defs and app_defs.get('items', None):

            return table_output(app_defs['items'], ['id$', '^_', '^app_tag_id$', 'conn_idle_timeout', 'path_affinity',
                                                    'udp_rules', 'tcp_rules', 'ingress_traffic_pct',
                                                    'transfer_type', 'domains', 'abbreviation', 'aggregate_flows',
                                                    'order_number', 'overrides_allowed', 'system_app_overridden',
                                                    'is_deprecated', 'use_parentapp_network_policy',
                                                    'app_unreachability_detection', 'network_scan_application',
                                                    'ip_rules', 'session_timeout'],
                                ['display_name', 'app_type', 'category'])
        else:
            return "Sorry, couldn't retrieve the Applications List."

    else:
        logger.info('ID/name passed: {0}'.format(passed_detail))
        return_val = ""

        # create a list in items key for output.
        appdef_resp = sdk.get.appdefs()
        status = appdef_resp.cgx_status
        app_defs = appdef_resp.cgx_content

        # output the app_def info
        app_get = {}
        if status and app_defs:
            for app_def in app_defs['items']:
                if app_def['id'] == passed_detail:
                    # print "found app.... %s" % passed_detail
                    app_get = dict(app_def)

        else:
            return "Sorry, couldn't retrieve the Applications List."

        if app_get:
            tcp_rules_dict = app_get.pop('tcp_rules')
            udp_rules_dict = app_get.pop('udp_rules')
            ip_rules_dict = app_get.pop('ip_rules')

            # check for IDNA domains, and supplement output
            current_domains = app_get.get('domains', [])
            if current_domains or current_domains == [""]:
                idna_compliant_domains = []
                for domain in current_domains:
                    # check if domain in unicode = IDNA decoded domain, if so - non IDNA domain.
                    idna_decoded_entry = idna_to_domain(domain)
                    if domain.encode('utf_8') == idna_decoded_entry:
                        idna_compliant_domains.append(domain)
                    else:
                        idna_compliant_domains.append(idna_decoded_entry + '(' + str(domain) + ')')
                app_get['domains'] = idna_compliant_domains

            return_val += hierarchy_output(app_get, ['^_'], ['display_name', 'id'])

            filter_lookup = idname
            rule_list = []
            tcp_rules = False
            udp_rules = False
            ip_rules = False

            for idx, rule in enumerate(tcp_rules_dict or []):
                sp = rule.get('server_port')
                cp = rule.get('client_port')
                dscp = rule.get('dscp')
                sf = [filter_lookup.get(x, x) for x in rule.get('server_filters') or []]
                cf = [filter_lookup.get(x, x) for x in rule.get('client_filters') or []]
                rule_info = {}
                rule_info['TCP Rule No'] = idx
                rule_info['Server Port'] = None if not sp else '-'.join([str(sp['start']), str(sp['end'])])
                rule_info['Client Port'] = None if not cp else '-'.join([str(cp['start']), str(cp['end'])])
                rule_info['Server Filters'] = None if not sf else ','.join(sf)
                rule_info['Client Filters'] = None if not cf else ','.join(cf)
                rule_info['DSCP'] = None if not dscp else dscp
                rule_list.append(rule_info)
            if rule_list:
                tcp_rules = True
                return_val += table_output(rule_list, [],
                                           ['TCP Rule No', 'Server Port', 'Client Port', 'Server Filters',
                                            'Client Filters'])
            rule_list = []
            for idx, rule in enumerate(udp_rules_dict or []):
                up = rule.get('udp_port')
                uf = [filter_lookup.get(x, x) for x in rule.get('udp_filters') or []]
                dscp = rule.get('dscp')
                rule_info = {}
                rule_info['UDP Rule No'] = idx
                rule_info['Port'] = None if not up else '-'.join([str(up['start']), str(up['end'])])
                rule_info['Filters'] = None if not uf else ','.join(uf)
                rule_info['DSCP'] = None if not dscp else dscp
                rule_list.append(rule_info)
            if rule_list:
                udp_rules = True
                # see if we need to add lf
                if tcp_rules:
                    return_val += '\n'
                return_val += table_output(rule_list, [],
                                           ['UDP Rule No', 'Port', 'Filters'])

            rule_list = []
            for idx, rule in enumerate(ip_rules_dict or []):
                ip_proto = rule.get('protocol')
                sf = [filter_lookup.get(x, x) for x in rule.get('src_filters') or []]
                df = [filter_lookup.get(x, x) for x in rule.get('dest_filters') or []]
                dscp = rule.get('dscp')
                rule_info = {}
                rule_info['IP Rule No'] = idx
                rule_info['Protocol'] = None if not ip_proto else ip_proto
                rule_info['Source Filters'] = None if not sf else ','.join(sf)
                rule_info['Destination Filters'] = None if not df else ','.join(df)
                rule_info['DSCP'] = None if not dscp else dscp
                rule_list.append(rule_info)
            if rule_list:
                ip_rules = True
                # see if we need to add lf
                if udp_rules:
                    return_val += '\n'
                return_val += table_output(rule_list, [],
                                           ['IP Rule No', 'Protocol', 'Source Filters', 'Destination Filters'])

        else:
            return "Sorry, couldn't retrieve the Applications you requested."

        return return_val
