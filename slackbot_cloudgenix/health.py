#!/usr/bin/env python
import sys
from datetime import datetime, timedelta
import numpy as np
import requests
import json
from lxml import html

GOOD_RESPONSE = '✅'
BAD_RESPONSE = '❌'
POOR_RESPONSE = '🔴'
NO_RESPONSE = '⚪'
EXCEPTIONAL_RESPONSE = '🔵'
WARNING_RESPONSE = '⚠️'

print_console = True
print_pdf = False

dns_trt_thresholds = {
    'fail': 120,
    'warn': 50
}

diff_hours = 24  # Hours to look back at

pan_service_dict = {
    "Prisma Access": 'q8kbg3n63tmp',
    "Prisma Cloud Management": "61lhr4ly5h9b",
    "Prisma Cloud": '1nvndw0xz3nd',
    "Prisma SaaS": 'f0q7vkhppsgw',
}


# we will be using slack blocks for this response in place of text.


def blocks_section(wanted_text):
    return {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": wanted_text
        }
    }


def blocks_divider():
    return {
        "type": "divider"
    }


def pBold(str_to_print):
    return '*' + str_to_print + '*'


def pFail(str_to_print):
    return str_to_print + " " + POOR_RESPONSE


def pPass(str_to_print):
    return str_to_print + " " + GOOD_RESPONSE


def pWarn(str_to_print):
    return str_to_print + " " + WARNING_RESPONSE


def pExceptional(str_to_print):
    return str_to_print + " " + EXCEPTIONAL_RESPONSE


def pUnderline(str_to_print):
    return '_' + str_to_print + '_'


def dns_trt_classifier(dns_trt_time):
    if dns_trt_time > dns_trt_thresholds['fail']:
        return pFail(str(dns_trt_time))
    elif dns_trt_time > dns_trt_thresholds['warn']:
        return pWarn(str(dns_trt_time))
    else:
        return pPass(str(dns_trt_time))


def metric_classifier(value, expected, error_percentage_as_decimal, warn_percentage_as_decimal=0.05):
    if value < (expected - (expected * error_percentage_as_decimal)):
        return pFail(str(value))

    elif value >= expected + (expected * error_percentage_as_decimal * 2):
        return pExceptional(str(value))

    elif value >= expected - (expected * warn_percentage_as_decimal):
        return pPass(str(value))

    else:
        return pWarn(str(value))


class dbbox:
    dl = u'\u255a'
    ul = u'\u2554'
    dc = u'\u2569'
    uc = u'\u2566'
    lc = u'\u2560'
    u = u'\u2550'
    c = u'\u256c'
    l = u'\u2551'


P1 = "P1"
H1 = "H1"
H2 = "H2"
B1 = "B1"
B2 = "B2"
END_SECTION = "END_SECTION"


def vprint(text, style="B1", buffer=None):
    if buffer is None:
        buffer = []
    if print_console:
        if text == "END_SECTION":
            buffer.append(blocks_divider())
            buffer.append(blocks_section(" "))
        elif style == "P1":
            buffer.append(blocks_divider())
            buffer.append(blocks_section(pBold(text)))
            buffer.append(blocks_divider())
        elif style == "H1":
            buffer.append(blocks_divider())
            buffer.append(blocks_section(pBold(text)))
            buffer.append(blocks_divider())
        elif style == "H2":
            buffer.append(blocks_divider())
            buffer.append(blocks_section(pBold(text)))
            buffer.append(blocks_divider())
        elif style == "B1":
            buffer.append(blocks_section(text))
        elif style == "B2":
            buffer.append(blocks_section("• " + text))

        return buffer

    elif print_pdf == True:
        return None

    else:
        return None


def getpanstatus(webcontent, str_service):
    services_list = webcontent.xpath('//*[@data-component-id="' + str_service + '"]/span')
    if (len(services_list) == 4):
        service_status = (services_list[2].text).lstrip().rstrip()
    else:
        service_status = (services_list[1].text).lstrip().rstrip()
    return service_status


