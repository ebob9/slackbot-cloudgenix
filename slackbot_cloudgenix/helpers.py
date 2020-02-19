#!/usr/bin/env python

#
# CLI Module Helper functions
# (c) 2014 CloudGenix
# Aaron Edwards <aaron@cloudgenix.com>
#

from collections import OrderedDict
import logging
import re
import datetime
import tabulate
import idna
import cloudgenix

# Logging
logger = logging.getLogger(__name__)

# Dictionary of keys to pretty name
PRETTYNAMES = {
    '': ' ',  # Needed in cases where a priorty key is blank. Otherwise will not be added to right spot.
    'admin_state': 'Admin State',
    'name': 'Name',
    'description': 'Description',
    'element_cluster_role': 'Element Role',
    'site_mode': 'Site Mode',
    'address': 'Address',
    'ipv4_addrs': 'IP Addresses',
    'vlan_id': 'VLAN ID',
    'type': 'Type',
    'protocol': 'Protocol',
    'local_as_num': 'Local ASN',
    'remote_as_num': 'Remote ASN',
    'peer_ip': 'Peer IP',
    'app_name': 'Application Name',
    'category': 'Category',
    'display_name': 'Application Name',
    'app_tag_id': 'CloudGenix App ID',
    'created_on_utc': 'Created on (UTC)',
    'state': 'State',
    'role': 'Role',
    'sub_type': 'Sub-type',
    'status': 'Status',
    'source_wan_network': 'Source WAN Network',
    'target_wan_network': 'Destination WAN Network',
    'priority_num': 'Priority',
    'model_name': 'Model',
    'software_version': 'Software Version',
    'serial_number': 'Serial Number',
    'connected': 'Connected',
    'id': 'ID',
    'site_id': 'Site ID',
    'operational_state': 'Operational State',
    'mtu': 'MTU',
    'used_for': 'Network Type',
    'admin_up': 'Admin State',
    'ethernet_port': 'Speed / Duplex',
    'in_use': 'In Use',
    'default_policy': 'is Default Policy',
    'lan_network_ids': 'LAN Network IDs',
    'wan_network_ids': 'WAN Network IDs',
    'policy_set_ids': 'Policy Set IDs',
    'location': 'Location',
    'hw_id': 'Hardware ID',
    'DIRECT_PRIVATE_WAN': 'Direct Private WAN',
    'DIRECT_PUBLIC_WAN': 'Direct Internet',
    'VPN_ON_PUBLIC_WAN': 'VPN over Internet',
    'business_priority_name': 'Business Priority Name',
    'post_code': 'Postal Code',
    'city': 'City',
    'street': 'Street',
    'street2': 'Street 2',
    'country': 'Country',
    'site_paths_allowed': 'Allowed WAN Paths',
    'app_def_name': 'Application Definition',
    'wn_name': 'WAN Network',
    'wan_path_type': 'WAN Path',
    'app_id': 'Application ID',
    'site_state': 'Site State',
    'element_id': 'Element ID',
    'interface_id': 'Interface ID',
    'rx_packets': 'Input Packets',
    'rx_bytes': 'Input Bytes',
    'rx_errors': 'Input Errors',
    'rx_crc_errors': 'Input CRC Errors',
    'rx_frame_errors': 'Input Frame Errors',
    'rx_dropped': 'Input Drops',
    'rx_fifo_errors': 'Input FIFO Errors',
    'rx_compressed': 'Input Compressed',
    'tx_packets': 'Output Packets',
    'tx_bytes': 'Output Bytes',
    'tx_errors': 'Output Errors',
    'tx_crc_errors': 'Output CRC Errors',
    'tx_frame_errors': 'Output Frame Errors',
    'tx_dropped': 'Output Drops',
    'tx_fifo_errors': 'Output FIFO Errors',
    'tx_compressed': 'Output Compressed',
    'multicast': 'Multicast',
    'start_time': 'Start Time',
    'end_time': 'End Time',
    'tx_carrier_errors': 'Output Link Errors',
    'collisions': 'Collisions',
    'peer_id': 'Peer ID',
    'rx_bgp_pkts': 'Input BGP packets',
    'rx_bgp_open_pkts': 'Input BGP Open packets',
    'rx_bgp_update_pkts': 'Input BGP Update packets',
    'rx_bgp_notifications_pkts': 'Input BGP Notify packets',
    'rx_bgp_keepalive_pkts': 'Input BGP Keepalive packets',
    'tx_bgp_pkts': 'Output BGP packets',
    'tx_bgp_open_pkts': 'Output BGP Open packets',
    'tx_bgp_update_pkts': 'Output BGP Update packets',
    'tx_bgp_notifications_pkts': 'Output BGP Notify packets',
    'tx_bgp_keepalive_pkts': 'Output BGP Keepalive packets',
    'bgp_conn_established_count': 'BGP Connection Established count',
    'bgp_conn_dropped_count': 'BGP Dropped Connection count',
    'bgp_accepted_prefix_count': 'BGP Accepted Prefix count',
    'bw_utilization': 'Min BW Guarantee %',
    'path_id': 'Path ID',
    'anynet_link_id': 'vLink ID',
    'packets_ingress': 'Input Packets',
    'packets_egress': 'Output Packets',
    'bytes_ingress': 'Input Bytes',
    'bytes_egress': 'Output Bytes',
    'peer_config': 'Peer Config',
    'bgp_config': 'BGP Config',
    'peer_status': 'Peer Status',
    'reachable_prefix_set': 'Prefixes Received',
    'advertised_prefix_set': 'Advertised Prefixes',
    'uptime': 'Uptime',
    'email': 'Email',
    'email_validated': 'Email Validated',
    'disabled': 'Disabled',
    'enabled': 'Enabled',
    'unknown': 'Unknown',
    'first_name': 'First Name',
    'tenant_id': 'Tenant ID',
    'created_by_operator_id': 'Created By',
    'updated_on_utc': 'Updated on (UTC)',
    'inactive': 'Inactive',
    'updated_by_operator_id': 'Updated By',
    'canonical_name': 'Canonical Name',
    'em_element_id': 'Assigned to Element',
    'image_version': 'Inital Image Version',
    'machine_state': 'Machine State',
    'sl_no': 'Serial Number',
    'right_site_name': 'Site1',
    'left_site_name': 'Site2',
    'link_up': 'Link Up',
    'right_element_id': 'Element1',
    'left_element_id': 'Element2',
    'right_elem_if_name': 'If1',
    'left_elem_if_name': 'If2',
    'allowed_roles': 'Allowed Roles',
    'business_priorities': 'Business Priorities',
    'bw_share': 'Bandwidth Contention Shares',
    'app_def_id': 'Application Definition ID',
    'network_context_id': 'Network Context ID',
    'network_context_name': 'Network Context',
    'hub_element_id': 'Datacenter Element ID',
    'load_factors': 'Load Factors',
    'headend1_site_ids': 'Headend 1 Associated Branch IDs',
    'headend2_site_ids': 'Headend 2 Associated Branch IDs',
    'scope': 'Scope',
    'prefix': 'Prefix',
    'global': 'Global',
    'ipv4_config': 'IPv4 Config',
    'ipv4_set': 'IPv4 Set',
    'default_routers': 'Default Routers',
    'path_type': 'Path Type',
    'link_bw_down': 'Bandwidth Down',
    'link_bw_up': 'Bandwidth Up',
    'bw_config_mode': 'Bandwidth Allocation',
    'nexthop': 'Next Hop',
    'as_path_list': 'Path',
    'network': 'Network',
    'statistics': 'Statistics',
    'units': 'Units',
    'security_policy_set': 'Bound Security Policy Set',
    'dhcp_relay': 'DHCP Relay',
    'dhcp_server': 'DHCP Server',
    'referers': 'Referers',
    'ports': 'Ports',
    'ips': 'IPs',
    'contenttypes': 'Content Types',
    'servers': 'Servers',
    'transfer_type': 'Transfer Type',
    'domains': 'Domains',
    'app_type': 'Application Type',
    'uris': 'URIs',
    'action': 'Action',
    'zone_id': 'Zone ID',
    'prefix_filter_id': 'Prefix Filter ID',
    'service_binding': 'Domain',
    'policy_set_id': 'Policy Set ID',
    'security_policyset_id': 'Security Policy Set ID',
    'network_policysetstack_id': 'Network Policyset Stack ID',
    'priority_policysetstack_id': 'Priority Policyset Stack ID',
    'nat_policysetstack_id': 'NAT Policyset Stack ID',
    'nat_policysetstack': 'NAT Policyset Stack',
    'network_policysetstack': 'Network Policyset Stack',
    'priority_policysetstack': 'Priority Policyset Stack',
    'security_policyset': 'Security Policyset',
    'tags': 'Tags',
    'dscp': 'DSCP',
    'path_affinity': 'Path Affinity',
    'ingress_traffic_pct': 'Ingress Traffic Percentage',
    'conn_idle_timeout': 'Connection Idle Timeout',
    'session_timeout': 'Session Timeout',
    'aggregate_flows': 'Aggregate Flows',
    'order_number': 'Order Number',
    'overrides_allowed': 'App Overrides Allowed',
    'system_app_overridden': 'System App Overridden',
    'is_deprecated': 'Is Application Deprecated',
    'parent_id': 'Parent App ID',
    'use_parentapp_network_policy': 'Use Parent App Network Policy',
    'app_unreachability_detection': 'Application Unreachability Detection Enabled',
    'network_scan_application': 'Network Scanning Application'
}


