"""Monitors exchange rates using the ER API."""

# Logging
import json
import logging
LOG = logging.getLogger("zen.ER")

# stdlib Imports

# Twisted Imports
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.error import Error as TwistedWebError
from twisted.python.failure import Failure

# PythonCollector Imports
from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource import (
    PythonDataSourcePlugin,
    )

# local imports
from ZenPacks.training.CR.agent import CustomHttpAgent


class CustomResponseError(Exception):
    pass


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
            context.id,
            datasource.getCycleTime(context),
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
                raise CustomResponseError(
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
                        value = result[code][datapoint_id]
                        dpname = "_".join((datasource.datasource, datapoint_id))
                        data["values"][datasource.component][dpname] = (value, "N")
        return data

    def onError(self, result, config):
        """
        Called only on error. After onResult, before onComplete.
        """
        LOG.info("onError working")
        LOG.exception("In onError - result is {} and config is {}.".format(result, config.id))