def site_health_header(site_id, sdk, idname):
    sites_id2n = idname.generate_sites_map()
    vpnpaths_id2n = idname.generate_anynets_map()

    site_count = 0
    search_ratio = 0
    site_name = sites_id2n.get(site_id)

    # Output queue for slack blocks.
    blocks = []

    vprint("Health Check for SITE: " + pUnderline(pBold(site_name)) + " SITE ID: " + pBold(site_id), B1,
           buffer=blocks)
    # vprint(END_SECTION, buffer=blocks)

    # Check if elements are online
    site_elements = []
    element_count = 0
    resp = sdk.get.elements()
    if resp.cgx_status:

        vprint("ION Status for site", H1, buffer=blocks)

        element_list = resp.cgx_content.get("items", None)  # EVENT_LIST contains an list of all returned events

        if len(element_list) >= 0:
            for element in element_list:  # Loop through each EVENT in the EVENT_LIST
                if element['site_id'] == site_id:
                    element_count += 1
                    site_elements.append(element['id'])
                    # if element_count > 1:
                    #     print(dbbox.l)

                    output_buffer = "ION found NAME: " + pBold(str(element['name'])) + " ION ID: " + \
                                    pBold(str(element['id']))

                    if element['connected'] is True:
                        output_buffer += "\n  ION Status: " + pPass("CONNECTED")
                    else:
                        output_buffer += "\n  ION Status: " + pFail("OFFLINE (!!!)")
                    vprint(output_buffer, B1, buffer=blocks)
        if element_count == 0:
            vprint("ION Status: " + pBold("No IONS for site found"), B1, buffer=blocks)
        vprint(END_SECTION, buffer=blocks)

    # give back the slack message.
    return blocks