def update_id2n_dicts_slow(idname_obj):
    # pull slow updates. This can take 1-2 minutes or more. Run at start of bot.
    global_id2n = {}
    sites_id2n = idname_obj.generate_sites_map()
    global_id2n.update(sites_id2n)
    elements_id2n = idname_obj.generate_elements_map()
    global_id2n.update(elements_id2n)
    machines_id2n = idname_obj.generate_machines_map()
    global_id2n.update(machines_id2n)
    policysets_id2n = idname_obj.generate_policysets_map()
    global_id2n.update(policysets_id2n)
    securitypolicysets_id2n = idname_obj.generate_securitypolicysets_map()
    global_id2n.update(securitypolicysets_id2n)
    securityzones_id2n = idname_obj.generate_securityzones_map()
    global_id2n.update(securityzones_id2n)
    networkpolicysetstacks_id2n = idname_obj.generate_networkpolicysetstacks_map()
    global_id2n.update(networkpolicysetstacks_id2n)
    networkpolicysets_id2n = idname_obj.generate_networkpolicysets_map()
    global_id2n.update(networkpolicysets_id2n)
    prioritypolicysetstacks_id2n = idname_obj.generate_prioritypolicysetstacks_map()
    global_id2n.update(prioritypolicysetstacks_id2n)
    prioritypolicysets_id2n = idname_obj.generate_prioritypolicysets_map()
    global_id2n.update(prioritypolicysets_id2n)
    waninterfacelabels_id2n = idname_obj.generate_waninterfacelabels_map()
    global_id2n.update(waninterfacelabels_id2n)
    wannetworks_id2n = idname_obj.generate_wannetworks_map()
    global_id2n.update(wannetworks_id2n)
    wanoverlays_id2n = idname_obj.generate_wanoverlays_map()
    global_id2n.update(wanoverlays_id2n)
    servicebindingmaps_id2n = idname_obj.generate_servicebindingmaps_map()
    global_id2n.update(servicebindingmaps_id2n)
    serviceendpoints_id2n = idname_obj.generate_serviceendpoints_map()
    global_id2n.update(serviceendpoints_id2n)
    ipsecprofiles_id2n = idname_obj.generate_ipsecprofiles_map()
    global_id2n.update(ipsecprofiles_id2n)
    networkcontexts_id2n = idname_obj.generate_networkcontexts_map()
    global_id2n.update(networkcontexts_id2n)
    appdefs_id2n = idname_obj.generate_appdefs_map()
    global_id2n.update(appdefs_id2n)
    natglobalprefixes_id2n = idname_obj.generate_natglobalprefixes_map()
    global_id2n.update(natglobalprefixes_id2n)
    natlocalprefixes_id2n = idname_obj.generate_natlocalprefixes_map()
    global_id2n.update(natlocalprefixes_id2n)
    natpolicypools_id2n = idname_obj.generate_natpolicypools_map()
    global_id2n.update(natpolicypools_id2n)
    natpolicysetstacks_id2n = idname_obj.generate_natpolicysetstacks_map()
    global_id2n.update(natpolicysetstacks_id2n)
    natpolicysets_id2n = idname_obj.generate_natpolicysets_map()
    global_id2n.update(natpolicysets_id2n)
    natzones_id2n = idname_obj.generate_natzones_map()
    global_id2n.update(natzones_id2n)
    try:
        tenant_operators_id2n = idname_obj.generate_tenant_operators_map()
        global_id2n.update(tenant_operators_id2n)
    except cloudgenix.CloudGenixAPIError as e:
        logger.debug("Tenant Operators id2n map failed (likely no permission.)")
    topology_id2n = idname_obj.generate_topology_map()
    global_id2n.update(topology_id2n)
    anynets_id2n = idname_obj.generate_anynets_map()
    global_id2n.update(anynets_id2n)
    interfaces_id2n = idname_obj.generate_interfaces_map()
    global_id2n.update(interfaces_id2n)
    waninterfaces_id2n = idname_obj.generate_waninterfaces_map()
    global_id2n.update(waninterfaces_id2n)
    lannetworks_id2n = idname_obj.generate_lannetworks_map()
    global_id2n.update(lannetworks_id2n)
    spokeclusters_id2n = idname_obj.generate_spokeclusters_map()
    global_id2n.update(spokeclusters_id2n)
    localprefixfilters_id2n = idname_obj.generate_localprefixfilters_map()
    global_id2n.update(localprefixfilters_id2n)
    globalprefixfilters_id2n = idname_obj.generate_globalprefixfilters_map()
    global_id2n.update(globalprefixfilters_id2n)

    return global_id2n


