# Zenoss Imports
from Products.DataCollector.plugins.CollectorPlugin import PythonPlugin


VALID_METALS = ("Gold", "Silver", "Platinum", "Palladium", "Rhodium", "Cobalt")


class Metals(PythonPlugin):
    """
    ER Precious Metals modeler plugin.
    """
    relname = "erMetals"
    modname = "ZenPacks.training.ER.ErMetal"

    requiredProperties = (
        "zMetals",
        )

    deviceProperties = PythonPlugin.deviceProperties + requiredProperties

    @staticmethod
    def collect(device, log):
        """
        Asynchronously collect data from device. Return a deferred.
        """
        log.info("{}: collecting metals data".format(device.id))

        metals = getattr(device, "zMetals", None)
        if not metals:
            log.error("{}: zMetals not set.".format(device.id))
            return None

        valid_metals = []

        for metal in metals:
            if metal in VALID_METALS:
                valid_metals.append(metal)
            else:
                log.error("\"{}\" is not a valid metal.".format(metal))
                return None

        return valid_metals

    def process(self, device, results, log):
        """
        Process results. Return iterable of datamaps or None.
        """
        rm = self.relMap()

        for valid_metal in results:
            metal_id = self.prepId(valid_metal)
            rm.append(self.objectMap({
                "id": metal_id,
                }))
        return rm
