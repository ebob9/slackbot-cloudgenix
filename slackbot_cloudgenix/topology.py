# -*- coding: UTF-8 -*-
# standard modules
import logging
import json
import time
import slackbot_cloudgenix.metrics as metrics

logger = logging.getLogger(__name__)


def render_topology(passed_site_id, sdk, id2n):
    logger.info('render_topology start: ')

    query = {
        "type": "basenet",
        "nodes": [
            passed_site_id
        ]
    }
    topology_resp = sdk.post.topology(query)
    status = topology_resp.cgx_status
    topology = topology_resp.cgx_content

    if status:
        # (id2n should be more complete) create site ID to name lookup table.
        # node_lookup = {}
        #
        # for node in topology.get('nodes', []):
        #     node_id = node.get('id')
        #     name = node.get('name')
        #
        #     if node_id and name:
        #         node_lookup[node_id] = name

        pub_anynet_links = []
        priv_anynet_links = []
        priv_links = []
        pub_links = []

        vpn_id_lookup = {}

        # pre-iterate and extract vpn-class links
        for link in topology.get('links', []):
            vpn_id = link.get('path_id')
            if link.get('type').lower() in ["vpn"] and vpn_id:
                vpn_id_lookup['vpn_id'] = link

        # create list of links.
        # print(json.dumps(topology.get('links', []), indent=4))

        test = {
                   "_etag": 0,
                   "_schema": 0,
                   "_created_on_utc": 15715557714610031,
                   "_updated_on_utc": 0,
                   "path_id": "15715557713050119",
                   "source_node_id": "14999711899520156",
                   "source_site_name": "Washington D.C. - DC 2",
                   "target_node_id": "14994856888650209",
                   "target_site_name": "New York Branch 1",
                   "status": "up",
                   "type": "vpn",
                   "source_wan_if_id": "14994575846300032",
                   "source_wan_network": "Verizon-MPLS",
                   "source_wan_nw_id": "14994517570580047",
                   "target_wan_if_id": "14994517585570072",
                   "target_wan_network": "Verizon-MPLS",
                   "target_wan_nw_id": "14994517570580047",
                   "anynet_link_id": "14994575875140196"
               },

        for link in topology.get('links', []):

            if link.get('type').lower() in ["priv-wan-stub"]:
                network = link.get('network', link.get('path_id', '<UNKNOWN>'))
                status = link.get('status')
                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list
                priv_links.append(
                    {
                        'text': network,
                        'color': color
                    }
                )

            elif link.get('type').lower() in ["internet-stub"]:
                network = link.get('network', link.get('path_id', '<UNKNOWN>'))
                status = link.get('status')
                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list
                pub_links.append(
                    {
                        'text': network,
                        'color': color
                    }
                )

            elif link.get('type').lower() in ["anynet", "public-anynet", "private-anynet"]:
                link_type = link.get('type').lower()
                source_wan_network = link.get('source_wan_network')
                source_wan_node_id = link.get('source_node_id')
                source_wan_node = id2n.get(source_wan_node_id, source_wan_node_id)
                target_wan_network = link.get('target_wan_network')
                target_wan_node_id = link.get('target_node_id')
                target_wan_node = id2n.get(target_wan_node_id, target_wan_node_id)
                status = link.get('status')

                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list, check for reversed order:
                if passed_site_id == target_wan_node_id:
                    anynet_text = "{0} ⇔ {1}".format(target_wan_node, source_wan_node)
                    network_txt = "{0} ⇔ {1}".format(target_wan_network, source_wan_network)
                else:
                    anynet_text = "{0} ⇔ {1}".format(source_wan_node, target_wan_node)
                    network_txt = "{0} ⇔ {1}".format(source_wan_network, target_wan_network)

                # parse vpnlinks in anynet.
                vpnlinks_additional_text = ""
                vpnlinks_list = link.get('vpnlinks', [])
                if vpnlinks_list:
                    tunnel_num = 1
                    for vpnlink in vpnlinks_list:
                        vpnlinks_additional_text = "\nTunnel {0}: {1}".format(tunnel_num, network_txt)
                        tunnel_num += 1

                # add tunnel info
                anynet_text += vpnlinks_additional_text
                if link_type in ["anynet", "public-anynet"]:
                    pub_anynet_links.append({
                        'text': anynet_text,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    })
                elif link_type in ["private-anynet"]:
                    priv_anynet_links.append({
                        'text': anynet_text,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    })
            else:
                pass

        # combine links
        if pub_links:
            pub_links[0]['pretext'] = "*Internet*"
            pub_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if priv_links:
            priv_links[0]['pretext'] = "*Private WAN*"
            priv_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if pub_anynet_links:
            pub_anynet_links[0]['pretext'] = "*AppFabric over Internet*"
            pub_anynet_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if priv_anynet_links:
            pub_anynet_links[0]['pretext'] = "*AppFabric over Private WAN*"
            pub_anynet_links[0]['mrkdwn_in'] = ["pretext", "text"]

        combined_message = pub_links + priv_links + pub_anynet_links + priv_anynet_links

        return combined_message
    else:

        return [{'pretext': "Sorry, couldn't query the site topology at this moment. Please try later."}]


