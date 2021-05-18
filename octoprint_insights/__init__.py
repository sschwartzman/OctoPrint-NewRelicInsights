# coding=utf-8
from __future__ import absolute_import

from flatten_json import flatten
import json
import octoprint.plugin
import requests

class InsightsPlugin(octoprint.plugin.StartupPlugin,
					octoprint.plugin.SettingsPlugin,
					octoprint.plugin.ProgressPlugin,
					octoprint.plugin.EventHandlerPlugin,
					octoprint.plugin.AssetPlugin,
					octoprint.plugin.TemplatePlugin):

	def get_settings_defaults(self):
		return dict(
            api_urlbase="https://insights-collector.newrelic.com/v1/accounts/",
            api_urltip="/events",
            api_inskey="enter_your_insert_key_here",
            account_id="enter_your_account_id_here",
            event_type="OctoPrintEvent"
		)

	def get_assets(self):
		return dict(
			js=["js/insights.js"],
			css=["css/insights.css"],
			less=["less/insights.less"]
		)

	def get_update_information(self):
		return dict(
			insights=dict(
				displayName="Insights Plugin",
				displayVersion=self._plugin_version,
				type="github_release",
				user="sschwartzman",
				repo="OctoPrint-Insights",
				current=self._plugin_version,
				pip="https://github.com/sschwartzman/OctoPrint-Insights/archive/{target_version}.zip"
			)
		)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False, name="Insights")
		]

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		self.post_event_to_insights({'message': 'InsightsPluginSettingsSaved'})
		self._logger.info("Insights plugin settings saved.")

	def on_after_startup(self):
		self.post_event_to_insights({'message': 'OctoprintStarted'})
		self._logger.info("Insights plugin started.")

	def on_event(self, event, payload):
		output = {'message': event}
		self.update_if_not_empty(output, self.get_print_details())
		self.update_if_not_empty(output, payload)
		self.post_event_to_insights(output)

	def on_print_progress(self, location, path, progress):
		output = {'message': 'Print Job Status', 'file': path, 'location': location, 'progress': progress}
		self.update_if_not_empty(output, self.get_print_details())
		self.post_event_to_insights(output)

	def on_slicing_progress(self, slicer, source_location, source_path, destination_location, destination_path, progress):
		pass

	def get_print_details(self):
		deets = {}
		self.update_if_not_empty(deets, self._printer.get_current_data())
		self.update_if_not_empty(deets, self._printer.get_current_job())
		self.update_if_not_empty(deets, self._printer.get_current_temperatures())
		self.update_if_not_empty(deets, {'state': self._printer.get_state_string()})
		return deets

	def update_if_not_empty(self, thisdict, thisvar):
		if thisvar is not None and thisvar:
			thisdict.update(thisvar)

	def post_event_to_insights(self, event):
		event['eventType'] = self._settings.get(['event_type'])
		event_json = json.dumps([flatten(event, '.')])
		self._logger.debug("Payload: %s", event_json)
		headers = {
			'Content-Type': 'application/json',
			'X-Insert-Key': self._settings.get(['api_inskey'])
		}
		api_fullurl = self._settings.get(['api_urlbase']) + self._settings.get(['account_id']) + self._settings.get(['api_urltip'])
		response = requests.post(api_fullurl, data=event_json, headers=headers)
		self._logger.debug(response)
		success = response.status_code == 200
		if not success:
			self._logger.warn(response.content)
		return success

__plugin_name__ = "Insights Plugin"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = InsightsPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
