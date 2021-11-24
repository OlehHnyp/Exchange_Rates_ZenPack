"""Models currencies using the Exchange Rates API."""

# stdlib Imports
import json

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue

# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin

# local imports
from ZenPacks.training.ER.agent import CustomHttpAgent


class Currencies(PythonPlugin):
    """
    ER Currencies modeler plugin.
    """
    relname = "erCurrencies"
    modname = "ZenPacks.training.ER.ErCurrency"

    custom_agent = CustomHttpAgent()

    requiredProperties = (
        "zCurrencyCodes",
        "zCurrencyApiKey",
        )

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties

    @inlineCallbacks
    def collect(self, device, log):
        """
        Asynchronously collect data from device. Return a deferred.
        """
        log.info("{}: collecting data".format(device.id))

        cr_codes = getattr(device, "zCurrencyCodes", None)
        if not cr_codes:
            log.error("{}: zCrCodes not set.".format(device.id))
            returnValue(None)

        api_key = getattr(device, "zCurrencyApiKey", None)
        if not api_key:
            log.error("{}: API key not set.".format(device.id))
            returnValue(None)

        raw_bodies = []

        for code in cr_codes:
            try:
                response_body = yield self.custom_agent.get_response_body(
                    "https://v6.exchangerate-api.com/v6/{key}/enriched/{code}/{code}/".format(key=api_key, code=code)
                )
                raw_bodies.append(response_body)
            except Exception, e:
                log.error("{}: {}".format(device.id, e))
                returnValue(None)

        returnValue(raw_bodies)

    def process(self, device, results, log):
        """
        Process results. Return iterable of datamaps or None.
        """
        rm = self.relMap()

        for raw_body in results:
            try:
                json_body = json.loads(raw_body)
            except ValueError:
                log.error("Can't deserialize response body: {}.\nDevice: {}".format(raw_body, device.id))
            else:
                currency_id = self.prepId(json_body["target_code"])
                rm.append(self.objectMap({
                    "id": currency_id,
                    "full_name": json_body["target_data"]["currency_name"],
                    "short_name": json_body["target_data"]["currency_name_short"],
                    }))
        return rm