def update_id2n_dicts_delta(idname_obj):
    # pull query api updates only. This should be fast.
    global_id2n = {}
    sites_id2n = idname_obj.generate_sites_map()
    global_id2n.update(sites_id2n)
    elements_id2n = idname_obj.generate_elements_map()
    global_id2n.update(elements_id2n)
    machines_id2n = idname_obj.generate_machines_map()
    global_id2n.update(machines_id2n)
    policysets_id2n = idname_obj.generate_policysets_map()
    global_id2n.update(policysets_id2n)
    securitypolicysets_id2n = idname_obj.generate_securitypolicysets_map()
    global_id2n.update(securitypolicysets_id2n)
    securityzones_id2n = idname_obj.generate_securityzones_map()
    global_id2n.update(securityzones_id2n)
    networkpolicysetstacks_id2n = idname_obj.generate_networkpolicysetstacks_map()
    global_id2n.update(networkpolicysetstacks_id2n)
    networkpolicysets_id2n = idname_obj.generate_networkpolicysets_map()
    global_id2n.update(networkpolicysets_id2n)
    prioritypolicysetstacks_id2n = idname_obj.generate_prioritypolicysetstacks_map()
    global_id2n.update(prioritypolicysetstacks_id2n)
    prioritypolicysets_id2n = idname_obj.generate_prioritypolicysets_map()
    global_id2n.update(prioritypolicysets_id2n)
    waninterfacelabels_id2n = idname_obj.generate_waninterfacelabels_map()
    global_id2n.update(waninterfacelabels_id2n)
    wannetworks_id2n = idname_obj.generate_wannetworks_map()
    global_id2n.update(wannetworks_id2n)
    wanoverlays_id2n = idname_obj.generate_wanoverlays_map()
    global_id2n.update(wanoverlays_id2n)
    servicebindingmaps_id2n = idname_obj.generate_servicebindingmaps_map()
    global_id2n.update(servicebindingmaps_id2n)
    serviceendpoints_id2n = idname_obj.generate_serviceendpoints_map()
    global_id2n.update(serviceendpoints_id2n)
    ipsecprofiles_id2n = idname_obj.generate_ipsecprofiles_map()
    global_id2n.update(ipsecprofiles_id2n)
    networkcontexts_id2n = idname_obj.generate_networkcontexts_map()
    global_id2n.update(networkcontexts_id2n)
    appdefs_id2n = idname_obj.generate_appdefs_map()
    global_id2n.update(appdefs_id2n)
    natglobalprefixes_id2n = idname_obj.generate_natglobalprefixes_map()
    global_id2n.update(natglobalprefixes_id2n)
    natlocalprefixes_id2n = idname_obj.generate_natlocalprefixes_map()
    global_id2n.update(natlocalprefixes_id2n)
    natpolicypools_id2n = idname_obj.generate_natpolicypools_map()
    global_id2n.update(natpolicypools_id2n)
    natpolicysetstacks_id2n = idname_obj.generate_natpolicysetstacks_map()
    global_id2n.update(natpolicysetstacks_id2n)
    natpolicysets_id2n = idname_obj.generate_natpolicysets_map()
    global_id2n.update(natpolicysets_id2n)
    natzones_id2n = idname_obj.generate_natzones_map()
    global_id2n.update(natzones_id2n)
    try:
        tenant_operators_id2n = idname_obj.generate_tenant_operators_map()
        global_id2n.update(tenant_operators_id2n)
    except cloudgenix.CloudGenixAPIError as e:
        logger.debug("Tenant Operators id2n map failed (likely no permission.)")
    # topology_id2n = idname_obj.generate_topology_map()
    # global_id2n.update(topology_id2n)
    # anynets_id2n = idname_obj.generate_anynets_map()
    # global_id2n.update(anynets_id2n)
    interfaces_id2n = idname_obj.generate_interfaces_map()
    global_id2n.update(interfaces_id2n)
    # waninterfaces_id2n = idname_obj.generate_waninterfaces_map()
    # global_id2n.update(waninterfaces_id2n)
    # lannetworks_id2n = idname_obj.generate_lannetworks_map()
    # global_id2n.update(lannetworks_id2n)
    # spokeclusters_id2n = idname_obj.generate_spokeclusters_map()
    # global_id2n.update(spokeclusters_id2n)

    return global_id2n


