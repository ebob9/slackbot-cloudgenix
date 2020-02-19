# -*- coding: UTF-8 -*-
# standard modules
import logging
import json
import pandas as pd
import datetime

logger = logging.getLogger(__name__)


#
# def get_bw_metrics(passed_site_id, passed_link_id=None, sdk, id2n):
#
#     logger.info('get_bw_metrics start: ')
#
#     metrics_query = {
#         "start_time": "2016-11-16T17:06:27.141Z",
#         "end_time": "2016-11-17T17:06:27.141Z",
#         "interval": "5min",
#         "metrics": [
#             {
#                 "statistics": [
#                     "average"
#                 ],
#                 "name": "BandwidthUsage",
#                 "unit": "Mbps"
#             },
#             {
#                 "statistics": [
#                     "average"
#                 ],
#                 "name": "PathCapacity",
#                 "unit": "Mbps"
#             },
#         ],
#         "filter": {
#             "path": [
#                 "14643839952690003"
#             ],
#             "site": [
#                 "14643839950050237"
#             ],
#         },
#         "view": {
#             "individual": "direction",
#             "summary": False
#         }
#     }
#
#     status, metrics = sdk.get_metrics(metrics_query, sdk_vars=sdk_vars)
#
#     return json.dumps(metrics)


def apprt_site_app_path_summary(app_id, site_id, path_id, sdk, id2n):
    """

    :param app_id:
    :param site_id:
    :param path_id:
    :param sdk:
    :param id2n:
    :return:
    """

    # get time for query
    curtime = datetime.datetime.utcnow()
    endtime = curtime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    starttime = (curtime - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    metrics_query = {
        "end_time": endtime,  # "2016-11-18T17:21:52.871Z",
        "filter": {
            "app": [
                app_id  # "14117753006360199"
            ],
            "site": [
                site_id  # "14643839950050237"
            ],
            "path": [
                path_id  # "14652291803220110"
            ]
        },
        "interval": "5min",
        "metrics": [
            # {
            #     "name": "AppNormalizedNetworkTransferTime",
            #     "statistics": [
            #         "average"
            #     ],
            #     "unit": "milliseconds"
            # },
            {
                "name": "AppRoundTripTime",
                "statistics": [
                    "average"
                ],
                "unit": "milliseconds"
            },
            # {
            #     "name": "AppServerResponseTime",
            #     "statistics": [
            #         "average"
            #     ],
            #     "unit": "milliseconds"
            # },
            {
                "name": "AppUDPTransactionResponseTime",
                "statistics": [
                    "average"
                ],
                "unit": "milliseconds"
            }
        ],
        "start_time": starttime,  # "2016-11-18T16:21:52.871Z",
        "view": {
            "summary": True
        }
    }

    metrics_resp = sdk.post.metrics_monitor(metrics_query)
    status = metrics_resp.cgx_status
    metrics_response = metrics_resp.cgx_content

    # print "Status: ", status
    # print "Metrics: ", json.dumps(metrics_response, indent=4)

    if status:

        # parse the response to get into dataframe

        name_xlate = {
            "AppNormalizedNetworkTransferTime": "NTTn",
            "AppRoundTripTime": "RTT  ",
            "AppServerResponseTime": "SRT  ",
            "AppUDPTransactionResponseTime": "uTRT"
        }

        data_dict = {}
        return_str = "\n"
        label_list = []
        for metrics in metrics_response.get('metrics', []):

            metric_list = []
            name = name_xlate.get(metrics['series'][0]['name'], 'UNKNOWN')

            # parse datapoints
            for datapoint in metrics['series'][0]['data'][0]['datapoints']:
                metric_list.append(datapoint.get('value', None))

            # if not all values are none
            if not metric_list.count(None) == len(metric_list):
                data_dict[name] = metric_list
                label_list.append(name)
            else:
                logger.debug("No data in series {0} for App {1}/site {2}/ path {3}".format(name, app_id, site_id,
                                                                                           path_id))

        metric_dataframe = pd.DataFrame(data_dict)

        for label in label_list:
            string = " *{0}* - Avg: *{1}ms*, Std: *{2}ms*, 95th *{3}ms*, Max *{4}ms*, Min *{5}ms*\n".format(
                label,
                "{:.0f}".format(metric_dataframe[label].mean()),
                "{:.0f}".format(metric_dataframe[label].std()),
                "{:.0f}".format(metric_dataframe[label].quantile(0.95)),
                "{:.0f}".format(metric_dataframe[label].max()),
                "{:.0f}".format(metric_dataframe[label].min()),
            )

            return_str += string

        # print(return_str)
        return return_str

    else:
        # return blank as we didnt get stats
        return None


def media_site_app_path_summary(app_id, site_id, path_id, sdk, id2n):
    """

    :param app_id:
    :param site_id:
    :param path_id:
    :param sdk:
    :param id2n:
    :return:
    """

    # get time for query
    curtime = datetime.datetime.utcnow()
    endtime = curtime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    starttime = (curtime - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    metrics_query = {
        "end_time": endtime,  # "2016-11-18T17:21:52.871Z",
        "filter": {
            "app": [
                app_id  # "14117753006360199"
            ],
            "site": [
                site_id  # "14643839950050237"
            ],
            "path": [
                path_id  # "14652291803220110"
            ],
            "direction": "Ingress"
        },
        "interval": "5min",
        "metrics": [
            {
                "name": "AppPerfUDPAudioBandwidth",
                "statistics": [
                    "average"
                ],
                "unit": "Mbps"
            },
            {
                "statistics": [
                    "average"
                ],
                "name": "AppPerfUDPVideoPacketLoss",
                "unit": "percentage"
            },
            {
                "statistics": [
                    "average"
                ],
                "name": "AppPerfUDPAudioPacketLoss",
                "unit": "percentage"
            },
            {
                "statistics": [
                    "average"
                ],
                "name": "AppPerfUDPVideoJitter",
                "unit": "milliseconds"
            },
            {
                "statistics": [
                    "average"
                ],
                "name": "AppPerfUDPAudioJitter",
                "unit": "milliseconds"
            },

            {
                "statistics": [
                    "average"
                ],
                "name": "AppPerfUDPVideoBandwidth",
                "unit": "Mbps"
            }
        ],
        "start_time": starttime,  # "2016-11-18T16:21:52.871Z",
        "view": {
            "individual": "app"
        }
    }

    metrics_resp = sdk.post.metrics_monitor(metrics_query)
    status = metrics_resp.cgx_status
    metrics_response = metrics_resp.cgx_content

    # print "Status: ", status
    # print "Metrics: ", json.dumps(metrics_response, indent=4)

    if status:

        # parse the response to get into dataframe

        name_xlate = {
            "AppNormalizedNetworkTransferTime": "NTTn",
            "AppRoundTripTime": "RTT  ",
            "AppServerResponseTime": "SRT  ",
            "AppUDPTransactionResponseTime": "uTRT",
            "AppPerfUDPVideoBandwidth": "Video BW",
            "AppPerfUDPAudioBandwidth": "Audio BW",
            "AppPerfUDPVideoPacketLoss": "Video Packetloss",
            "AppPerfUDPAudioPacketLoss": "Audio Packetloss",
            "AppPerfUDPVideoJitter": "Video Jitter",
            "AppPerfUDPAudioJitter": "Audio Jitter",
            "AppAudioMos": "Audio MOS"
        }

        data_dict = {}
        return_str = "\n"
        label_list = []
        for metrics in metrics_response.get('metrics', []):

            current_metric_name = metrics['series'][0]['name']

            metric_list = []
            name = name_xlate.get(current_metric_name, 'UNKNOWN')

            # parse datapoints
            for datapoint in metrics['series'][0]['data'][0]['datapoints']:
                if current_metric_name in ["AppPerfUDPVideoBandwidth", "AppPerfUDPAudioBandwidth"]:
                    current_data_point = datapoint.get('value', None)
                    if current_data_point:
                        metric_list.append(current_data_point * 1024)  # convert Mb to Kb
                    else:
                        metric_list.append(current_data_point)
                else:
                    metric_list.append(datapoint.get('value', None))

            # if not all values are none
            if not metric_list.count(None) == len(metric_list):
                data_dict[name] = metric_list
                label_list.append(name)
            else:
                logger.debug("No data in series {0} for App {1}/site {2}/ path {3}".format(name, app_id, site_id,
                                                                                           path_id))

        metric_dataframe = pd.DataFrame(data_dict)

        for label in label_list:

            if label in ["Video Jitter", "Audio Jitter"]:

                string = " *{0}* - Avg: *{1}ms*, Std: *{2}ms*, 95th *{3}ms*, Max *{4}ms*, Min *{5}ms*\n".format(
                    label,
                    "{:.0f}".format(metric_dataframe[label].mean()),
                    "{:.0f}".format(metric_dataframe[label].std()),
                    "{:.0f}".format(metric_dataframe[label].quantile(0.95)),
                    "{:.0f}".format(metric_dataframe[label].max()),
                    "{:.0f}".format(metric_dataframe[label].min()),
                )
            elif label in ["Audio Packetloss", "Video Packetloss"]:
                string = " *{0}* - Avg: *{1}%*, Std: *{2}%*, 95th *{3}%*, Max *{4}%*, Min *{5}%*\n".format(
                    label,
                    "{:.0f}".format(metric_dataframe[label].mean()),
                    "{:.0f}".format(metric_dataframe[label].std()),
                    "{:.0f}".format(metric_dataframe[label].quantile(0.95)),
                    "{:.0f}".format(metric_dataframe[label].max()),
                    "{:.0f}".format(metric_dataframe[label].min()),
                )
            elif label in ["Video BW", "Audio BW"]:
                # check for zero values
                # logger.debug(" *{0}* - Avg: *{1}kb*, Std: *{2}kb*, 95th *{3}kb*, Max *{4}kb*, Min *{5}kb*\n".format(
                #             label,
                #             metric_dataframe[label].mean(),
                #             metric_dataframe[label].std(),
                #             metric_dataframe[label].quantile(0.95),
                #             metric_dataframe[label].max(),
                #             metric_dataframe[label].min(),
                #         ))

                if metric_dataframe[label].mean() > 0.01 or metric_dataframe[label].std() > 0.01 or \
                        metric_dataframe[label].quantile(0.95) > 0.01 or \
                        metric_dataframe[label].max() > 0.01 or \
                        metric_dataframe[label].min() > 0.01:

                    string = " *{0}* - Avg: *{1}kb*, Std: *{2}kb*, 95th *{3}kb*, Max *{4}kb*, Min *{5}kb*\n".format(
                        label,
                        "{:.2f}".format(metric_dataframe[label].mean()),
                        "{:.2f}".format(metric_dataframe[label].std()),
                        "{:.2f}".format(metric_dataframe[label].quantile(0.95)),
                        "{:.2f}".format(metric_dataframe[label].max()),
                        "{:.2f}".format(metric_dataframe[label].min()),
                    )
                else:
                    string = None
            else:
                string = None

            if string:
                return_str += string

        mos_str = media_site_app_mos(app_id, site_id, path_id, sdk, id2n)

        if mos_str:
            return_str += mos_str

        # print(repr(return_str))
        return return_str

    else:
        # return blank as we didnt get stats
        return None


def media_site_app_mos(app_id, site_id, path_id, sdk, id2n):
    """

    :param app_id:
    :param site_id:
    :param path_id:
    :param sdk:
    :param id2n:
    :return:
    """

    # get time for query
    curtime = datetime.datetime.utcnow()
    endtime = curtime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    starttime = (curtime - datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    metrics_query = {
        "end_time": endtime,  # "2016-11-18T17:21:52.871Z",
        "filter": {
            "app": [
                app_id  # "14117753006360199"
            ],
            "site": [
                site_id  # "14643839950050237"
            ],
            "path": [
                path_id  # "14652291803220110"
            ]
        },
        "interval": "5min",
        "metrics": [
            {
                "statistics": [
                    "average"
                ],
                "name": "AppAudioMos",
                "unit": "count"
            },
        ],
        "start_time": starttime,  # "2016-11-18T16:21:52.871Z",
        "view": {
            "individual": "direction"
        }
    }

    metrics_resp = sdk.post.metrics_monitor(metrics_query)
    status = metrics_resp.cgx_status
    metrics_response = metrics_resp.cgx_content

    # print "Status: ", status
    # print "Metrics: ", json.dumps(metrics_response, indent=4)

    if status:

        # parse the response to get into dataframe

        name_xlate = {
            "AppNormalizedNetworkTransferTime": "NTTn",
            "AppRoundTripTime": "RTT  ",
            "AppServerResponseTime": "SRT  ",
            "AppUDPTransactionResponseTime": "uTRT",
            "AppPerfUDPVideoBandwidth": "Video BW",
            "AppPerfUDPAudioBandwidth": "Audio BW",
            "AppPerfUDPVideoPacketLoss": "Video Packetloss",
            "AppPerfUDPAudioPacketLoss": "Audio Packetloss",
            "AppPerfUDPVideoJitter": "Video Jitter",
            "AppPerfUDPAudioJitter": "Audio Jitter",
            "AppAudioMos_Egress": "Audio MOS Out",
            "AppAudioMos_Ingress": "Audio MOS In",
        }

        data_dict = {}
        return_str = ""
        label_list = []
        for metrics in metrics_response.get('metrics', []):

            current_metric_name = metrics['series'][0]['name'] + "_" + metrics['series'][0]['view']['direction']

            metric_list = []
            name = name_xlate.get(current_metric_name, 'Audio MOS')

            # parse datapoints
            for datapoint in metrics['series'][0]['data'][0]['datapoints']:
                metric_list.append(datapoint.get('value', None))

            # if not all values are none
            if not metric_list.count(None) == len(metric_list):
                data_dict[name] = metric_list
                label_list.append(name)
            else:
                logger.debug("No data in series {0} for App {1}/site {2}/ path {3}".format(name, app_id, site_id,
                                                                                           path_id))

            # hack twice just for now for multiple directions.
            current_metric_name = metrics['series'][1]['name'] + "_" + metrics['series'][1]['view']['direction']

            metric_list = []
            name = name_xlate.get(current_metric_name, 'Audio MOS')

            # parse datapoints
            for datapoint in metrics['series'][1]['data'][0]['datapoints']:
                metric_list.append(datapoint.get('value', None))

            # if not all values are none
            if not metric_list.count(None) == len(metric_list):
                data_dict[name] = metric_list
                label_list.append(name)
            else:
                logger.debug("No data in series {0} for App {1}/site {2}/ path {3}".format(name, app_id, site_id,
                                                                                           path_id))

        metric_dataframe = pd.DataFrame(data_dict)

        for label in label_list:

            string = " *{0}* - Avg: *{1}*, Std: *{2}*, 95th *{3}*, Max *{4}*, Min *{5}*\n".format(
                label,
                "{:.2f}".format(metric_dataframe[label].mean()),
                "{:.2f}".format(metric_dataframe[label].std()),
                "{:.2f}".format(metric_dataframe[label].quantile(0.95)),
                "{:.2f}".format(metric_dataframe[label].max()),
                "{:.2f}".format(metric_dataframe[label].min()),
            )

            return_str += string

        # print(repr(return_str))
        return return_str

    else:
        # return blank as we didnt get stats
        return None
