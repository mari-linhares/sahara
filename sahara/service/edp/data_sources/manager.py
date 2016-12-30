# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from oslo_config import cfg
from oslo_log import log as logging
import six
from stevedore import enabled

from sahara import conductor as cond
from sahara import exceptions as ex
from sahara.i18n import _
from sahara.i18n import _LI

conductor = cond.API

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class DataSourceManager(object):
    def __init__(self):
        self.data_sources = {}
        self._load_data_sources()

    def _load_data_sources(self):
        config_ds = CONF.data_sources_types
        extension_manager = enabled.EnabledExtensionManager(
            check_func=lambda ext: ext.name in config_ds,
            namespace='sahara.service.edp.data_source.types',
            invoke_on_load=True
        )

        for ext in extension_manager.extensions:
            if ext.name in self.data_sources:
                raise ex.ConfigurationError(
                    _("Data source with name '%s' already exists.") %
                    ext.name)
            ext.obj.name = ext.name
            self.data_sources[ext.name] = ext.obj
            LOG.info(_LI("Data source name {ds_name} loaded {entry_point}")
                     .format(plugin_name=ext.name,
                             entry_point=ext.entry_point_target))

        if len(self.data_sources) < len(config_ds):
            loaded_ds = set(six.iterkeys(self.data_sources))
            requested_ds = set(config_ds)
            raise ex.ConfigurationError(
                _("Data sources couldn't be loaded: %s") %
                ", ".join(requested_ds - loaded_ds))

    def get_data_sources(self):
        config_ds = CONF.data_sources_types
        return [self.get_gata_source(name) for name in config_ds]

    def get_data_source(self, ds_name):
        return self.data_sources.get(ds_name)

    def update_data_source(self, plugin_name, values):
        self.label_handler.update_data_source(plugin_name, values)
        return self.get_data_source(plugin_name)

    def validate_plugin_update(self, plugin_name, values):
        return self.label_handler.validate_data_source_update(
               plugin_name, values)

    def get_data_source_update_validation_jsonschema(self):
        return self.label_handler.get_data_source_update_validation_jsonschema()


DATA_SOURCES = None

def setup_plugins():
    global DATA_SOURCES
    DATA_SOURCES = DataSourceManager()