def string_can_be_int(value):
    """
    Quick check if string value can be an integer before conversion
    :param value:
    :return:
    """
    try:
        _ = int(value)
        return True
    except ValueError:
        return False


def get_pretty_name(name):
    """
    Get the pretty name of the key for output, if exists
    :param name:
    :return:
    """
    # Boolean formatting
    if type(name) is bool:
        if name:
            name = 'True'
        else:
            name = 'False'

    return PRETTYNAMES.get(str(name), name)


def replace_tab_and_clear(s, tabstop=4):
    """
    :param s:
    :param tabstop:
    :return:
    """
    result = str()
    for c in s.expandtabs():
        result += ' '
    return result


def index_list_by_dict_value(passed_list, key):
    """
    Create a dict with indexes based on the value sub-dicts in a list.
    :param passed_list: list of dicts
    :param key: value in sub-dict of list to create key values with
    :return: dictionary of keys matching to originial list items
    """
    return dict((passed_dict[key], dict(passed_dict)) for
                (iterator, passed_dict) in enumerate(passed_list))


def exclude(search_string, list_of_strings):
    """
    Grep for value and only show lines NOT matching
    :param search_string:
    :param list_of_strings:
    :return:
    """
    grep_minus_v_string = r"^((?!" + re.escape(search_string) + r").)*$"
    return filter(lambda x: re.search(grep_minus_v_string, x, re.UNICODE), list_of_strings)


def grep(search_string, list_of_strings):
    """
    Grep for value and only show that value.
    :param search_string:
    :param list_of_strings:
    :return:
    """
    return filter(lambda x: re.search(re.escape(search_string), x, re.UNICODE), list_of_strings)


def egrep(search_string, list_of_strings):
    """
    Grep for value and only show that value.
    :param search_string:
    :param list_of_strings:
    :return:
    """
    return filter(lambda x: re.search(search_string, x, re.UNICODE), list_of_strings)


