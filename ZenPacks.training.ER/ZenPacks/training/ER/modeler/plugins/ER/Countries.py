"""Models countries using the Exchange Rates API."""

# stdlib Imports
import json

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue

# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin

# local imports
from ZenPacks.training.ER.agent import CustomHttpAgent


class Countries(PythonPlugin):
    """
    ER Currencies modeler plugin.
    """
    relname = "erDeviceCountries"
    modname = "ZenPacks.training.ER.ErCountry"

    custom_agent = CustomHttpAgent()

    requiredProperties = (
        "zCurrencyCodes",
    )

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties

    @inlineCallbacks
    def collect(self, device, log):
        """
        Asynchronously collect data from device. Return a deferred.
        """
        log.info("{}: collecting countries data ".format(device.id))

        cr_codes = getattr(device, "zCurrencyCodes", None)
        if not cr_codes:
            log.error("{}: zCurrencyCodes not set.".format(device.id))
            returnValue(None)

        responses_data = {}
        for cr_code in cr_codes:
            if cr_code:
                try:
                    response_body = yield self.custom_agent.get_response_body(
                        "https://restcountries.com/v2/currency/{}/".format(cr_code)
                    )
                    responses_data[cr_code] = response_body
                except Exception as e:
                    log.info("{}: {}".format(device.id, e))
                    returnValue(None)
        returnValue(responses_data)

    def process(self, device, results, log):
        """
        Process results. Return iterable of datamaps or None.
        """
        rm = self.relMap()
        countries_data = {}

        for code in results:
            try:
                json_data = json.loads(results[code])
                countries_data[code] = json_data
            except ValueError:
                log.error(
                    "Can't deserialize response body for {} currency code.\nDevice: {}".format(code, device.id)
                )
                return None

        for currency_code in countries_data:
            for country_data in countries_data.get(currency_code):
                country_id = self.prepId(country_data.get("name"))
                currency_id = self.prepId(currency_code)
                timezones = ', '.join(country_data.get("timezones"))
                rm.append(self.objectMap({
                    "set_erCountryCurrency": currency_id,
                    "id": country_id,
                    "code": country_data.get("alpha2Code"),
                    "capital": country_data.get("capital"),
                    "population": country_data.get("population"),
                    "area": country_data.get("area"),
                    "independent": country_data.get("independent"),
                    "region": country_data.get("region"),
                    "timezones": timezones,
                }))
        return rm
