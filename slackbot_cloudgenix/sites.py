# standard modules
import logging
from copy import deepcopy

# helpers
from .helpers import table_output, hierarchy_output

logger = logging.getLogger(__name__)


def showsites(passed_id, sdk, id2n):
    logger.info('showsites start: ')
    if passed_id is None:
        all_sites_resp = sdk.get.sites()
        sites_items = sdk.extract_items(all_sites_resp, 'sites')

        if all_sites_resp.cgx_status and sites_items:
            # do basic id->name
            all_sites_template = []
            lookup_keys = [
                'service_binding'
            ]
            for site in sites_items:
                site_template = dict(site)
                for key in lookup_keys:
                    value = site_template.get(key, "")
                    value_name = id2n.get(value)
                    if value_name:
                        # remove _id
                        site_template.pop(key)
                        cleaned_key = key.rstrip('_id')
                        site_template[cleaned_key] = value_name

                # check tags.
                tags = site_template.get('tags')
                if tags and isinstance(tags, list):
                    site_template['tags'] = ", ".join(tags)

                # save
                all_sites_template.append(site_template)

            sites_cleaned_byname = sorted(all_sites_template, key=lambda i: i['name'])
            return table_output(sites_cleaned_byname, ['^_', 'id$', '^lan_network_ids$', 'element_cluster_role',
                                                       'description', 'site_mode', 'address'], ['name', 'admin_state'])
        else:
            return "Sorry, couldn't get a list of sites at this moment."

    else:
        site_resp = sdk.get.sites(passed_id)

        if site_resp.cgx_status:

            # do basic id->name
            site_template = site_resp.cgx_content
            lookup_keys = [
                'nat_policysetstack_id',
                'network_policysetstack_id',
                'policy_set_id',
                'priority_policysetstack_id',
                'security_policyset_id',
                'service_binding'
            ]
            for key in lookup_keys:
                value = site_template.get(key, "")
                value_name = id2n.get(value)
                if value_name:
                    # remove _id
                    site_template.pop(key)
                    cleaned_key = key.rstrip('_id')
                    site_template[cleaned_key] = value_name

            # check tags.
            tags = site_template.get('tags')
            if tags and isinstance(tags, list):
                site_template['tags'] = ", ".join(tags)

            return hierarchy_output([site_template], ['^_'],
                                    ['name', 'element_cluster_role', 'street', 'street2', 'city',
                                     'state', 'post_code', 'country'], trailing_newline=False)
        else:
            return "Sorry, couldn't retrieve the site."