def unique_list(values):
    """
    Remove all duplicate chars in a list
    :param values:
    :return:
    """
    exists = set()
    return [v for v in values if v not in exists and not exists.add(v)]


def validate_ascii_domain(domain_str):
    """
    Validates ASCII domain str is compliant
    :param domain_str:
    :return: True for Compliant, False for non-compliant.
    """

    domain_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
    return set(domain_str).issubset(domain_chars)


def domain_to_idna(passed_domain):
    """
    Change unicode domain to bytes
    :param passed_domain: bytes or str object
    :return: bytes domain in idna format
    """
    # make sure we are unicode
    if not isinstance(passed_domain, str):
        # domain is already bytes. Return as-is
        return passed_domain
    else:
        unicode_domain = passed_domain

    # try to convert to idna2008
    try:
        return_val = idna.encode(unicode_domain)
    except:
        # on fail, fall back to older (non compatible) IDNA 2003
        try:
            return_val = unicode_domain.encode('idna')
        except:
            # could not decode, return string as is.
            return_val = unicode_domain

    return return_val


def idna_to_domain(passed_domain):
    """
    Change idna domain to unicode. Should only be done right before display!
    :return:
    """
    # make sure we are str
    if type(passed_domain) is not bytes:
        # already a unicode domain. Just return.
        return passed_domain
    else:
        str_domain = passed_domain

    # try to decode idna2008
    try:
        returnval = idna.decode(str_domain)
    except:
        # on fail, fall back to older (non compatible) IDNA 2003
        try:
            returnval = str_domain.decode('idna')
        except:
            # could not decode, return string as is.
            returnval = str_domain

    return returnval


def get_pretty_data(key, value):
    """
    Pretify/parse data if certain keys.
    :param key:
    :param value:
    :return:
    """
    if key == 'created_on_utc':
        # Timestamp in nanoseconds - convert
        logger.debug('converting timestamp: {0}'.format(value))
        pretty_value = datetime.datetime.fromtimestamp(int(int(value) / 10000000)).strftime('%c')
    elif key == 'updated_on_utc':
        # Timestamp in nanoseconds - convert
        logger.debug('converting timestamp: {0}'.format(value))
        pretty_value = datetime.datetime.fromtimestamp(int(int(value) / 10000000)).strftime('%c')
    elif (key == 'start_time') or (key == 'end_time'):
        # Change ISO time to human readable
        logger.debug('converting ISO timestamp: {0}'.format(value))
        converted_datetime = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        pretty_value = converted_datetime.strftime("%c UTC")
    elif key == 'WAN-Path':
        # use dict to look up value
        xlate_dict = {
            "DirectInternet": "Direct Internet",
            "PrivateWAN": "Direct Private WAN",
            "VPN": "VPN over Internet",
            "private_vpn": "VPN over Private WAN"
        }
        pretty_value = xlate_dict.get(value, "Unknown")
    else:
        pretty_value = value

    return pretty_value


def check_sub_dict(parsed_dict, key, value):
    """
    Logic for handling sub dictionaries in table_output (hide, reparse)
    :param parsed_dict:  Parsed output that this function will add items too
    :param key:
    :param value:
    :return:
    """
    # check for specific well-known keys we want to format and show differently.
    if key == 'address':
        # street city state post_code country
        pretty_address = "{0} {1} {2} {3} {4}".format(str(value.get('street', '')).strip(), str(value.get('city',
                                                                                                          '')).strip(),
                                                      str(value.get('state', '')).strip(), str(value.get('post_code',
                                                                                                         '')).strip(),
                                                      str(value.get('country', '')).strip())
        parsed_dict[get_pretty_name(key)] = pretty_address
        status = True

    elif key == 'peer_config':
        # routing peer configuration, add multiple lines.
        parsed_dict[get_pretty_name('protocol')] = value.get('protocol', None)
        parsed_dict[get_pretty_name('local_as_num')] = value['bgp_config'].get('local_as_num', None)
        parsed_dict[get_pretty_name('remote_as_num')] = value['bgp_config'].get('remote_as_num', None)
        parsed_dict[get_pretty_name('peer_ip')] = value.get('peer_ip', None)
        status = True

    elif key == 'ethernet_port':

        # Ethernet port info
        speed = value.get('speed', 'Unknown')
        duplex = value.get('full_duplex', 'Unknown')
        if duplex == 'Unknown':
            pretty_duplex = 'Unknown'
        elif duplex:
            pretty_duplex = "Full Duplex"
        else:
            pretty_duplex = "Half Duplex"

        if speed == 'Unknown':
            # speed was non retrievable
            parsed_dict[get_pretty_name('ethernet_port')] = pretty_duplex + ', ' + speed
        elif speed == 0:
            # port is down
            parsed_dict[get_pretty_name('ethernet_port')] = '(Auto)'
        else:
            # port is up
            parsed_dict[get_pretty_name('ethernet_port')] = pretty_duplex + ', ' + str(speed) + 'Mbps'
        status = True

    else:
        # not well known, do not display dict.
        status = False

    return status