def site_health_alarms(site_id, sdk, idname):

    # Output queue for slack blocks.
    blocks = []

    ################### ALARMS ###################
    ### Get last 5 ALARMS for last diff_hours hours

    dt_now = str(datetime.now().isoformat())
    dt_start = str((datetime.today() - timedelta(hours=diff_hours)).isoformat())
    dt_yesterday = str((datetime.today() - timedelta(hours=48)).isoformat())

    event_filter = '{"limit":{"count":5,"sort_on":"time","sort_order":"descending"},"view":{"summary":false},' \
                   '"severity":[],"query":{"site":["' + site_id + \
                   '"],"category":[],"code":[],"correlation_id":[],"type":["alarm"]}, ' \
                   '"start_time": "' + dt_start + '", "end_time": "' + dt_now + '"}'
    resp = sdk.post.events_query(event_filter)
    if resp.cgx_status:
        vprint("Last 5 Alarms for site within the past " + str(diff_hours) + " hours", H1, buffer=blocks)

        alarms_list = resp.cgx_content.get("items", None)
        if len(alarms_list) == 0:
            vprint("No Alarms found in the past " + str(diff_hours) + " hours", B1, buffer=blocks)
        else:
            for alarm in alarms_list:
                vprint("ALARM: " + str(alarm['code']), B1, buffer=blocks)
                vprint("Acknowledged: " + str(alarm['cleared']), B2, buffer=blocks)
                if alarm['severity'] == "minor":
                    vprint("Severity    : " + pWarn(str(alarm['severity'])), B2, buffer=blocks)
                elif alarm['severity'] == "major":
                    vprint("Severity    : " + pFail(str(alarm['severity'])), B2, buffer=blocks)
                else:
                    vprint("Severity    : " + str(alarm['severity']), B2, buffer=blocks)
                vprint("Timestamp   : " + str(alarm['time']), B2, buffer=blocks)
    else:
        vprint(pFail("ERROR in SCRIPT. Could not get ALARMS"), B1, buffer=blocks)

    ### Get SUMMARY ALARMS  for last diff_hours hours
    alarm_summary_dict = {}
    event_filter = '{"limit":{"count":1000,"sort_on":"time","sort_order":"descending"},"view":{"summary":false},' \
                   '"severity":[],"query":{"site":["' + site_id + \
                   '"],"category":[],"code":[],"correlation_id":[],"type":["alarm"]}, "start_time": "' + dt_start + \
                   '", "end_time": "' + dt_now + '"}'
    resp = sdk.post.events_query(event_filter)
    if resp.cgx_status:
        vprint("Alarm Summaries for the past " + pUnderline(str(diff_hours)) + pBold(" hours"), H2, buffer=blocks)
        alarms_list = resp.cgx_content.get("items", None)
        if len(alarms_list) > 0:
            for alarm in alarms_list:
                if alarm['code'] in alarm_summary_dict.keys():
                    alarm_summary_dict[alarm['code']] += 1
                else:
                    alarm_summary_dict[alarm['code']] = 1
            for alarm_code in alarm_summary_dict.keys():
                vprint("CODE: " + str(alarm_code), B1, buffer=blocks)
                vprint("TOTAL Count: " + pUnderline(str(alarm_summary_dict[alarm_code])), B2, buffer=blocks)
        else:
            vprint("No Alarm summaries", B1, buffer=blocks)
    else:
        vprint(pFail("ERROR in SCRIPT. Could not get ALARMS"), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    # give back the slack message.
    return blocks


def site_health_alerts(site_id, sdk, idname):

    # Output queue for slack blocks.
    blocks = []

    dt_now = str(datetime.now().isoformat())
    dt_start = str((datetime.today() - timedelta(hours=diff_hours)).isoformat())
    dt_yesterday = str((datetime.today() - timedelta(hours=48)).isoformat())

    ################### ALERTS ###################
    ### Get last 5 ALERTS for last diff_hours hours
    event_filter = '{"limit":{"count":5,"sort_on":"time","sort_order":"descending"},"view":{"summary":false},' \
                   '"severity":[],"query":{"site":["' + site_id + \
                   '"],"category":[],"code":[],"correlation_id":[],"type":["alert"]}, "start_time": "' + dt_start + \
                   '", "end_time": "' + dt_now + '"}'
    resp = sdk.post.events_query(event_filter)
    if resp.cgx_status:
        vprint("Last 5 Alerts for site within the past " + str(diff_hours) + " hours", H1, buffer=blocks)

        alerts_list = resp.cgx_content.get("items", None)
        if len(alerts_list) == 0:
            vprint("No Alerts found", B1, buffer=blocks)
        else:
            for alert in alerts_list:
                vprint("ALERT CODE: " + pBold(str(alert['code'])), B1, buffer=blocks)
                if 'reason' in alert['info'].keys():
                    vprint("REASON    : " + str(alert['info']['reason']), B2, buffer=blocks)
                if 'process_name' in alert['info'].keys():
                    vprint("PROCESS   : " + str(alert['info']['process_name']), B2, buffer=blocks)
                if 'detail' in alert['info'].keys():
                    vprint("DETAIL    : " + str(alert['info']['detail']), B2, buffer=blocks)
                if alert['severity'] == "minor":
                    vprint("SEVERITY  : " + pWarn(str(alert['severity'])), B2, buffer=blocks)
                elif alert['severity'] == "major":
                    vprint("SEVERITY  : " + pFail(str(alert['severity'])), B2, buffer=blocks)
                else:
                    vprint("SEVERITY  : " + (str(alert['severity'])), B2, buffer=blocks)
                vprint("TIMESTAMP : " + str(alert['time']), B2, buffer=blocks)
    else:
        vprint("ERROR in SCRIPT. Could not get Alerts", buffer=blocks)

    ### Get ALERTS summary for last diff_hours hours
    alert_summary_dict = {}
    event_filter = '{"limit":{"count":1000,"sort_on":"time","sort_order":"descending"},"view":{"summary":false},' \
                   '"severity":[],"query":{"site":["' + site_id + \
                   '"],"category":[],"code":[],"correlation_id":[],"type":["alert"]}, ' \
                   '"start_time": "' + dt_start + '", "end_time": "' + dt_now + '"}'
    resp = sdk.post.events_query(event_filter)
    if resp.cgx_status:
        vprint("Alert Summaries for the past " + pUnderline(str(diff_hours)) + pBold(" hours"), H1, buffer=blocks)

        alerts_list = resp.cgx_content.get("items", None)
        if len(alerts_list) > 0:
            for alert in alerts_list:
                if alert['code'] in alert_summary_dict.keys():
                    alert_summary_dict[alert['code']] += 1
                else:
                    alert_summary_dict[alert['code']] = 1
            for alert_code in alert_summary_dict.keys():
                vprint("CODE: " + str(alert_code), B1, buffer=blocks)
                vprint("TOTAL Count: " + pUnderline(str(alert_summary_dict[alert_code])), B2, buffer=blocks)
        else:
            vprint("No Alarm summaries", B1, buffer=blocks)
    else:
        vprint(pFail("ERROR in SCRIPT. Could not get Alerts"), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    # give back the slack message.
    return blocks


def site_health_links(site_id, sdk, idname):
    sites_id2n = idname.generate_sites_map()
    vpnpaths_id2n = idname.generate_anynets_map()

    site_count = 0
    search_ratio = 0
    site_name = sites_id2n.get(site_id)

    dt_now = str(datetime.now().isoformat())
    dt_start = str((datetime.today() - timedelta(hours=diff_hours)).isoformat())
    dt_yesterday = str((datetime.today() - timedelta(hours=48)).isoformat())

    # Output queue for slack blocks.
    blocks1 = []
    blocks2 = []
    blocks3 = []

    elements_id_to_name = idname.generate_elements_map()
    site_id_to_name = idname.generate_sites_map()
    wan_label_id_to_name = idname.generate_waninterfacelabels_map()
    wan_if_id_to_name = idname.generate_waninterfaces_map()

    wan_interfaces_resp = sdk.get.waninterfaces(site_id)
    wan_interfaces_list = wan_interfaces_resp.cgx_content.get("items")

    ### GET  LINKS status (VPN/PHYS)
    topology_filter = '{"type":"basenet","nodes":["' + site_id + '"]}'
    resp = sdk.post.topology(topology_filter)
    if resp.cgx_status:
        topology_list = resp.cgx_content.get("links", None)
        vprint("VPN STATUS", H1, buffer=blocks1)
        vpn_count = 0
        output_buffer = ""
        for links in topology_list:
            if (links['type'] == 'vpn') and links['source_site_name'] == site_name:
                if vpn_count > 0:
                    output_buffer += '\n'
                vpn_count += 1
                # print(dbbox.l + format(vpnpaths_id_to_name.get(links['path_id'], links['path_id'])))
                output_buffer += f"VPN {vpn_count}-> SITE:{site_name} " \
                                 f"[ION:{elements_id_to_name[links['source_node_id']]}] ---> " \
                                 f"{wan_if_id_to_name[links['source_wan_if_id']]}:{links['source_wan_network']} " \
                                 f"{dbbox.u * 3}{dbbox.c}{dbbox.u * 3} {links['target_wan_network']}:" \
                                 f"{wan_if_id_to_name[links['target_wan_if_id']]} <--- [" \
                                 f"{elements_id_to_name[links['target_node_id']]}] {links['target_site_name']}"

                if links['status'] == "up":
                    output_buffer += "\n  STATUS: " + pPass("UP")
                else:
                    output_buffer += "\n  STATUS: " + pFail("DOWN")
            # flush the buffer
        if vpn_count == 0:
            vprint("No SDWAN VPN links found at site", B1, buffer=blocks1)
        else:
            # got links
            vprint(output_buffer, B1, buffer=blocks1)
        vprint(END_SECTION, buffer=blocks1)

        pcm_metrics_array_up = []
        pcm_metrics_array_down = []
        vprint("PHYSICAL LINK STATUS", P1, buffer=blocks2)
        stub_count = 0

        for links in topology_list:
            if links['type'] == 'internet-stub':
                stub_count += 1
                if 'target_circuit_name' in links.keys():
                    vprint("Physical LINK: " + pBold(str(links['network'])) + ":" + pUnderline(
                        str(links['target_circuit_name'])), H1, buffer=blocks2)
                else:
                    vprint("Physical LINK: " + pBold(str(links['network'])), H1, buffer=blocks2)
                output_buffer = ""
                if links['status'] == "up":
                    output_buffer += "  STATUS: " + pPass("UP")
                elif links['status'] == "init":
                    output_buffer += "  STATUS: " + pWarn("INIT")
                else:
                    output_buffer += "  STATUS: " + pFail("DOWN")

                ###PCM BANDWIDTH CAPACITY MEASUREMENTS
                pcm_request = '{"start_time":"' + dt_start + 'Z","end_time":"' + dt_now + \
                              'Z","interval":"5min","view":{"summary":false,"individual":"direction"},' \
                              '"filter":{"site":["' + site_id + '"],"path":["' + \
                              links['path_id'] + '"]},"metrics":[{"name":"PathCapacity","statistics":["average"],' \
                                                 '"unit":"Mbps"}]}'
                pcm_resp = sdk.post.metrics_monitor(pcm_request)
                pcm_metrics_array_up.clear()
                pcm_metrics_array_down.clear()
                measurements_up = 0
                measurements_down = 0
                z_count_down = 0
                z_count_up = 0
                if pcm_resp.cgx_status:
                    # stop error with default value
                    direction = "Upload"
                    pcm_metric = pcm_resp.cgx_content.get("metrics", None)[0]['series']
                    if pcm_metric[0]['view']['direction'] == 'Ingress':
                        direction = "Download"
                    for series in pcm_metric:
                        if direction == "Download":
                            for datapoint in series['data'][0]['datapoints']:
                                if datapoint['value'] is None:
                                    # pcm_metrics_array_down.append(0)
                                    z_count_down += 1
                                else:
                                    pcm_metrics_array_down.append(datapoint['value'])
                                    measurements_down += 1
                            direction = 'Upload'
                        else:
                            for datapoint in series['data'][0]['datapoints']:
                                if datapoint['value'] is None:
                                    # pcm_metrics_array_up.append(0)
                                    z_count_up += 1
                                else:
                                    pcm_metrics_array_up.append(datapoint['value'])
                                    measurements_up += 1
                            direction = 'Download'

                    output_buffer += "\nConfigured Bandwidth/Throughput for the site:"

                    # Initialize in case no match, no exception
                    upload = None
                    download = None

                    for wan_int in wan_interfaces_list:
                        if wan_int['id'] == links['path_id']:
                            upload = wan_int['link_bw_up']
                            download = wan_int['link_bw_down']
                            output_buffer += "\nMaximum BW Download : " + str(wan_int['link_bw_down'])
                            output_buffer += "\nMaximum BW Upload   : " + str(wan_int['link_bw_up'])

                    error_percentage = 0.1
                    warn_percentage = 0.05
                    output_buffer += "\nMeasured Link Capacity (PCM) STATS for the last 24 hours" \
                                     "\nTHRESHOLDS: " + pFail("") + \
                                     ">=" + (str(error_percentage * 100)) + \
                                     "% |  " + pWarn("") + \
                                     ">=" + (str(warn_percentage * 100)) + \
                                     "%  | " + pPass("") + \
                                     "=Within " + (str(warn_percentage * 100)) + \
                                     "% | " + pExceptional("") + \
                                     "=" + (str(error_percentage * 100 * 2)) + \
                                     "% Above expected"

                    output_buffer += "Upload - Calculated from " + str(measurements_up) + \
                                     " Measurements in the past 24 Hours in mbits"
                    if len(pcm_metrics_array_up) == 0:
                        pcm_metrics_array_up.append(0)
                    if len(pcm_metrics_array_down) == 0:
                        pcm_metrics_array_down.append(0)

                    np_array = np.array(pcm_metrics_array_up)

                    # vprint("Zeros:" + str(z_count_up), B1)
                    output_buffer += "\n25th percentile      : " \
                                     "" + metric_classifier(round(np.percentile(np_array, 25), 3), upload,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\n50th Percentile(AVG) : " \
                                     "" + metric_classifier(round(np.average(np_array), 3), upload,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\n75th percentile      : " \
                                     "" + metric_classifier(round(np.percentile(np_array, 75), 3), upload,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\n95th percentile      : " \
                                     "" + metric_classifier(round(np.percentile(np_array, 95), 3), upload,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\nMax Value            : " \
                                     "" + metric_classifier(round(np.amax(np_array), 3), upload,
                                                            error_percentage, warn_percentage)

                    output_buffer += "\nDownload - Calculated from " + str(measurements_up) + \
                                     " Measurements in the past 24 Hours"

                    np_array = np.array(pcm_metrics_array_down)
                    # vprint("Zeros:" + str(z_count_down), B1)
                    output_buffer += "\n25th percentile      : " \
                                     "" + metric_classifier(round(np.percentile(np_array, 25), 3), download,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\n50th Percentile(AVG) : " \
                                     "" + metric_classifier(round(np.average(np_array), 3), download,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\n75th percentile      : " \
                                     "" + metric_classifier(round(np.percentile(np_array, 75), 3), download,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\n95th percentile      : " \
                                     "" + metric_classifier(round(np.percentile(np_array, 95), 3), download,
                                                            error_percentage, warn_percentage)
                    output_buffer += "\nMax Value            : " \
                                     "" + metric_classifier(round(np.amax(np_array), 3), download,
                                                            error_percentage, warn_percentage)
                # flush buffer.
                vprint(output_buffer, B1, buffer=blocks2)
                vprint(END_SECTION, buffer=blocks2)

        if stub_count == 0:
            vprint("No Physical links found at site", B1, buffer=blocks2)
            vprint(END_SECTION, buffer=blocks2)

        vprint("3RD PARTY LINK STATUS", H1, buffer=blocks3)
        service_link_count = 0
        output_buffer = ""
        for links in topology_list:
            if links['type'] == 'servicelink':
                if service_link_count > 0:
                    output_buffer += '\n'
                service_link_count += 1
                output_buffer += "3RD PARTY LINK: " + pBold(str(links['sep_name'])) + " VIA WAN " + pUnderline(
                    str(links['wan_nw_name']))
                if links['status'] == "up":
                    output_buffer += "\nSTATUS: " + pPass("UP")
                else:
                    output_buffer += "\nSTATUS: " + pFail("DOWN")
        if service_link_count == 0:
            vprint("No 3rd party VPN tunnels found", B1, buffer=blocks3)
        else:
            vprint(output_buffer, B1, buffer=blocks3)
        vprint(END_SECTION, buffer=blocks3)

    # give back the slack message.
    return blocks1, blocks2, blocks3


def site_health_dns(site_id, sdk, idname):
    sites_id2n = idname.generate_sites_map()
    vpnpaths_id2n = idname.generate_anynets_map()

    site_count = 0
    search_ratio = 0
    site_name = sites_id2n.get(site_id)

    dt_now = str(datetime.now().isoformat())
    dt_start = str((datetime.today() - timedelta(hours=diff_hours)).isoformat())
    dt_yesterday = str((datetime.today() - timedelta(hours=48)).isoformat())
    # Output queue for slack blocks.
    blocks = []

    #######DNS RESPONSE TIME:
    app_name_map = {}
    app_name_map = idname.generate_appdefs_map(key_val="display_name", value_val="id")
    if "dns" in app_name_map.keys():
        dns_app_id = app_name_map['dns']
        dns_request = '{"start_time":"' + dt_start + \
                      'Z","end_time":"' + dt_now + \
                      'Z","interval":"5min","metrics":[{"name":"AppUDPTransactionResponseTime","statistics":' \
                      '["average"],"unit":"milliseconds"}],"view":{},"filter":{"site":["' + site_id + \
                      '"],"app":["' + dns_app_id + '"],"path_type":["DirectInternet",' \
                                                   '"VPN","PrivateVPN","PrivateWAN","ServiceLink"]}}'
        dns_trt_array = []
        resp = sdk.post.metrics_monitor(dns_request)
        if resp.cgx_status:
            dns_metrics = resp.cgx_content.get("metrics", None)[0]['series'][0]
            for datapoint in dns_metrics['data'][0]['datapoints']:
                if datapoint['value'] == None:
                    dns_trt_array.append(0)
                else:
                    dns_trt_array.append(datapoint['value'])

            vprint("DNS TRT STATS", H1, buffer=blocks)

            output_buffer = "Stats for past 24 hours"

            np_array = np.array(dns_trt_array)
            output_buffer += "\nMin             : " + dns_trt_classifier(round(np.amin(np_array), 2))
            output_buffer += "\naverage         : " + dns_trt_classifier(round(np.average(np_array), 2))
            output_buffer += "\n80th percentile : " + dns_trt_classifier(round(np.percentile(np_array, 80), 2))
            output_buffer += "\n95th percentile : " + dns_trt_classifier(round(np.percentile(np_array, 95), 2))
            output_buffer += "\nMax Value       : " + dns_trt_classifier(round(np.amax(np_array), 2))

            ### Get stats from 48 hours ago
            dns_request = '{"start_time":"' + dt_yesterday + 'Z","end_time":"' + dt_start + \
                          'Z","interval":"5min","metrics":[{"name":"AppUDPTransactionResponseTime",' \
                          '"statistics":["average"],"unit":"milliseconds"}],"view":{},"filter":{"site":["' + site_id + \
                          '"],"app":["' + dns_app_id + '"],"path_type":["DirectInternet","VPN","PrivateVPN",' \
                                                       '"PrivateWAN","ServiceLink"]}}'
            dns_trt_array.clear()
            resp = sdk.post.metrics_monitor(dns_request)
            dns_metrics = resp.cgx_content.get("metrics", None)[0]['series'][0]
            for datapoint in dns_metrics['data'][0]['datapoints']:
                if (datapoint['value'] == None):
                    dns_trt_array.append(0)
                else:
                    dns_trt_array.append(datapoint['value'])

            output_buffer += "\nStats from Yesterday"

            np_array_yesterday = np.array(dns_trt_array)
            output_buffer += "\nMin             : " + dns_trt_classifier(round(np.amin(np_array_yesterday), 2))
            output_buffer += "\naverage         : " + dns_trt_classifier(round(np.average(np_array_yesterday), 2))
            output_buffer += "\n80th percentile : " + dns_trt_classifier(round(np.percentile(np_array_yesterday, 80)))
            output_buffer += "\n95th percentile : " + dns_trt_classifier(round(np.percentile(np_array_yesterday, 95)))
            output_buffer += "\nMax Value       : " + dns_trt_classifier(round(np.amax(np_array_yesterday), 2))

            # flush time
            vprint(output_buffer, B1, buffer=blocks)
    else:
        vprint(pFail("ERROR: DNS APPLICATION NOT FOUND"), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    # give back the slack message.
    return blocks


def site_health_cloud(site_id, sdk, idname):
    sites_id2n = idname.generate_sites_map()

    # Output queue for slack blocks.
    blocks = []

    ###Get PAN STATUS
    pan_core_services_url = 'https://status.paloaltonetworks.com/'
    pan_health_request = requests.get(url=pan_core_services_url)
    pan_tree_data = html.fromstring(pan_health_request.content)

    vprint("Palo Alto Prisma Cloud STATUS from: " + pUnderline(pan_core_services_url), H1, buffer=blocks)

    for service in pan_service_dict:
        service_status = getpanstatus(pan_tree_data, pan_service_dict[service])
        if service_status == "Operational":
            vprint("SERVICE: " + service + "            STATUS: " + pPass(service_status), B1, buffer=blocks)
        else:
            vprint("SERVICE: " + service + "            STATUS: " + pFail(service_status), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    ###Get zScaler STATUS
    zs_core_services_url = 'https://trust.zscaler.com/api/cloud-status.json?_format=json&a=b'

    vprint("zScaler Cloud STATUS from: " + pUnderline(zs_core_services_url), H1, buffer=blocks)

    zs_post_data = '{"cloud":"trust.zscaler.net","dateOffset":0,"requestType":"core_cloud_services"}'
    zs_query_params = {'_format': 'json', 'a': 'b'}
    zs_headers = {'Content-type': 'application/json'}

    zscaler_health_request = requests.post(url=zs_core_services_url, data=zs_post_data, params=zs_query_params,
                                           headers=zs_headers)

    zs_data = zscaler_health_request.json()

    zscaler_severity = {}
    for severity in zs_data['data']['severity']:
        zscaler_severity[severity['tid']] = severity['name']

    if 'data' in zs_data.keys():
        if 'category' in zs_data['data'].keys():
            for service in zs_data['data']['category'][0]['subCategory']:
                if 'category_status' in service.keys():
                    vprint(service['name'] + " STATUS: " + pFail(
                        zscaler_severity[service['category_status']['severityTid']] + "(" + service['category_status'][
                            'severityTid'] + ")"), B1, buffer=blocks)
                    vprint(pUnderline(service['category_status']['ri_date'] + ": ") + pBold(
                        service['category_status']['short_description']).replace("&nbsp;", " "), B2, buffer=blocks)
                else:
                    vprint(service['name'] + " STATUS: " + pPass("GOOD"), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    ### Check MSFT Cloud Serivces status:
    ms_core_services_url = 'https://portal.office.com/api/servicestatus/index'

    vprint("Microsoft Cloud STATUS from: " + pUnderline(ms_core_services_url), H1, buffer=blocks)

    ms_headers = {'Content-type': 'application/json'}
    ms_health_request = requests.get(url=ms_core_services_url, headers=ms_headers)
    ms_data = ms_health_request.json()

    if 'Services' in ms_data.keys():
        for service in ms_data['Services']:
            if service['IsUp']:
                vprint(service['Name'] + " STATUS: " + pPass("GOOD"), B1, buffer=blocks)
            else:
                vprint(service['Name'] + " STATUS: " + pFail("ISSUE DETECTED"), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    ### Check Google Cloud Serivces status:
    google_core_services_url = 'https://www.google.com/appsstatus/json/en'

    vprint("Google Cloud STATUS from: " + pUnderline(google_core_services_url), H1, buffer=blocks)

    google_headers = {'Content-type': 'application/json'}
    google_health_request = requests.get(url=google_core_services_url, headers=google_headers)
    google_data = json.loads(google_health_request.text.replace("dashboard.jsonp(", "").replace("});", "}"))

    google_service_list = {}
    for service in google_data['services']:
        google_service_list[service['id']] = service['name']

    google_issue_count = 0
    for messages in google_data['messages']:
        if not (messages['resolved']):
            google_issue_count += 1
            vprint(google_service_list[messages['service']] + " STATUS: " + pFail("ISSUE DETECTED"), B1, buffer=blocks)
    if google_issue_count == 0:
        vprint(pPass("No unresolved google cloud issues detected"), B1, buffer=blocks)
    vprint(END_SECTION, buffer=blocks)

    # debug
    print(json.dumps(blocks, indent=4))

    # give back the slack message.
    return blocks