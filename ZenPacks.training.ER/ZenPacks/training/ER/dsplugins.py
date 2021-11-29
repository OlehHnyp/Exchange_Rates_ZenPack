"""Monitors exchange rates using the ER API."""

# Logging
import json
import logging
LOG = logging.getLogger("zen.ER")

# stdlib Imports

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.error import Error as TwistedWebError
from twisted.web.http_headers import Headers

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )

# local imports
from ZenPacks.training.ER.agent import CustomHttpAgent
from ZenPacks.training.ER.custom_exceptions import ResponseError, NotSupportedValueError


PRECIOUS_METALS_DICT = {"Gold": 0, "Silver": 1, "Platinum": 2, "Palladium": 3, "Rhodium": 4, "Cobalt": 6}


class ExchangeRates(PythonDataSourcePlugin):
    """
    Exchange rates data source plugin.
    """
    proxy_attributes = ("zCurrencyApiKey",)

    custom_agent = CustomHttpAgent()

    @classmethod
    def config_key(cls, datasource, context):
        LOG.info("config_key working")
        return (
            context.device().id,
            datasource.getCycleTime(context),
            context.id,
            "exchange rates",
            )

    @classmethod
    def params(cls, datasource, context):
        LOG.info("params working")
        return {
            "currency_code": context.id,
            }

    @inlineCallbacks
    def collect(self, config):
        LOG.info("collect working")
        raw_response_bodies = {}

        for datasource in config.datasources:
            currency_code = datasource.params["currency_code"]
            try:
                raw_response_body = yield self.custom_agent.get_response_body(
                    "https://v6.exchangerate-api.com/v6/{}/latest/{}/".format(
                        datasource.zCurrencyApiKey, currency_code
                    )
                )
                raw_response_bodies[currency_code] = raw_response_body
            except TwistedWebError as error:
                error.message += "{}: failed to get response for {}".format(config.id, currency_code)
                returnValue(error)
        returnValue(raw_response_bodies)

    def onResult(self, result, config):
        """
        Called first for success and error.
        """
        LOG.info("onResult working")
        json_response_bodies = {}
        for code in result:
            try:
                json_response_bodies[code] = json.loads(result[code])
            except ValueError as error:
                error.message += "{}: can't deserialize response body: {}".format(code, result[code])
                raise error
            if json_response_bodies[code]["result"] == "error":
                raise ResponseError(
                    "{}, {} response error: {}".format(config.id, code, json_response_bodies[code]["error-type"])
                )
        return json_response_bodies

    def onSuccess(self, result, config):
        """
        Called only on success. After onResult, before onComplete.
        """
        LOG.info("onSuccess working")
        data = self.new_data()

        for code in result:
            for datasource in config.datasources:
                if datasource.datasource == "exchangeRates":
                    for datapoint_id in (x.id for x in datasource.points):
                        value = result[code]["conversion_rates"][datapoint_id]
                        dpname = "_".join((datasource.datasource, datapoint_id))
                        data["values"][datasource.component][dpname] = (value, "N")
        return data

    def onError(self, result, config):
        """
        Called only on error. After onResult, before onComplete.
        """
        LOG.info("onError working")
        LOG.exception("In onError - result is {} and config is {}.".format(result, config.id))


class PreciousMetals(PythonDataSourcePlugin):
    """
    Precious metals rates data source plugin.
    """
    proxy_attributes = ("zMetalsApiKey", "zCurrencyApiKey")

    custom_agent = CustomHttpAgent()
    supported_metals = PRECIOUS_METALS_DICT

    @classmethod
    def config_key(cls, datasource, context):
        LOG.info("config_key working")
        return (
            context.device().id,
            datasource.getCycleTime(context),
            context.id,
            "precious metals rates",
            )

    @classmethod
    def params(cls, datasource, context):
        LOG.info("params working")
        return {
            "precious_metal_name": context.id,
            }

    @inlineCallbacks
    def collect(self, config):
        LOG.info("collect working")
        result = {}
        raw_response_bodies = {}

        for datasource in config.datasources:
            metal_name = datasource.params["precious_metal_name"]
            metal_code = self.supported_metals.get(metal_name)
            if metal_code is None:
                returnValue(NotSupportedValueError("\"{}\" is not supported precious metal name.".format(metal_name)))

            url = "https://current-precious-metal-price.p.rapidapi.com/metals/v1/{}".format(metal_code)
            headers = {
                "x-rapidapi-host": "current-precious-metal-price.p.rapidapi.com",
                "x-rapidapi-key": datasource.zMetalsApiKey
            }
            try:
                raw_response_body = yield self.custom_agent.get_response_body(url, Headers(headers))
                raw_response_bodies[metal_name] = raw_response_body
            except TwistedWebError as error:
                error.message += "{}: failed to get response for {}".format(config.id, metal_name)
                returnValue(error)

        result["raw_metals_data"] = raw_response_bodies
        try:
            raw_usd_rates = yield self.custom_agent.get_response_body(
                "https://v6.exchangerate-api.com/v6/{}/latest/USD/".format(config.datasources[0].zCurrencyApiKey)
            )
            result["raw_usd_rates"] = raw_usd_rates
        except TwistedWebError as error:
            error.message += "{}: failed to get response for USD".format(config.id)
            returnValue(error)

        returnValue(result)

    def onResult(self, result, config):
        """
        Called first for success and error.
        """
        LOG.info("onResult working")
        deserialized_result = {}
        json_response_bodies = {}
        for metal_name in result["raw_metals_data"]:
            try:
                json_response_bodies[metal_name] = json.loads(result["raw_metals_data"][metal_name])
            except ValueError as error:
                error.message += "{}: can't deserialize response body: {}".format(
                    metal_name, result["raw_metals_data"][metal_name]
                )
                raise error

        deserialized_result["json_metals_data"] = json_response_bodies
        try:
            deserialized_result["json_usd_rates"] = json.loads(result["raw_usd_rates"])["conversion_rates"]
        except ValueError as error:
            error.message += "USD: can't deserialize response body: {}".format(result["raw_usd_rates"])
            raise error
        return deserialized_result

    def onSuccess(self, result, config):
        """
        Called only on success. After onResult, before onComplete.
        """
        LOG.info("onSuccess working")
        data = self.new_data()
        metals_data = result["json_metals_data"]
        usd_rates = result["json_usd_rates"]

        for metal_name in metals_data:
            for datasource in config.datasources:
                if datasource.datasource == "MetalsRates":
                    for datapoint_id in (x.id for x in datasource.points):
                        rate = usd_rates[datapoint_id]
                        value = metals_data[metal_name] * rate
                        dpname = "_".join((datasource.datasource, datapoint_id))
                        data["values"][datasource.component][dpname] = (value, "N")
        return data

    def onError(self, result, config):
        """
        Called only on error. After onResult, before onComplete.
        """
        LOG.info("onError working")
        LOG.exception("In onError - result is {} and config is {}.".format(result, config.id))