def check_sub_list(parsed_dict, key, value):
    """
    Logic for handling sub list in table_output (hide, reparse)
    :param parsed_dict: Parsed output that this function will add items too
    :param key: Dictionary Key
    :param value: Dictionary Value
    :return:
    """
    # check for specific well-known lists we want to format and show differently.
    if key == 'ipv4_addrs':
        # add IPs
        pretty_ips = ", ".join(value)
        parsed_dict[get_pretty_name(key)] = pretty_ips

        status = True
    elif key == 'bound_interfaces':
        # add bound_interfaces
        pretty_interfaces = ", ".join(value)
        parsed_dict[get_pretty_name(key)] = pretty_interfaces

        status = True
    elif key == 'lan_network_ids':
        # add bound_interfaces
        pretty_lannets = ", ".join(value)
        parsed_dict[get_pretty_name(key)] = pretty_lannets

        status = True

    elif key == 'site_paths_allowed':
        # WAN Paths
        path_list = []
        # list of dicts with wn_name and wn_path_type
        for wn_entry in value:
            # verify dict
            if type(wn_entry) is dict:
                # get wan_path_type, prettify and added to path_list
                path_list.append(get_pretty_name(wn_entry.get('wan_path_type', "Unknown")))
        # Create a path string
        parsed_dict['Allowed WAN Paths'] = ", ".join(path_list)
        status = True

    elif key == 'roles':
        # list of dicts - roles.
        role_list = []
        # list of roles
        for role_entry in value:
            # verify dict
            if type(role_entry) is dict:
                # get the roles
                role_list.append(get_pretty_name(role_entry.get('name', 'Unknown')))
        # Create role string
        parsed_dict['Roles'] = ", ".join(role_list)
        status = True

    else:
        # don't add it to output.
        status = False

    return status


def table_output(data, excludelist=None, orderlist=None, remove_sub_dict=True, remove_sub_list=True,
                 space_indent=4, trailing_newline=True, filters_enabled=True):
    """
    Format raw API JSON into tables
    #print table_output(testdict['items'], ['^_', 'id$'])
    :param data: List of Dictionaries that need sent to tabilizer
    :param excludelist: List of REGEX expressions to match items to supress
    :param orderlist: List of items that should be ordered first.
    :param remove_sub_dict: Boolean - remove sub dictionaries from table (almost always should be true)
    :param remove_sub_list: Boolean - remove sub Lists from table (almost always should be true)
    :param space_indent: spaces to indent output string (default 4 if not specified)
    :return:
    """

    # handle empty list
    if not data:
        logger.debug('sub_table_output - got empty list')
        return_str = u"\tNo results found."
        if trailing_newline:
            return return_str + u'\n'
        else:
            return return_str

    output_list = []

    # Check for debug override of excluding variables in output.
    if not filters_enabled:
        excludelist = None

    # Assume outer list wrapper
    for listline in data:
        parsed_dict = OrderedDict({})

        if orderlist is not None:
            # ordering list exists
            for priority_key in orderlist:
                # for each priority key, insert if exists.
                priority_key_value = listline.get(priority_key, None)
                if priority_key in listline:
                    logger.debug('got priority key: {0}'.format(priority_key))

                    if excludelist is not None:
                        # there is a regex exclude list, check if key matches
                        is_in_excludelist = False

                        for regexstr in excludelist:
                            if re.search(regexstr, priority_key):
                                # matched exclude list
                                is_in_excludelist = True

                        if not is_in_excludelist:
                            # Not in exclude list, add to output, 'prettyfiying' data as needed.

                            # is this a list
                            if (type(priority_key_value) is list) and (remove_sub_list is True):
                                check_sub_list(parsed_dict, priority_key, priority_key_value)

                            # is this a dict
                            elif (type(priority_key_value) is dict) and (remove_sub_dict is True):
                                check_sub_dict(parsed_dict, priority_key, priority_key_value)

                            else:
                                # other key, just add
                                parsed_dict[get_pretty_name(priority_key)] = get_pretty_name(
                                    get_pretty_data(priority_key, priority_key_value))

                    else:
                        # no exclude list and not dict or list
                        # is this a list
                        if (type(priority_key_value) is list) and (remove_sub_list is True):
                            check_sub_list(parsed_dict, priority_key, priority_key_value)

                        # is this a dict
                        elif (type(priority_key_value) is dict) and (remove_sub_dict is True):
                            check_sub_dict(parsed_dict, priority_key, priority_key_value)

                        else:
                            # other key, just add
                            parsed_dict[get_pretty_name(priority_key)] = get_pretty_name(
                                get_pretty_data(priority_key, priority_key_value))

                    # Pop the key out of the dictionary. Remaining keys will be sorted after priority ones.
                    listline.pop(priority_key)
                else:
                    # There is no value for this key. Add a blank to preserve spot in the desplay list
                    # (cover case of blank spot in first value):
                    parsed_dict[get_pretty_name(priority_key)] = ' '

        # Sort remaining keys not in priority orderlist (or all if orderlist is none). Inserted as found.
        for k, v in listline.items():

            if excludelist is not None:
                # there is a regex exclude list, check if key matches
                is_in_excludelist = False

                for regexstr in excludelist:
                    if re.search(regexstr, k):
                        # matched exclude list
                        is_in_excludelist = True

                if not is_in_excludelist:
                    # Not in exclude list, add to output, 'prettyfiying' data as needed.
                    # logger.debug('name = {0}, pretty_name = {1}'.format(k, get_pretty_name(k)))

                    # is this a list
                    if (type(v) is list) and (remove_sub_list is True):
                        check_sub_list(parsed_dict, k, v)

                    # is this a dict
                    elif (type(v) is dict) and (remove_sub_dict is True):
                        check_sub_dict(parsed_dict, k, v)

                    else:
                        # other key, just add.
                        parsed_dict[get_pretty_name(k)] = get_pretty_name(get_pretty_data(k, v))
            else:
                # no exclude list and not dict or list
                # logger.debug('name = {0}, pretty_name = {1}'.format(k, get_pretty_name(k)))

                # is this a list
                if (type(v) is list) and (remove_sub_list is True):
                    check_sub_list(parsed_dict, k, v)

                # is this a dict
                elif (type(v) is dict) and (remove_sub_dict is True):
                    check_sub_dict(parsed_dict, k, v)

                # other key, just add
                else:
                    parsed_dict[get_pretty_name(k)] = get_pretty_name(get_pretty_data(k, v))
        # add parsed dictionary to output
        output_list.append(parsed_dict)

    # Make initial output string
    data_str = str(tabulate.tabulate(output_list, headers='keys'))

    # Indent string for output
    return_str = u"\n".join((space_indent * u" ") + i for i in data_str.splitlines())

    if trailing_newline:
        return return_str + u'\n'
    else:
        return return_str