def render_site_app_paths(app_id, site_id, sdk, id2n, stats_app_id=None):
    # if querying unknown, and stats_app_id is passed, use that for stats.
    if not stats_app_id:
        stats_app_id = app_id

    query = {
        "type": "basenet",
        "nodes": [
            site_id
        ]
    }
    topology_resp = sdk.post.topology(query)
    status = topology_resp.cgx_status
    topology = topology_resp.cgx_content

    if status:
        # create site ID to name lookup table.

        public_anynet_links = []
        private_anynet_links = []
        priv_links = []
        pub_links = []

        vpn_id_lookup = {}

        # pre-iterate and extract vpn-class links
        for link in topology.get('links', []):
            vpn_id = link.get('path_id')
            if link.get('type').lower() in ["vpn"] and vpn_id:
                vpn_id_lookup['vpn_id'] = link

        # create list of links.
        for link in topology.get('links', []):

            if link.get('type').lower() in ["priv-wan-stub"]:
                network = link.get('network', link.get('path_id', '<UNKNOWN>'))
                status = link.get('status')
                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # Get stats for path.
                path_id = link.get('path_id')
                if path_id:
                    # get path stats string
                    path_stats = metrics.apprt_site_app_path_summary(stats_app_id, site_id, path_id, sdk, id2n)

                    # if we get stats, add it to the text.
                    if path_stats:
                        network += path_stats

                # add to list
                priv_links.append(
                    {
                        'text': network,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            elif link.get('type').lower() in ["internet-stub"]:
                network = link.get('network', link.get('path_id', '<UNKNOWN>'))
                status = link.get('status')
                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # Get stats for path.
                path_id = link.get('path_id')
                if path_id:
                    # get path stats string
                    path_stats = metrics.apprt_site_app_path_summary(stats_app_id, site_id, path_id, sdk, id2n)

                    # if we get stats, add it to the text.
                    if path_stats:
                        network += path_stats

                # add to list
                pub_links.append(
                    {
                        'text': network,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            elif link.get('type').lower() in ["anynet", "public-anynet"]:

                source_wan_network = link.get('source_wan_network')
                source_wan_node_id = link.get('source_node_id')
                source_wan_node = id2n.get(source_wan_node_id, source_wan_node_id)
                target_wan_network = link.get('target_wan_network')
                target_wan_node_id = link.get('target_node_id')
                target_wan_node = id2n.get(target_wan_node_id, target_wan_node_id)
                status = link.get('status')

                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list, check for reversed order:
                if site_id == target_wan_node_id:
                    anynet_text = "{0} ⇔ {1}".format(target_wan_node, source_wan_node)
                    network_txt = "{0} ⇔ {1}".format(target_wan_network, source_wan_network)
                else:
                    anynet_text = "{0} ⇔ {1}".format(source_wan_node, target_wan_node)
                    network_txt = "{0} ⇔ {1}".format(source_wan_network, target_wan_network)

                # parse vpnlinks in anynet.
                vpnlinks_additional_text = ""
                vpnlinks_list = link.get('vpnlinks', [])
                if vpnlinks_list:
                    tunnel_num = 1
                    for vpnlink in vpnlinks_list:
                        vpnlinks_additional_text = "\nTunnel {0}: {1}".format(tunnel_num, network_txt)
                        tunnel_num += 1
                        path_id = vpnlink
                        if path_id:
                            # get path stats string
                            path_stats = metrics.apprt_site_app_path_summary(stats_app_id, site_id, path_id, sdk, id2n)

                            # if we get stats, add it to the text.
                            if path_stats:
                                vpnlinks_additional_text += path_stats

                # add tunnel info
                anynet_text += vpnlinks_additional_text

                public_anynet_links.append(
                    {
                        'text': anynet_text,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            elif link.get('type').lower() in ["private-anynet"]:

                source_wan_network = link.get('source_wan_network')
                source_wan_node_id = link.get('source_node_id')
                source_wan_node = id2n.get(source_wan_node_id, source_wan_node_id)
                target_wan_network = link.get('target_wan_network')
                target_wan_node_id = link.get('target_node_id')
                target_wan_node = id2n.get(target_wan_node_id, target_wan_node_id)
                status = link.get('status')

                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list, check for reversed order:
                if site_id == target_wan_node_id:
                    anynet_text = "{0} ⇔ {1}".format(target_wan_node, source_wan_node)
                    network_txt = "{0} ⇔ {1}".format(target_wan_network, source_wan_network)
                else:
                    anynet_text = "{0} ⇔ {1}".format(source_wan_node, target_wan_node)
                    network_txt = "{0} ⇔ {1}".format(source_wan_network, target_wan_network)

                # parse vpnlinks in anynet.
                vpnlinks_additional_text = ""
                vpnlinks_list = link.get('vpnlinks', [])
                if vpnlinks_list:
                    tunnel_num = 1
                    for vpnlink in vpnlinks_list:
                        vpnlinks_additional_text = "\nTunnel {0}: {1}".format(tunnel_num, network_txt)
                        tunnel_num += 1
                        path_id = vpnlink
                        if path_id:
                            # get path stats string
                            path_stats = metrics.apprt_site_app_path_summary(stats_app_id, site_id, path_id, sdk, id2n)

                            # if we get stats, add it to the text.
                            if path_stats:
                                vpnlinks_additional_text += path_stats

                # add tunnel info
                anynet_text += vpnlinks_additional_text

                private_anynet_links.append(
                    {
                        'text': anynet_text,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            else:
                pass

        # combine links
        if pub_links:
            pub_links[0]['pretext'] = "*Internet*"
            pub_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if priv_links:
            priv_links[0]['pretext'] = "*Private WAN*"
            priv_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if public_anynet_links:
            public_anynet_links[0]['pretext'] = "*VPN over Internet*"
            public_anynet_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if private_anynet_links:
            private_anynet_links[0]['pretext'] = "*VPN over Private WAN*"
            private_anynet_links[0]['mrkdwn_in'] = ["pretext", "text"]

        combined_message = pub_links + public_anynet_links + priv_links + private_anynet_links

        return combined_message
    else:

        return [
            {'pretext': "Sorry, couldn't query the application info for this site at the moment. Please try later."}]


def render_site_media_paths(app_id, site_id, sdk, id2n, stats_app_id=None):
    # if querying unknown, and stats_app_id is passed, use that for stats.
    if not stats_app_id:
        stats_app_id = app_id

    query = {
        "type": "basenet",
        "nodes": [
            site_id
        ]
    }
    topology_resp = sdk.post.topology(query)
    status = topology_resp.cgx_status
    topology = topology_resp.cgx_content

    # query completed, parse topology
    if status:
        # create site ID to name lookup table.

        public_anynet_links = []
        private_anynet_links = []
        priv_links = []
        pub_links = []

        vpn_id_lookup = {}

        # pre-iterate and extract vpn-class links
        for link in topology.get('links', []):
            vpn_id = link.get('path_id')
            if link.get('type').lower() in ["vpn"] and vpn_id:
                vpn_id_lookup['vpn_id'] = link

        # create list of links.
        for link in topology.get('links', []):

            if link.get('type').lower() in ["priv-wan-stub"]:
                network = link.get('network', link.get('path_id', '<UNKNOWN>'))
                status = link.get('status')
                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # Get stats for path.
                path_id = link.get('path_id')
                if path_id:
                    # get path stats string
                    path_stats = metrics.media_site_app_path_summary(stats_app_id, site_id, path_id,
                                                                     sdk, id2n)

                    # if we get stats, add it to the text.
                    if path_stats:
                        network += path_stats

                # add to list
                priv_links.append(
                    {
                        'text': network,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            elif link.get('type').lower() in ["internet-stub"]:
                network = link.get('network', link.get('path_id', '<UNKNOWN>'))
                status = link.get('status')
                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # Get stats for path.
                path_id = link.get('path_id')
                if path_id:
                    # get path stats string
                    path_stats = metrics.media_site_app_path_summary(stats_app_id, site_id, path_id,
                                                                     sdk, id2n)

                    # if we get stats, add it to the text.
                    if path_stats:
                        network += path_stats

                # add to list
                pub_links.append(
                    {
                        'text': network,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            elif link.get('type').lower() in ["anynet", "public-anynet"]:

                source_wan_network = link.get('source_wan_network')
                source_wan_node_id = link.get('source_node_id')
                source_wan_node = id2n.get(source_wan_node_id, source_wan_node_id)
                target_wan_network = link.get('target_wan_network')
                target_wan_node_id = link.get('target_node_id')
                target_wan_node = id2n.get(target_wan_node_id, target_wan_node_id)
                status = link.get('status')

                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list, check for reversed order:
                if site_id == target_wan_node_id:
                    anynet_text = "{0} ⇔ {1}".format(target_wan_node, source_wan_node)
                    network_txt = "{0} ⇔ {1}".format(target_wan_network, source_wan_network)
                else:
                    anynet_text = "{0} ⇔ {1}".format(source_wan_node, target_wan_node)
                    network_txt = "{0} ⇔ {1}".format(source_wan_network, target_wan_network)

                # parse vpnlinks in anynet.
                vpnlinks_additional_text = ""
                vpnlinks_list = link.get('vpnlinks', [])
                if vpnlinks_list:
                    tunnel_num = 1
                    for vpnlink in vpnlinks_list:
                        vpnlinks_additional_text = "\nTunnel {0}: {1}".format(tunnel_num, network_txt)
                        tunnel_num += 1
                        path_id = vpnlink
                        if path_id:
                            # get path stats string
                            path_stats = metrics.media_site_app_path_summary(stats_app_id, site_id, path_id,
                                                                             sdk, id2n)

                            # if we get stats, add it to the text.
                            if path_stats:
                                vpnlinks_additional_text += path_stats

                # add tunnel info
                anynet_text += vpnlinks_additional_text

                public_anynet_links.append(
                    {
                        'text': anynet_text,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            elif link.get('type').lower() in ["private-anynet"]:

                source_wan_network = link.get('source_wan_network')
                source_wan_node_id = link.get('source_node_id')
                source_wan_node = id2n.get(source_wan_node_id, source_wan_node_id)
                target_wan_network = link.get('target_wan_network')
                target_wan_node_id = link.get('target_node_id')
                target_wan_node = id2n.get(target_wan_node_id, target_wan_node_id)
                status = link.get('status')

                color = "#888888"

                if status.lower() == 'up':
                    color = 'good'
                elif status.lower() == 'down':
                    color = 'danger'

                # add to list, check for reversed order:
                if site_id == target_wan_node_id:
                    anynet_text = "{0} ⇔ {1}".format(target_wan_node, source_wan_node)
                    network_txt = "{0} ⇔ {1}".format(target_wan_network, source_wan_network)
                else:
                    anynet_text = "{0} ⇔ {1}".format(source_wan_node, target_wan_node)
                    network_txt = "{0} ⇔ {1}".format(source_wan_network, target_wan_network)

                # parse vpnlinks in anynet.
                vpnlinks_additional_text = ""
                vpnlinks_list = link.get('vpnlinks', [])
                if vpnlinks_list:
                    tunnel_num = 1
                    for vpnlink in vpnlinks_list:
                        vpnlinks_additional_text = "\nTunnel {0}: {1}".format(tunnel_num, network_txt)
                        tunnel_num += 1
                        path_id = vpnlink
                        if path_id:
                            # get path stats string
                            path_stats = metrics.media_site_app_path_summary(stats_app_id, site_id, path_id,
                                                                             sdk, id2n)

                            # if we get stats, add it to the text.
                            if path_stats:
                                vpnlinks_additional_text += path_stats

                # add tunnel info
                anynet_text += vpnlinks_additional_text

                private_anynet_links.append(
                    {
                        'text': anynet_text,
                        'color': color,
                        'mrkdwn': True,
                        'mrkdwn_in': ["pretext", "text"]
                    }
                )

            else:
                pass

        # combine links
        if pub_links:
            pub_links[0]['pretext'] = "*Internet*"
            pub_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if priv_links:
            priv_links[0]['pretext'] = "*Private WAN*"
            priv_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if public_anynet_links:
            public_anynet_links[0]['pretext'] = "*VPN over Internet*"
            public_anynet_links[0]['mrkdwn_in'] = ["pretext", "text"]
        if private_anynet_links:
            private_anynet_links[0]['pretext'] = "*VPN over Private WAN*"
            private_anynet_links[0]['mrkdwn_in'] = ["pretext", "text"]

        combined_message = pub_links + public_anynet_links + priv_links + private_anynet_links

        return combined_message
    else:

        return [{
            'pretext': "Sorry, couldn't query the media application info for this site at the moment. "
                       "Please try later."}]