def hierarchy_output(data, excludelist=None, orderlist=None, remove_sub_dict=False, remove_sub_list=False,
                     space_indent=0, trailing_newline=True, no_indent_first=False, filters_enabled=True):
    """
    Function to print DICT data as a text hierarchy instead of JSON-style.
    :param data:
    :return:
    """

    logger.debug("hierarchy_output start: ")
    data_str = u''
    left_indent = space_indent + 4

    # Check for debug override of excluding variables in output.
    if not filters_enabled:
        excludelist = None

    if type(data) is dict:
        # Figure out the largest key value:
        colon_indent = 0
        parsed_dict = OrderedDict({})

        if orderlist is not None:
            # ordering list exists
            for priority_key in orderlist:
                # for each priority key, insert if exists.
                priority_key_value = data.get(priority_key, None)
                if priority_key in data:
                    logger.debug('got priority key: {0}'.format(priority_key))

                    if excludelist is not None:
                        # there is a regex exclude list, check if key matches
                        is_in_excludelist = False

                        for regexstr in excludelist:
                            if re.search(regexstr, priority_key):
                                # matched exclude list
                                is_in_excludelist = True

                        if not is_in_excludelist:
                            # Not in exclude list, add to output
                            parsed_dict[priority_key] = priority_key_value
                            if len(get_pretty_name(priority_key)) > colon_indent:
                                colon_indent = len(get_pretty_name(priority_key))

                    else:
                        # No exclude list, add to output
                        parsed_dict[priority_key] = priority_key_value
                        if len(get_pretty_name(priority_key)) > colon_indent:
                            colon_indent = len(get_pretty_name(priority_key))

                    # Pop the key out of the dictionary. Remaining keys will be sorted after priority ones.
                    data.pop(priority_key)

                # else:
                #     # There is no value for this key. Add a blank to preserve spot in the dIsplay list
                #       (cover case of blank spot in first value):
                #     # parsed_dict[priority_key] = ' '

        # pre-parse data (if dict) to get key lengths and exclude excludelist items.
        for key, value in data.items():
            if excludelist is not None:
                # there is a regex exclude list, check if key matches
                is_in_excludelist = False
                for regexstr in excludelist:
                    # check all regex patterns against key.
                    if re.search(regexstr, key):
                        # matched exclude list, delete key
                        # print "\nmatch!\n" + key + "\n"
                        # del data[key]
                        is_in_excludelist = True
                        # don't keep doing loop if we delete key.
                        # break

                if not is_in_excludelist:
                    parsed_dict[key] = value
                    if len(get_pretty_name(key)) > colon_indent:
                        colon_indent = len(get_pretty_name(key))

            # if no exclude list...
            else:
                parsed_dict[key] = value
                if len(get_pretty_name(key)) > colon_indent:
                    colon_indent = len(get_pretty_name(key))

        # Start actual output
        for key, value in parsed_dict.items():
            # act on values of each data
            if type(value) is dict:
                # pass
                key_indent = colon_indent - len(get_pretty_name(key))

                if no_indent_first:
                    # Remove left indent if set, and clear no_indent_first.
                    # print (key_indent * " ") + get_pretty_name(key) + ":",
                    data_str += str(key_indent * " ") + get_pretty_name(key) + ": "
                    no_indent_first = False
                else:
                    # print (left_indent * " ") + (key_indent * " ") + get_pretty_name(key) + ":",
                    data_str += str(left_indent * " ") + str(key_indent * " ") + get_pretty_name(key) + ": "

                # recurse back into function, move indent to one space right of colon.
                data_str += hierarchy_output(value, excludelist=excludelist, orderlist=orderlist,
                                             remove_sub_dict=remove_sub_dict,
                                             remove_sub_list=remove_sub_list,
                                             space_indent=(left_indent + colon_indent + 2 - 4),
                                             trailing_newline=True, no_indent_first=True)
            elif type(value) is list:
                # pass
                key_indent = colon_indent - len(get_pretty_name(key))

                if no_indent_first:
                    # Remove left indent if set, and clear no_indent_first.
                    # print (key_indent * " ") + get_pretty_name(key) + ":",
                    data_str += str(key_indent * " ") + get_pretty_name(key) + ": "
                    no_indent_first = False
                else:
                    # print (left_indent * " ") + (key_indent * " ") + get_pretty_name(key) + ":",
                    data_str += str(left_indent * " ") + str(key_indent * " ") + get_pretty_name(key) + ": "

                # recurse back into function, move indent to one space right of colon.
                data_str += hierarchy_output(value, excludelist=excludelist, orderlist=orderlist,
                                             remove_sub_dict=remove_sub_dict,
                                             remove_sub_list=remove_sub_list,
                                             space_indent=(left_indent + colon_indent + 2 - 4),
                                             trailing_newline=False, no_indent_first=True)
            else:
                key_indent = colon_indent - len(get_pretty_name(key))
                if no_indent_first:
                    # Remove left indent if set, and clear no_indent_first.
                    # print (key_indent * " ") + get_pretty_name(key) + ": " + str(value)
                    data_str += str(key_indent * " ") + get_pretty_name(key) + ": " + str(value) + u'\n'
                    no_indent_first = False
                else:
                    # print (left_indent * " ") + (key_indent * " ") + get_pretty_name(key) + ": " + \
                    #      get_pretty_data(key, str(value))
                    data_str += str(left_indent * " ") + str(key_indent * " ") + get_pretty_name(key) + ": " + \
                                get_pretty_data(key, str(value)) + u'\n'

    elif type(data) is list and len(data) > 1:
        # print a \n, seperated list.
        end_data = len(data) - 1
        for index, item in enumerate(data):
            # act on values of each data
            if type(item) is dict:
                # recurse back into function
                if no_indent_first:
                    data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                                 remove_sub_dict=remove_sub_dict,
                                                 remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                                 trailing_newline=True, no_indent_first=no_indent_first)
                    no_indent_first = False
                else:
                    data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                                 remove_sub_dict=remove_sub_dict,
                                                 remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                                 trailing_newline=True)
            elif type(item) is list:
                data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                             remove_sub_dict=remove_sub_dict,
                                             remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                             trailing_newline=True, no_indent_first=no_indent_first)
            elif type(item) is list:
                # recurse back into function
                if no_indent_first:
                    data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                                 remove_sub_dict=remove_sub_dict,
                                                 remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                                 trailing_newline=False, no_indent_first=no_indent_first)
                    no_indent_first = False
                else:
                    data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                                 remove_sub_dict=remove_sub_dict,
                                                 remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                                 trailing_newline=False)
            else:
                if no_indent_first:
                    # Remove left indent if set, and clear no_indent_first.
                    # print str(item) + ","
                    data_str += str(item) + u",\n"
                    no_indent_first = False
                elif index == end_data:
                    # print (left_indent * " ") + str(item) + ","
                    data_str += str(left_indent * " ") + str(item) + u"\n"
                else:
                    # print (left_indent * " ") + str(item) + ","
                    data_str += str(left_indent * " ") + str(item) + u",\n"

    elif type(data) is list and len(data) == 1:
        # print a flat list.
        for item in data:
            # act on values of each data
            if type(item) is dict:
                # recurse back into function
                data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                             remove_sub_dict=remove_sub_dict,
                                             remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                             trailing_newline=True, no_indent_first=no_indent_first)
            elif type(item) is list:
                # recurse back into function
                data_str += hierarchy_output(item, excludelist=excludelist, orderlist=orderlist,
                                             remove_sub_dict=remove_sub_dict,
                                             remove_sub_list=remove_sub_list, space_indent=(left_indent - 4),
                                             trailing_newline=False, no_indent_first=no_indent_first)
            else:
                if no_indent_first:
                    # Remove left indent if set, and clear no_indent_first.
                    # print str(item)
                    data_str += str(item) + u'\n'
                    no_indent_first = False
                else:
                    # print (left_indent * " ") + str(item)
                    data_str += str(left_indent * " ") + str(item) + u'\n'

    elif type(data) is list and len(data) < 1:
        if no_indent_first:
            # Remove left indent if set, and clear no_indent_first.
            # print "None"
            data_str += u"None" + u'\n'
            no_indent_first = False
        else:
            # print (left_indent * " ") + "None"
            data_str += str(left_indent * " ") + u"None" + u'\n'

    else:
        # print data
        data_str += data + u'\n'

    if trailing_newline:
        # print ""
        data_str += u'\n'

    return data_str
